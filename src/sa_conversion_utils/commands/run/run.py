import os
import argparse
import logging

# Local
from .sql_runner import run_sql_script
# from .sort_scripts import sort_scripts_using_metadata
from sa_conversion_utils.commands.backup import backup

# External
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TaskProgressColumn
from rich.console import Console
from dotenv import load_dotenv

console = Console()
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file
DEFAULT_SERVER = os.getenv("SERVER")
DEFAULT_DB = os.getenv("TARGET_DB")


def run(args: argparse.Namespace):
    server = args.server or os.getenv("SERVER")
    database = args.database or os.getenv("TARGET_DB")
    input_dir = args.input

    if not (input_dir and os.path.isdir(input_dir)):
        logger.error(f"Input directory '{input_dir}' does not exist or is not a directory.")
        return

    scripts = [f for f in os.listdir(input_dir) if f.lower().endswith(".sql")]
    scripts.sort()  # Sort scripts alphabetically for sequential execution
    if not scripts:
        logger.warning(f"No SQL scripts found in {input_dir}.")
        return

    # Format the list of scripts for console output
    formatted_scripts = "\n".join([f"- {script}" for script in scripts])
    # logger.info(f"Order of scripts to execute: \n{formatted_scripts}")
    console.print(f"[bold blue] The following scripts will be executed against {server}.{database}[/bold blue]\n{formatted_scripts}")

    if not Confirm.ask('Execute?'):
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
                    # username=username,
                    # password=password,
                    progress=progress,
                )
                progress.advance(overall_task)
            
            progress.update(overall_task, description=f"[green]SQL Script Execution Complete")

    # Optionally back up the database after execution
    if Confirm.ask(f"SQL scripts completed. Backup {database}?"):
        logger.debug("Starting database backup.")
        backup(
            {
                "server": server,
                "database": database,
                "output": os.path.join(os.getcwd(), "workspace//backups"),
            }
        )


def setup_parser(subparsers):
    """
    Configures the parser for the 'run' subcommand.
    """
    run_parser = subparsers.add_parser("run", help="Run SQL scripts in order.")
    run_parser.add_argument(
        "-s",
        "--server",
        default=DEFAULT_SERVER,
        help="SQL Server"
    )
    run_parser.add_argument(
        "-d",
        "--database",
        default=DEFAULT_DB,
        help="Database to execute SQL scripts against."
    )
    run_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input folder containing SQL files."
    )
    run_parser.set_defaults(func=run)