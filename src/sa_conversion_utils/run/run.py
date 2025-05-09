import os
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.run.sql_runner import sql_runner
from sa_conversion_utils.run.sort_scripts import sort_scripts_using_metadata
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.utils.validate_dir import validate_input_dir
from rich.prompt import Confirm
import argparse

logger = setup_logger(__name__, log_file="run.log")

def add_run_parser(subparsers):
    """Add the run command to the parser."""
    run_parser = subparsers.add_parser("run", help="Run SQL scripts in order.")
    run_parser.add_argument("-s", "--server", required=True, help="SQL Server")
    run_parser.add_argument("-d", "--database", required=True, help="Database")
    run_parser.add_argument("-i", "--input", required=True, help="Path to the input folder containing SQL files.")
    run_parser.add_argument("--metadata", action="store_true", help="Use metadata to determine script execution order.")
    run_parser.set_defaults(func=handle_run_command)

def handle_run_command(args):
    """CLI dispatcher function for 'run' subcommand."""
    options = {
        'server': args.server,
        'database': args.database,
        'username': getattr(args, 'username', None),
        'password': getattr(args, 'password', None),
        'input': args.input,
        'use_metadata': args.metadata
    }
    run_sql_scripts(options)

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

# def execute_scripts(scripts, sql_dir, server, database, username, password):
#     """Executes the SQL scripts with simple loop-based tracking."""
#     logger.debug(f"Starting execution of {len(scripts)} scripts in {sql_dir}")

#     for index, script in enumerate(scripts, start=1):
#         script_path = os.path.join(sql_dir, script)
#         if not os.path.exists(script_path):
#             logger.error(f"SQL script '{script}' not found in folder: {sql_dir}")
#             continue

#         logger.debug(f"Running {script} ({index}/{len(scripts)})")
#         try:
#             sql_runner(
#                 script_path=script_path,
#                 server=server,
#                 database=database,
#                 username=username,
#                 password=password
#             )
#             logger.info(f"PASS: {script}")
#         except Exception:
#             logger.error(f"ERROR: {script}")

#     logger.info(f"Completed all scripts in {sql_dir}.")

# def execute_script(script_path, server, database, username, password):
#     """Executes a single SQL script."""
#     logger.debug(f"Running script: {script_path}")
#     try:
#         sql_runner(
#             script_path=script_path,
#             server=server,
#             database=database,
#             username=username,
#             password=password
#         )
#         logger.info(f"PASS: {script_path}")
#     except Exception:
#         logger.error(f"ERROR: {script_path}")

def run_sql_scripts(options):
    server = options.get('server')
    database = options.get('database')
    username = options.get('username')
    password = options.get('password')
    input_dir = options.get('input')
    use_metadata = options.get('use_metadata', False)

    logger.debug(f"Run started with options: {options}")

    # Validate input directory
    if not validate_input_dir(input_dir, logger):
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
    # execute_scripts(scripts, input_dir, server, database, username, password)

    # Optionally back up the database after execution
    if Confirm.ask(f"SQL scripts completed. Backup {database}?"):
        logger.debug("Starting database backup.")
        backup_db({
            'server': server,
            'database': database,
            'output': os.path.join(os.getcwd(), "_backups")
        })

if __name__ == "__main__":
     # Standard argparse setup for standalone execution
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
    
    # import argparse
    # parser = argparse.ArgumentParser(description="Process SQL files and execute them in order.")
    # parser.add_argument("-s", "--server", required=True, help="SQL Server")
    # parser.add_argument("-d", "--database", required=True, help="Database")
    # parser.add_argument("-i", "--input", required=True, help="Path to the input folder containing SQL files.")
    # parser.add_argument("--metadata", action="store_true", help="Use metadata to determine script execution order.")

    # args = parser.parse_args()

    # # Build options dictionary
    # options = {
    #     'server': args.server,
    #     'database': args.database,
    #     'input': args.input,
    #     'metadata': args.metadata
    # }

    # run(options)