import os
import logging
from dotenv import load_dotenv
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.run.sql_runner import sql_runner
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.prompt import Confirm

"""
This script collects applicable .sql scripts from the specified directory and passes them into sql_runner.py
"""

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File Handler (logs everything INFO and above)
logs_dir = "_logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

file_handler = logging.FileHandler(os.path.join(logs_dir, "run.log"))
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s")
file_handler.setFormatter(file_formatter)

# Console Handler (only ERROR and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_formatter = logging.Formatter("%(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s")
console_handler.setFormatter(console_formatter)

# Attach handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# BASE_DIR = os.getcwd()
# load_dotenv(os.path.join(BASE_DIR, '.env'))
# SQL_DIR = os.getenv('SQL_DIR', 'default_sql_dir')
# WORKING_DIR = os.path.join(BASE_DIR, SQL_DIR)
console = Console()

def get_script_order(input_dir):
    """Reads the runlist file and returns the order of scripts."""
    runlist_path = os.path.join(input_dir, "_runlist.txt")
    if not os.path.exists(runlist_path):
        logger.error(f"'runlist' file not found in folder: {input_dir}")
        raise FileNotFoundError(f"'runlist' file not found in folder: {input_dir}")

    with open(runlist_path, "r") as runlist_file:
        scripts = [line.strip() for line in runlist_file if line.strip() and not line.strip().startswith("#")]
        logger.debug(f"Script order loaded: {scripts}")
        return scripts

def validate_script_path(folder_path, script_name):
    """Validates the existence of a script in the given folder."""
    script_path = os.path.join(folder_path, script_name)
    if not os.path.exists(script_path):
        logger.error(f"SQL script '{script_name}' not found in folder: {folder_path}")
        raise FileNotFoundError(f"SQL script '{script_name}' listed in 'runlist' not found in folder: {folder_path}")
    logger.debug(f"Validated script path: {script_path}")
    return script_path

def filter_scripts(scripts, dev, vanilla):
    """Filters scripts based on dev and vanilla flags."""
    original_count = len(scripts)
    if vanilla:
        scripts = [file for file in scripts if '_std_' in file.lower()]
    elif dev:
        scripts = [file for file in scripts if 'dev_' in file.lower() or 'dev_' not in file.lower()]
    else:
        scripts = [file for file in scripts if 'dev_' not in file.lower()]
    logger.debug(f"Filtered scripts: {len(scripts)} out of {original_count} (dev={dev}, vanilla={vanilla})")
    return scripts

def execute_scripts(scripts, sql_dir, server, database, username, password, debug):
    """Executes the SQL scripts with progress tracking."""
    logger.debug(f"Starting execution of {len(scripts)} scripts in {sql_dir}")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        "•",
        TimeElapsedColumn(),
        "•",
        TextColumn("{task.completed:,}/{task.total:,}"),
        console=console
    ) as progress:
        for script in scripts:
            # Validate script path
            script_path = os.path.join(sql_dir, script)
            if not os.path.exists(script_path):
                logger.error(f"SQL script '{script}' not found in folder: {sql_dir}")
                console.print(f"[red]SQL script '{script}' not found in folder: {sql_dir}[/red]")
                continue  # Skip to the next script

            logger.debug(f"Running {script}")
            try:
                sql_runner(
                    script_path=script_path,
                    server=server,
                    database=database,
                    username=username,
                    password=password
                )
                logger.info(f"PASS: {script}")
            except Exception as e:
                logger.error(f"ERROR: {script}: {e}")
                console.print(f"[red]Error executing script {script}: {e}[/red]")

            if debug:
                progress.stop()
                if not Confirm.ask("[yellow]DEBUG MODE is active. Continue?[/yellow]"):
                    logger.warning("Execution stopped in DEBUG mode.")
                    console.print("Exiting", style="bold red")
                    return
                progress.start()

    logger.info(f"Completed all scripts in {sql_dir}.")
    console.print(f"[green]Completed all scripts in {sql_dir}.[/green]")

def run(options):
    """Main function to process and execute SQL scripts."""
    server = options.get('server')
    database = options.get('database')
    username = options.get('username')
    password = options.get('password')
    input_dir = options.get('input')
    backup = options.get('backup', False)
    dev = options.get('dev', False)
    debug = options.get('debug', False)
    vanilla = options.get('vanilla', False)

    logger.debug(f"Run started with options: {options}")

    try:
        script_order = get_script_order(input_dir)
        scripts = filter_scripts(script_order, dev, vanilla)

        if not scripts:
            logger.warning(f"No SQL scripts found in {input_dir}.")
            console.print(f"No SQL scripts found in {input_dir}.", style="bold red")
            return

        if not Confirm.ask(f"Run [bold blue]{input_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow] (dev={dev}, debug={debug})?"):
            logger.debug(f"Execution skipped for {input_dir}.")
            console.print(f"[bold red]Skipping {input_dir}[/bold red]")
            return

        execute_scripts(scripts, input_dir, server, database, username, password, debug)

        if backup or Confirm.ask("SQL scripts completed. Backup database?"):
            logger.debug("Starting database backup.")
            backup_db({
                'server': server,
                'database': database,
                'output': os.path.join(os.getcwd(), "_backups")
                })

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        console.print(f"Error: {str(e)}", style="bold red")

if __name__ == "__main__":
    # Example usage
    options = {
        'server': r'dylans\mssqlserver2022',
        'database': 'test',
        'input': r'D:\skolrood\needles\conv\2_case',
        'backup': False,
        'dev': False,
        'debug': False,
        'vanilla': False
    }
    run(options)