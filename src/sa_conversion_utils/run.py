import os
import re
from dotenv import load_dotenv
from sa_conversion_utils.db_utils import backup_db
from sa_conversion_utils.sql_runner import sql_runner
from .utilities.confirm import confirm_execution
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.prompt import Confirm

BASE_DIR = os.getcwd()
load_dotenv(os.path.join(BASE_DIR, '.env'))
SQL_DIR = os.getenv('SQL_DIR', 'default_sql_dir')
WORKING_DIR = os.path.join(BASE_DIR, SQL_DIR)
console = Console()

def exec_conv(options):
    server = options.get('server')
    database = options.get('database')
    folder = options.get('folder')
    backup = options.get('backup', False)
    skip = options.get('skip', False)
    debug = options.get('debug', False)

    sql_dir = os.path.join(SQL_DIR, folder)

    # Get list of SQL files
    try:
        scripts = [file for file in os.listdir(sql_dir) if file.lower().endswith('.sql')]

        # Omit files with "skip" in the name if the skip option is True
        if skip:
            scripts = [file for file in scripts if 'skip' not in file.lower()]

        if not scripts:
            console.print(f'No sql scripts found.', style="bold yellow")
            return
    except Exception as e:
        console.print(f'Error reading SQL scripts: {str(e)}', style="bold red")
        return

    try:
        if Confirm.ask(f"Run SQL scripts in [bold blue]{SQL_DIR}\\{folder}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow]"):
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
                task = progress.add_task(f"[cyan]Executing SQL Scripts", total=len(scripts))
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
                    
                    if debug and not Confirm.ask("[bold red]DEBUG MODE is active. Do you want to Continue?[/bold red]"):
                        console.print("Exiting", style="bold yellow")
                        return
                    
        # Backup process
        try:
            if backup:
                backup_db({
                    'database': database,
                    'output': os.path.join(BASE_DIR, 'backups'),
                    'server': server,
                    'message': 'AutoBackupAfterRun'
                })
            else:
                if Confirm.ask("SQL scripts completed. Backup database?"):
                    backup_db({
                        'database': database,
                        'output': os.path.join(BASE_DIR, 'backups'),
                        'server': server,
                        'message': 'AutoBackupAfterRun'
                    })
        except Exception as e:
            console.print(f'Error during backup: {str(e)}', style="bold red")

    except Exception as e:
        console.print(f'Error during SQL script execution: {str(e)}', style="bold red")
        return

    