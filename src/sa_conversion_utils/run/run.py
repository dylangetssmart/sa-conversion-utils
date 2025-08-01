import time
import os
import argparse
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.run.sql_runner import sql_runner
from sa_conversion_utils.run.sort_scripts import sort_scripts_using_metadata
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.utils.validate_dir import validate_dir
from sa_conversion_utils.config.user_config import load_user_config, REQUIRED_ENV_VARS
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TaskProgressColumn
from rich.console import Console
from rich.progress import track


from dotenv import load_dotenv

console = Console()
logger = setup_logger(__name__, log_file="run.log")
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file


def collect_scripts(input_dir, use_metadata):
    if use_metadata:
        logger.debug("Using metadata to process scripts.")
        scripts = sort_scripts_using_metadata(input_dir)
    else:
        logger.debug("Not using metadata to process scripts.")
        scripts = [f for f in os.listdir(input_dir) if f.lower().endswith(".sql")]
        scripts.sort()  # Sort scripts alphabetically for sequential execution

    if not scripts:
        logger.warning(f"No SQL scripts found in {input_dir} after filtering.")

    logger.debug(f"Collected scripts: {scripts}")
    return scripts


def run(config: dict):
    server = config.get("server") or os.getenv("SERVER")
    database = config.get("database") or os.getenv("TARGET_DB")
    username = config.get("username")
    password = config.get("password")
    input_dir = config.get("input")
    use_metadata = config.get("use_metadata", False)
    # server = options.get('server')
    # database = options.get('database')
    # username = options.get('username')
    # password = options.get('password')
    # input_dir = options.get('input')
    # use_metadata = options.get('use_metadata', False)

    # Lazy load environment variables with defaults
    # server = server or os.getenv("SERVER")
    # database = database or os.getenv("TARGET_DB")
    # print("config:", config)
    # print(f"server: {server}, database: {database}, input_dir: {input_dir}, use_metadata: {use_metadata}")  

    # logger.debug(f"Run started with options: {config}")

    # Validate input directory
    if not validate_dir(input_dir, logger):
        return

    # Collect scripts
    scripts = collect_scripts(input_dir, use_metadata)
    if not scripts:
        return

    # Format the list of scripts for console output
    formatted_scripts = "\n".join([f"- {script}" for script in scripts])
    logger.info(f"Order of scripts to execute: \n{formatted_scripts}")

    # Confirm with the user before proceeding
    if not Confirm.ask(
        f"Run [bold blue]{input_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow]"
    ):
        logger.info(f"Execution skipped for {input_dir}.")
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
            transient=False # Keep the bar visible after completion
            # redirect_stderr=True, # Ensure stderr goes through Rich
            # redirect_stdout=True # Ensure stdout goes through Rich
        ) as progress:
            
            overall_task = progress.add_task(f"[cyan]Executing SQL Scripts", total=len(scripts))

            for script in scripts:
                script_path = os.path.join(input_dir, script)
                
                progress.update(overall_task, description=f"[cyan]Running {script}")
                
                sql_runner(
                    script_path=script_path,
                    server=server,
                    database=database,
                    username=username,
                    password=password,
                    logger=logger,
                    progress=progress,
                )
                   
                progress.advance(overall_task)
            
            progress.update(overall_task, description=f"[green]SQL Script Execution Complete")

    # Optionally back up the database after execution
    if Confirm.ask(f"SQL scripts completed. Backup {database}?"):
        logger.debug("Starting database backup.")
        backup_db(
            {
                "server": server,
                "database": database,
                "output": os.path.join(os.getcwd(), "_backups"),
            }
        )


""" CLI Integration """
def handle_run_command(args):
    """CLI dispatcher function for 'run' subcommand."""
    options = {
        "server": args.server,
        "database": args.database,
        "input": args.input,
        "use_metadata": args.metadata,
    }
    run(options)


def add_run_parser(subparsers):
    """Add the run command to the parser."""
    # env_config = load_user_config(REQUIRED_ENV_VARS)
    # logger.debug(f"Loaded environment config: {env_config}")

    run_parser = subparsers.add_parser("run", help="Run SQL scripts in order.")
    run_parser.add_argument("-s", "--server", help="SQL Server")
    run_parser.add_argument("-d", "--database", help="Database")
    run_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input folder containing SQL files.",
    )
    run_parser.add_argument(
        "--metadata",
        action="store_true",
        help="Use metadata to determine script execution order.",
    )
    run_parser.set_defaults(func=handle_run_command)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Process SQL files and execute them in order."
    )
    subparsers = parser.add_subparsers(help="Available commands")

    # Add the 'run' command and its arguments
    add_run_parser(subparsers)

    # Parse arguments and dispatch to the appropriate function
    args = parser.parse_args()

    # Call the function set by the parser (i.e., handle_run_command)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()