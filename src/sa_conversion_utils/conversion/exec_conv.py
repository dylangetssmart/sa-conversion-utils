import os
import re
from dotenv import load_dotenv
from ..database.db_utils import backup_db
from ..database.sql_runner import sql_runner
from ..utils.confirm import confirm_execution
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

BASE_DIR = os.getcwd()
load_dotenv(os.path.join(BASE_DIR, '.env'))
SQL_DIR = os.getenv('SQL_DIR')
WORKING_DIR = os.path.join(BASE_DIR, SQL_DIR)
# BASE_DIR = os.path.dirname(os.getcwd())
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# SQL_SCRIPTS_DIR = os.path.join(BASE_DIR, '../sql/shiner/')

console = Console()

# Possible options are 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
# https://docs.python.org/3/library/stdtypes.html#typesseq-range
sequence_patterns = {
    i: re.compile(rf'^{i}.*\.sql$', re.I) for i in range(10)
}


def exec_conv(options):
    server = options.get('server')
    database = options.get('database')
    sequence = options.get('sequence')
    backup = options.get('backup', False)
    run_all = options.get('run_all', False)
    
    if run_all:
        sequence = 'all'
    elif sequence == 0:
        # Check if sequence is exactly 0
        # Python considers numeric 0 to be false
        # https://stackoverflow.com/questions/34376441/if-not-condition-statement-in-python
        selected_pattern = sequence_patterns[sequence]
    else:
        if not sequence or sequence not in sequence_patterns:
            console.print('Invalid sequence option.', style="bold red")
            return

    try:
        all_files = os.listdir(WORKING_DIR)
        # files = [file for file in all_files if selected_pattern.match(file)]

        if sequence == 'all':
            # Execute all SQL scripts in the directory
            files = [file for file in all_files if file.lower().endswith('.sql')]
        else:
            # Filter files based on sequence pattern
            selected_pattern = sequence_patterns[sequence]
            files = [file for file in all_files if selected_pattern.match(file)]

        if not files:
            console.print(f'No scripts found for pattern: {selected_pattern}', style="bold yellow")
            return
        else:
            custom_message = f"execute SQL sequence {sequence}"
            if not confirm_execution(server, database, custom_message):
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
                console=console
            ) as progress:
                task = progress.add_task(f"[cyan]Executing SQL Scripts Sequence: {sequence}", total=len(files))
                for file in files:
                    # progress.console.log(f"Processing file: {file}")
                    script_task = progress.add_task(f"[yellow]Running {file}")
                    sql_runner(
                        os.path.join(WORKING_DIR, file),
                        server,
                        database,
                        script_task,
                        progress
                    )
                    progress.update(task, advance=1)
                    # console.print(f'Executed {file}', style="green")
    except Exception as e:
        console.print(f'Error reading directory {WORKING_DIR}\n{str(e)}', style="bold red")

    if backup:    
        backup_db({
            'database': database,
            'directory': os.path.join(BASE_DIR, 'backups'),
            'sequence': sequence,
            'server': server,
            'message': 'AutoBackupFromExecute'
        })