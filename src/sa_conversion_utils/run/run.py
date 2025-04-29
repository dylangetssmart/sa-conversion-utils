import os
import logging
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.run.sql_runner import sql_runner
from sa_conversion_utils.utilities.read_yaml_metadata import read_yaml_metadata
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.prompt import Confirm

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logs_dir = "_logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

file_handler = logging.FileHandler(os.path.join(logs_dir, "run.log"))
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s")
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter("%(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s")
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

console = Console()

def get_scripts_with_metadata(input_dir):
    """Reads metadata from each SQL file and builds a list of scripts with their sequence."""
    scripts_with_metadata = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.sql'):
            file_path = os.path.join(input_dir, filename)
            # logger.debug(f"Reading metadata from {file_path}")
            metadata = read_yaml_metadata(file_path)
            if metadata:
                sequence = metadata.get("sequence", float('inf'))  # Default to infinity if no sequence is provided
                scripts_with_metadata.append({"filename": filename, "sequence": sequence})
            else:
                logger.warning(f"No metadata found for file: {filename}")
    # Sort scripts by sequence
    scripts_with_metadata.sort(key=lambda x: x["sequence"])
    # logger.debug(f"Scripts with metadata: {scripts_with_metadata}")
    return [script["filename"] for script in scripts_with_metadata]

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
            script_path = os.path.join(sql_dir, script)
            if not os.path.exists(script_path):
                logger.error(f"SQL script '{script}' not found in folder: {sql_dir}")
                console.print(f"[red]SQL script '{script}' not found in folder: {sql_dir}[/red]")
                continue

            logger.debug(f"Running {script}")
            try:
                # sql_runner(
                #     script_path=script_path,
                #     server=server,
                #     database=database,
                #     username=username,
                #     password=password
                # )
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
    use_metadata = options.get('metadata', True)

    logger.debug(f"Run started with options: {options}")

    try:
        # Validate the input directory
        if not os.path.exists(input_dir):
            logger.error(f"Input directory does not exist: {input_dir}")
            console.print(f"[red]Input directory does not exist: {input_dir}[/red]")
            return

        # Collect scripts
        if use_metadata:
            logger.debug("Using metadata to filter scripts.")
            # Get scripts with metadata and sort by sequence
            all_scripts = get_scripts_with_metadata(input_dir)
        else:
            logger.debug("Not using metadata to filter scripts.")   
            # Get all .sql files in the input directory
            all_scripts = [f for f in os.listdir(input_dir) if f.lower().endswith('.sql')]
            all_scripts.sort()  # Sort scripts alphabetically for sequential execution

        # Filter scripts
        scripts = filter_scripts(all_scripts, dev, vanilla)

        if not scripts:
            logger.warning(f"No SQL scripts found in {input_dir} after filtering.")
            console.print(f"No SQL scripts found in {input_dir} after filtering.", style="bold red")
            return
        
        logger.debug("Scripts to be executed in order:\n" + "\n".join(f"- {s}" for s in scripts))

        if not Confirm.ask(f"Run [bold blue]{input_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow] (dev={dev}, debug={debug})?"):
            logger.debug(f"Execution skipped for {input_dir}.")
            console.print(f"[bold red]Skipping {input_dir}[/bold red]")
            return

        # Execute scripts sequentially
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
    # options = {
    #     'server': r'dylans\mssqlserver2022',
    #     'database': 'test',
    #     'input': r'C:\LocalConv\conversion-boilerplate\needles\conversion\1_contact',
    #     'backup': False,
    #     'dev': False,
    #     'debug': False,
    #     'vanilla': False
    # }

    """Command-line interface entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Process SQL files and save results to an Excel file.")
    parser.add_argument("-s", "--server", required=True, help="SQL Server")
    parser.add_argument("-d", "--database", required=True, help="Database")
    parser.add_argument("-i", "--input", required=True, help="Path to the input folder containing SQL files.")
    
    args = parser.parse_args()

    # Build options dictionary
    options = {
        'server': args.server,
        'database': args.database,
        'input': args.input
    }

    run(options)