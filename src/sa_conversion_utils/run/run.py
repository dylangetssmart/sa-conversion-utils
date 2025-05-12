import os
import argparse
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.run.sql_runner import sql_runner
from sa_conversion_utils.run.sort_scripts import sort_scripts_using_metadata
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.utils.validate_dir import validate_dir
from sa_conversion_utils.utils.user_config import load_user_config, REQUIRED_ENV_VARS
from rich.prompt import Confirm

logger = setup_logger(__name__, log_file="run.log")

def add_run_parser(subparsers):
    """Add the run command to the parser."""
    env_config = load_user_config(REQUIRED_ENV_VARS)
    logger.debug(f"Loaded environment config: {env_config}")

    run_parser = subparsers.add_parser("run", help="Run SQL scripts in order.")
    run_parser.add_argument("-s", "--server", default=env_config["SERVER"], help="SQL Server")
    run_parser.add_argument("-d", "--database", default=env_config["TARGET_DB"], help="Database")
    run_parser.add_argument("-i", "--input", required=True, help="Path to the input folder containing SQL files.")
    run_parser.add_argument("--metadata", action="store_true", help="Use metadata to determine script execution order.")
    run_parser.set_defaults(func=handle_run_command)

def handle_run_command(args):
    """CLI dispatcher function for 'run' subcommand."""
    options = {
        'server': args.server,
        'database': args.database,
        'input': args.input,
        'use_metadata': args.metadata
    }
    run(options)

def collect_scripts(input_dir, use_metadata):
    if use_metadata:
        logger.debug("Using metadata to process scripts.")
        scripts = sort_scripts_using_metadata(input_dir)
    else:
        logger.debug("Not using metadata to process scripts.")
        scripts = [f for f in os.listdir(input_dir) if f.lower().endswith('.sql')]
        scripts.sort()  # Sort scripts alphabetically for sequential execution

    if not scripts:
        logger.warning(f"No SQL scripts found in {input_dir} after filtering.")

    logger.debug(f"Collected scripts: {scripts}")
    return scripts

def run(config: dict):
    server = config.get('server')
    database = config.get('database')
    username = config.get('username')
    password = config.get('password')
    input_dir = config.get('input')
    use_metadata = config.get('use_metadata', False)
    # server = options.get('server')
    # database = options.get('database')
    # username = options.get('username')
    # password = options.get('password')
    # input_dir = options.get('input')
    # use_metadata = options.get('use_metadata', False)

    logger.debug(f"Run started with options: {config}")

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
    if not Confirm.ask(f"Run [bold blue]{input_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow]"):
        logger.info(f"Execution skipped for {input_dir}.")
        return

    # Execute each script individually
    for script in scripts:
        script_path = os.path.join(input_dir, script)
        # execute_script(script_path, server, database, username, password)
        sql_runner(
            script_path=script_path,
            server=server,
            database=database,
            username=username,
            password=password
        )

    # Optionally back up the database after execution
    if Confirm.ask(f"SQL scripts completed. Backup {database}?"):
        logger.debug("Starting database backup.")
        backup_db({
            'server': server,
            'database': database,
            'output': os.path.join(os.getcwd(), "_backups")
        })

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Process SQL files and execute them in order.")
    subparsers = parser.add_subparsers(help="Available commands")

    # Add the 'run' command and its arguments
    add_run_parser(subparsers)

    # Parse arguments and dispatch to the appropriate function
    args = parser.parse_args()

    # Call the function set by the parser (i.e., handle_run_command)
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()