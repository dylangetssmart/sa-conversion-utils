import os
import re
from dotenv import load_dotenv
from ..database.db_utils import backup_db
from ..database.sql_runner import sql_runner
from ..utils.confirm import confirm_execution
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.prompt import Confirm

BASE_DIR = os.getcwd()
load_dotenv(os.path.join(BASE_DIR, '.env'))
SQL_DIR = os.getenv('SQL_DIR', 'default_sql_dir')
WORKING_DIR = os.path.join(BASE_DIR, SQL_DIR)

console = Console()

# Possible options are 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
series_patterns = {
    i: re.compile(rf'^{i}.*\.sql$', re.I) for i in range(10)
}

def exec_conv(options):
    server = options.get('server')
    database = options.get('database')
    series = options.get('series')
    backup = options.get('backup', False)
    run_all = options.get('run_all', False)
    init = options.get('init', False)
    map = options.get('map', False)
    post = options.get('post', False)

    # Determine directory based on flags
    if init:
        sql_dir = os.path.join(BASE_DIR, 'sql', 'init')
        script_type = 'init'
    elif map:
        sql_dir = os.path.join(BASE_DIR, 'sql', 'map')
        script_type = 'map'
    elif post:
        sql_dir = os.path.join(BASE_DIR, 'sql', 'post')
        script_type = 'post'
    else:
        sql_dir = os.path.join(BASE_DIR, 'sql', 'conv')
        script_type = 'conv'
    # if init:
    #     sql_dir = os.path.join(BASE_DIR, 'sql', 'needles', 'init')
    #     script_type = 'init'
    # elif map:
    #     sql_dir = os.path.join(BASE_DIR, 'sql', 'needles', 'map')
    #     script_type = 'map'
    # else:
    #     sql_dir = os.path.join(BASE_DIR, 'sql', 'needles', 'conv')
    #     script_type = 'conv'

    # Get list of SQL files
    try:
        scripts = [file for file in os.listdir(sql_dir) if file.lower().endswith('.sql')]

        # Filter scripts based on series pattern
        if not run_all:
            if series is not None and series in series_patterns:
                selected_pattern = series_patterns[series]
                scripts = [file for file in scripts if selected_pattern.match(file)]
            elif series is not None:
                console.print('Invalid series option.', style="bold red")
                return

        if not scripts:
            console.print(f'No scripts found for the specified pattern.', style="bold yellow")
            return
        
       # Dynamic confirmation prompt
        prompt_message = f"Execute SQL scripts in [bold yellow]sql\\{script_type}[/bold yellow]"
        if series is not None:
            prompt_message += f" series [bold yellow]{series}[/bold yellow]"
        prompt_message += f" against [bold yellow]{server}.{database}[/bold yellow]?"

        if Confirm.ask(prompt_message):
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
                task = progress.add_task(f"[cyan]Executing SQL Scripts Sequence: {series}", total=len(scripts))
                for file in scripts:
                    script_task = progress.add_task(f"[yellow]Running {file}")
                    sql_runner(
                        os.path.join(sql_dir, file),
                        server,
                        database,
                        script_task,
                        progress
                    )
                    progress.update(task, advance=1)

            if backup:
                backup_db({
                    'database': database,
                    'directory': os.path.join(BASE_DIR, 'backups'),
                    'sequence': series,
                    'server': server,
                    'message': 'AutoBackupFromExecute'
                })
            else:
                if Confirm.ask("The migration has been completed. Would you like to perform a backup now?"):
                    backup_db({
                    'database': database,
                    'directory': os.path.join(BASE_DIR, 'backups'),
                    'sequence': series,
                    'server': server,
                    'message': 'AutoBackupFromExecute'
                })

    except Exception as e:
        console.print(f'Error reading directory {sql_dir}\n{str(e)}', style="bold red")

