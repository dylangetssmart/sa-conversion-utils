import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional
# External
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TaskProgressColumn
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree 
from dotenv import load_dotenv

# Internal Project Dependencies
from ..backup import backup
from .sql_runner import run_sql_script
from ...logging.logger_config import logger_config


console = Console()
logger = logger_config(name='run', log_file="run.log", level=logging.DEBUG, rich_console=console)

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
DEFAULT_SERVER = os.getenv("SERVER", "DEFAULT_SQL_SERVER")
DEFAULT_DB = os.getenv("TARGET_DB", "DEFAULT_DATABASE")

# ----------------------------------------------------------------------
## ⚙️ Argument Parser Setup

def setup_parser(subparsers):
    """ Configures the parser for the 'run' subcommand. """
    run_parser = subparsers.add_parser("run", help="Run SQL scripts from a runlist file or an input folder.")
    
    # 1. Group: Script Source Configuration (How to find scripts)
    group_config = run_parser.add_argument_group('Input Options')
    group_config.add_argument(
        "-r", 
        "--runlist", 
        type=str, 
        default=None,
        metavar="<PATH>", 
        # UPDATED HELP TEXT: Only expects a path now
        help="Full path to a .txt runlist file."
    )
    group_config.add_argument(
        "-f", 
        "--folder", 
        type=Path, 
        default=None, 
        metavar="<PATH>", 
        help="Path to a folder containing SQL files."
    )
    
    # 2. Group: Runlist Options
    group_runlist = run_parser.add_argument_group('Runlist Options (Requires -r/--runlist)')
    group_runlist.add_argument(
        "-g", 
        "--group", 
        type=str, 
        default=None, 
        metavar="<NAME>",
        help="Optional group name (e.g., 'reset') to execute from the runlist file."
    )
    group_runlist.add_argument(
        "--show-groups", 
        action="store_true", 
        help="List all available execution groups from the runlist file in a rich tree view and exit."
    )

    # 3. Group: Execution Target
    group_target = run_parser.add_argument_group('SQL Target Connection')
    group_target.add_argument(
        "-s", 
        "--server", 
        default=DEFAULT_SERVER, 
        metavar="", 
        help="SQL Server name or IP."
    )
    group_target.add_argument(
        "-d", 
        "--database", 
        default=DEFAULT_DB, 
        metavar="", 
        help="Database to execute SQL scripts against."
    )
    
    run_parser.set_defaults(func=run)
    
# ----------------------------------------------------------------------
## 🛠️ Utility Functions

