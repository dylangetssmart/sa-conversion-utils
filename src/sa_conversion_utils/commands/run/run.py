import os
import argparse
import logging
import json
from pathlib import Path
from typing import List, Optional
# Local
from .sql_runner import run_sql_script
from ..backup import backup
from ...logging.logger_config import logger_config
from ..scan.workflow_resolver import resolve_workflow_path
# External
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TaskProgressColumn
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from dotenv import load_dotenv

console = Console()
logger = logger_config(name='run', log_file="run.log", level=logging.DEBUG, rich_console=console)

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file
DEFAULT_SERVER = os.getenv("SERVER")
DEFAULT_DB = os.getenv("TARGET_DB")


def run(args: argparse.Namespace):
    logger.info("Starting 'run' command") 
    server = args.server or os.getenv("SERVER")
    database = args.database or os.getenv("TARGET_DB")
    
    input_dir: Optional[Path] = None
    
    # 1. Try to resolve the path using workflow segments
    if args.workflow_path:
        logger.debug(f"Attempting to resolve workflow path: {args.workflow_path}")
        resolved_path = resolve_workflow_path(args.workflow_path, console)
        if resolved_path:
            input_dir = resolved_path
    
    # 2. Fall back to the direct input directory argument (-i)
    elif args.input:
        input_dir = Path(args.input)
        
    # 3. Handle cases where neither path is provided or resolved
    if not input_dir:
        logger.error("No input directory or valid workflow path provided.")
        console.print("[bold red]Fatal Error:[/bold red] Use workflow segments (e.g., `sami run needles convert`) or the -i/--input flag.")
        return

    # Final validation before running
    if not input_dir.is_dir():
        logger.error(f"Input directory '{input_dir}' does not exist or is not a directory.")
        console.print(f"[bold red]Error:[/bold red] Input directory '{input_dir}' does not exist.")
        return

    scripts = [f for f in os.listdir(input_dir) if f.lower().endswith(".sql")]
    scripts.sort()  # Sort scripts alphabetically for sequential execution
    
    if not scripts:
        logger.warning(f"No SQL scripts found in [yellow]{input_dir}[/yellow].")
        return

    # --- Display found scripts in a Rich Panel ---
    script_texts = [f"[bold dim]{i}.[/bold dim] [cyan]{script}[/cyan]" for i, script in enumerate(scripts, 1)]
    script_columns = Columns(script_texts, column_first=True, expand=True)
    panel_title = f"[dim white]Found {len(scripts)} scripts in {input_dir}[/dim white]"

    panel_content = Panel(
        script_columns,
        title=panel_title,
        border_style="blue",
        title_align="left"
    )
    console.print(panel_content)

    if not Confirm.ask(f'[bold blue]🚀 Execute scripts against [yellow]{server}.{database}[/yellow][/bold blue]'):
        logger.info(f"Execution skipped by user.")
        return

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

        for script in scripts:
            script_path = os.path.join(input_dir, script)
            progress.update(overall_task, description=f"[cyan]Running {script}")
            run_sql_script(
                script_path=script_path,
                server=server,
                database=database,
                progress=progress,
            )
            progress.advance(overall_task)
            
        progress.update(overall_task, description=f"[green]SQL Script Execution Complete")

    # Optionally back up the database after execution
    if Confirm.ask(f"SQL scripts completed. Backup {database}?"):
        logger.debug("Starting database backup.")
        backup(
            server=server,
            database=database,
            output=os.path.join(os.getcwd(), "backups"),
            skip_confirm=True
        )


def setup_parser(subparsers):
    """ Configures the parser for the 'run' subcommand. """
    run_parser = subparsers.add_parser(
        "run", 
        help="Run SQL scripts from an input folder or a discovered workflow path."
    )
    
    # Positional argument for workflow path segments (e.g., 'needles' 'convert' '2_case')
    run_parser.add_argument(
        "workflow_path", 
        nargs='*', # 0 or more positional arguments
        help="Hierarchical path to a workflow folder (e.g., 'scripts needles convert'). Takes precedence over -i."
    )
    
    # Optional argument for direct directory input (original functionality)
    run_parser.add_argument(
        "-i", 
        "--input", 
        default=None, # Changed default to None
        help="Direct path to the input folder containing SQL files (used if no workflow path is provided)."
    )
    
    run_parser.add_argument("-s", "--server", default=DEFAULT_SERVER, help="SQL Server")
    run_parser.add_argument("-d", "--database", default=DEFAULT_DB, help="Database to execute SQL scripts against.")
    
    run_parser.set_defaults(func=run)
