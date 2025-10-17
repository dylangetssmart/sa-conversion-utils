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
from dotenv import load_dotenv

from ..backup import backup
from .sql_runner import run_sql_script
from ...logging.logger_config import logger_config
from .runlist_utils import load_scripts_from_runlist, collect_scripts_from_dir, resolve_runlist_path, display_runlist_groups

# This is the directory that holds all project folders containing runlists (e.g., 'scripts/needles')
RUNLIST_BASE_DIR = Path("scripts")

console = Console()
logger = logger_config(name='run', log_file="run.log", level=logging.DEBUG, rich_console=console)

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
DEFAULT_SERVER = os.getenv("SERVER", "DEFAULT_SQL_SERVER")
DEFAULT_DB = os.getenv("TARGET_DB", "DEFAULT_DATABASE")

def setup_parser(subparsers):
    """ Configures the parser for the 'run' subcommand with grouped and clean help output. """
    run_parser = subparsers.add_parser("run", help="Run SQL scripts from a runlist file or an input folder.")
    
    # 1. Group: Script Source Configuration (How to find scripts)
    group_config = run_parser.add_argument_group('Input Options')
    group_config.add_argument(
        "-r", 
        "--runlist", 
        type=str, 
        default=None,
        metavar="<PROJECT|PATH>", 
        help="Project name (e.g., 'needles') or full path to a .txt runlist file."
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
    

def collect_scripts(args: argparse.Namespace) -> List[Path]:
    """ Determines which scripts to run based on precedence, handling smart resolution for runlists. """
    
    if args.runlist:
        runlist_input = args.runlist
        resolved_runlist_path = resolve_runlist_path(runlist_input)

        if resolved_runlist_path:
            # Store the resolved path on the args object for use in the 'run' function panel display/group listing
            setattr(args, '_resolved_runlist_path', resolved_runlist_path)
            
            # If we are only listing groups, we don't need to load the scripts yet.
            if args.show_groups:
                return [] # Return empty list, execution will be skipped in run()
                
            # Otherwise, load the scripts for execution
            return load_scripts_from_runlist(resolved_runlist_path, args.group)
            
        # If we reach here, resolution failed
        logger.error(f"Could not find runlist file for input: '{runlist_input}'")
        console.print(f"[bold red]Error:[/bold red] Runlist not found. Please check input or convention.")
        return []

    # 2. Fallback: Input Directory
    if args.folder:
        logger.info(f"Using input directory: {args.folder}")
        return collect_scripts_from_dir(args.folder)
        
    # 3. No input provided
    logger.error("No input provided. Use -r/--runlist or -i/--input.")
    console.print("[bold red]Fatal Error:[/bold red] Please specify a runlist file (-r) or an input directory (-i).")
    return []

def run(args: argparse.Namespace):
    logger.debug("Starting 'run' command...") 
    logger.debug(f"Server: {args.server}, Database: {args.database}")
    server = args.server
    database = args.database
    
    scripts = collect_scripts(args)

    if args.runlist and args.show_groups:
        if hasattr(args, '_resolved_runlist_path'):
            display_runlist_groups(args._resolved_runlist_path, console)
        return

    if not scripts:
        logger.warning("No valid SQL scripts collected. Exiting.")
        return

    # --- Display found scripts in a Rich Panel ---
    script_texts = []
    
    # Determine the source for the panel title using the stored resolved path or input path
    if hasattr(args, '_resolved_runlist_path'):
        # Runlist mode
        source_path = args._resolved_runlist_path
        
        if args.group:
            source_desc = f"Group '[bold yellow]{args.group}[/bold yellow]' from project '{args.runlist}'"
        else:
            source_desc = f"All scripts from project '{args.runlist}' (No group specified)"
    else: 
        # Input directory mode
        source_path = args.folder
        source_desc = "found in folder"

    for i, script_path in enumerate(scripts, 1):
        # Display the file name and its parent directory (useful for runlist mode)
        # display_name = f"[cyan]{script_path.name}[/cyan] [dim white]({script_path.parent.name})[/dim white]"
        full_path_str = str(script_path)
        display_name = f"[cyan]{full_path_str}[/cyan]"
        script_texts.append(f"[bold dim]{i}.[/bold dim] {display_name}")

    # script_columns = Columns(script_texts, column_first=True, expand=True)
    script_content = "\n".join(script_texts)

    panel_title = f"[green]Found {len(scripts)} scripts {source_desc}: {source_path}[/green]"

    panel_content = Panel(
        script_content,
        title=panel_title,
        border_style="blue",
        title_align="left"
    )
    console.print(panel_content)

    if not Confirm.ask(f'[bold blue]🚀 Run scripts on target 🖥️  [yellow]{server} 💿 {database}[/yellow][/bold blue]'):
        logger.info(f"Execution skipped by user.")
        return

    # Execution Block
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
            # script_path is already a complete Path object (Path.resolve())
            progress.update(overall_task, description=f"[cyan]Running {script_path.name}")
            run_sql_script(
                script_path=str(script_path), # Pass as string if required by the dependency
                server=server,
                database=database,
                progress=progress,
            )
            progress.advance(overall_task)
            
        progress.update(overall_task, description=f"[green]SQL Script Execution Complete")

    # Optionally back up the database after execution
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