def collect_scripts_from_runlist(runlist_path: Path, group_name: Optional[str]) -> List[Path]:
    """ 
    Reads the runlist file, resolves paths, validates scripts, and optionally filters by group.
    (No change needed here, it relies on runlist_path.parent)
    """
    scripts: List[Path] = []
    logger.debug(f"Parsing runlist file: {runlist_path}, Group: {group_name}")
    
    try:
        with open(runlist_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logger.error(f"Runlist file not found: {runlist_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading runlist file {runlist_path}: {e}")
        return []
        
    runlist_dir = runlist_path.parent
    
    # --- Group-based Parsing ---
    if group_name:
        target_header = f"[{group_name}]"
        in_target_group = False
        
        for i, line in enumerate(lines, 1):
            if line.startswith('[') and line.endswith(']'):
                if line == target_header:
                    in_target_group = True
                elif in_target_group:
                    break
                continue
            
            if in_target_group and line:
                script_path = runlist_dir / line
                
                if not script_path.is_file() or not script_path.name.lower().endswith(".sql"):
                    logger.error(f"Runlist line {i}: '{line}' in group '{group_name}' is not a valid SQL script path. Skipping.")
                    console.print(f"Runlist line {i}: '{line}' is not a valid SQL script path. Skipping.")
                    continue
                    
                scripts.append(script_path.resolve())
                
        if not scripts:
            logger.error(f"Group '{group_name}' not found or contains no valid scripts in the runlist.")
             
    # --- Full File Parsing (No Group Specified) ---
    else:
        for i, line in enumerate(lines, 1):
            if line.startswith('[') and line.endswith(']'):
                continue
                
            script_path = runlist_dir / line
            
            if not script_path.is_file() or not script_path.name.lower().endswith(".sql"):
                logger.error(f"Runlist line {i}: '{line}' is not a valid SQL script path. Skipping.")
                console.print(f"Runlist line {i}: '{line}' is not a valid SQL script path. Skipping.")
                continue
                
            scripts.append(script_path.resolve())
            
    return scripts


def collect_scripts_from_dir(input_dir: Path) -> List[Path]:
    """ Scans the input directory for SQL files, sorts them, and returns absolute paths. """
    
    if not input_dir.is_dir():
        logger.error(f"Input directory '{input_dir}' does not exist or is not a directory.")
        return []
        
    scripts = [f for f in input_dir.iterdir() if f.is_file() and f.name.lower().endswith(".sql")]
    scripts.sort(key=lambda p: p.name)
    
    return [s.resolve() for s in scripts]


def display_runlist_groups(runlist_path: Path, console: Console):
    """ Reads the runlist and displays its groups and scripts using a rich Tree. """
    try:
        with open(runlist_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        console.print(f"[bold red]Error reading runlist:[/bold red] {e}")
        return

    tree = Tree(
        # Use full path for clarity since we don't have a 'project name' anymore
        f"[bold blue]Runlist: {runlist_path.name}[/bold blue] [dim]({runlist_path.parent})[/dim]",
        guide_style="cyan"
    )
    
    runlist_dir = runlist_path.parent
    current_group_node = None
    group_count = 0
    script_count = 0
    
    default_node = tree.add("[bold white]• No Group / Root Scripts[/bold white]")
    in_default_group = True

    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            in_default_group = False 
            
            group_name = line[1:-1]
            current_group_node = tree.add(f"[bold yellow]Group: {group_name}[/bold yellow]")
            group_count += 1
            continue
        
        if line:
            script_path = runlist_dir / line
            target_node = current_group_node if current_group_node and not in_default_group else default_node

            if script_path.is_file():
                status_color = "green"
                status_icon = "✓"
                script_count += 1
            else:
                status_color = "red"
                status_icon = "✗"
                
            target_node.add(f"[{status_color}]{status_icon} [/][dim white]{line}[/dim white]")
            
    if not group_count and not default_node.children:
          tree.remove(default_node)
          tree.add("[dim]No scripts or group definitions found.[/dim]")
    
    console.print(tree)

# ----------------------------------------------------------------------
## 🔍 Script Collection Logic

def collect_scripts(args: argparse.Namespace) -> List[Path]:
    """ Determines which scripts to run based on precedence. """
    
    # Collect from runlist
    if args.runlist:
        runlist_path = Path(args.runlist)

        if not runlist_path.is_file():
            logger.error(f"Runlist file not found: {runlist_path}")
            console.print(f"[bold red]Error:[/bold red] Runlist file not found: {runlist_path}")
            return []

        resolved_runlist_path = runlist_path.resolve()
        setattr(args, '_resolved_runlist_path', resolved_runlist_path)

        return collect_scripts_from_runlist(resolved_runlist_path, args.group)


    # Collect from input folder
    if args.folder:
        logger.info(f"Using input directory: {args.folder}")
        return collect_scripts_from_dir(args.folder)
        
    logger.error("No input provided. Use -r/--runlist or -f/--folder.")
    console.print("[bold red]Fatal Error:[/bold red] Please specify a runlist file (-r) or an input directory (-f).")
    return []

# ----------------------------------------------------------------------
## 🚀 Main Execution Function

def run(args: argparse.Namespace):
    """ Main logic for the 'run' command: Collects, displays, confirms, and executes scripts. """
    logger.debug("Starting 'run' command...") 
    server = args.server
    database = args.database
    
    scripts = collect_scripts(args)

    # # 1. Handle explicit --show-groups flag and exit
    # if args.runlist and args.show_groups:
    #     if hasattr(args, '_resolved_runlist_path'):
    #         display_runlist_groups(args._resolved_runlist_path, console)
    #     return

    if not scripts:
        logger.warning("No valid SQL scripts collected. Exiting.")
        return

    # 2. --- Display found scripts in a Rich Panel ---
    script_texts = []
    
    # Runlist mode
    if hasattr(args, '_resolved_runlist_path'):
        source_path = args._resolved_runlist_path
        
        if args.group:
            source_desc = f"{source_path} - [bold yellow]group: '{args.group}'[/bold yellow]"
            # source_desc = f"Group '[bold yellow]{args.group}[/bold yellow]' from runlist"
        else:
            source_desc = f"{source_path} - [bold yellow]no group specified[/bold yellow]"
    else: 
        # Input directory mode
        source_desc = args.folder

    for i, script_path in enumerate(scripts, 1):
        full_path_str = str(script_path)
        script_texts.append(f"[bold dim]{i}.[/bold dim] [cyan]{full_path_str}[/cyan]")

    script_content = "\n".join(script_texts)

    panel_title = f"[green]Found {len(scripts)} scripts from {source_desc}"

    panel_content = Panel(
        script_content,
        title=panel_title,
        border_style="blue",
        title_align="left"
    )
    console.print(panel_content)

    # 3. --- Display runlist groups as part of confirmation ---
    # if args.runlist and hasattr(args, '_resolved_runlist_path'):
    #     console.print("\n[bold yellow]--- Runlist Group Structure Review ---[/bold yellow]")
    #     display_runlist_groups(args._resolved_runlist_path, console)
    #     console.print("[bold yellow]--------------------------------------[/bold yellow]\n")


    # 4. --- Confirmation ---
    if not Confirm.ask(f'[bold blue]🚀 Run the above {len(scripts)} scripts on target 🖥️  [yellow]{server} 💿 {database}[/yellow][/bold blue]'):
        logger.info(f"Execution skipped by user.")
        return

    # 5. --- Execution Block ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        "•",
        TimeElapsedColumn(),
        "•",
        TextColumn("{task.completed:,}/{task.total:,}"),
        console=console,
        transient=False
    ) as progress:
            
        overall_task = progress.add_task(f"[cyan]Executing SQL Scripts", total=len(scripts))

        for script_path in scripts:
            progress.update(overall_task, description=f"[cyan]Running {script_path.name}")
            run_sql_script(
                script_path=str(script_path), 
                server=server,
                database=database,
                progress=progress,
            )
            progress.advance(overall_task)
            
        progress.update(overall_task, description=f"[green]SQL Script Execution Complete")

    # 6. --- Optional Backup ---
    if Confirm.ask(f"SQL scripts completed. Backup {database}?"):
        backup(
            server=server,
            database=database,
            output=os.path.join(os.getcwd(), "backups"),
            skip_confirm=True
        )

# Mock main entry point (needed for the file to be runnable for testing)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple CLI tool for SQL execution.")
    subparsers = parser.add_subparsers(help='Available commands')
    setup_parser(subparsers)
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()