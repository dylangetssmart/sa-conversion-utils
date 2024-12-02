import os
from dotenv import load_dotenv
from sa_conversion_utils.db_utils import backup_db
from sa_conversion_utils.sql_runner import sql_runner
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.prompt import Confirm, Prompt

BASE_DIR = os.getcwd()
load_dotenv(os.path.join(BASE_DIR, '.env'))
SQL_DIR = os.getenv('SQL_DIR', 'default_sql_dir')
WORKING_DIR = os.path.join(BASE_DIR, SQL_DIR)
console = Console()

def backup_database_helper(server, database): 
    
    message = Prompt.ask("Message to include in backup filename")

    backup_db({
        'database': database,
        'output': os.path.join(BASE_DIR, 'backups'),
        'server': server,
        'message': message
    })

def exec_conv(options):
    server = options.get('server')
    database = options.get('database')
    username = options.get('username')
    password = options.get('password')
    input_dir = options.get('input', 'sql/conv')  # Default folder if no input specified
    backup = options.get('backup', False)
    skip = options.get('skip', False)
    debug = options.get('debug', False)
    run_all = options.get('all', False)

    ordered_folders = ['init', 'contact', 'case', 'udf', 'misc', 'intake']

    # Determine which directories to process
    directories_to_process = (
        [os.path.join(input_dir, folder) for folder in ordered_folders] if run_all
        else [input_dir]
    )

    for sql_dir in directories_to_process:
        if not os.path.exists(sql_dir):
            console.print(f"[bold red]Directory not found: {sql_dir}[/bold red]")
            continue

        # console.print(f"[cyan]Processing directory: {sql_dir}[/cyan]")

        try:
            scripts = [file for file in os.listdir(sql_dir) if file.lower().endswith('.sql')]

            if skip:
                scripts = [file for file in scripts if 'skip' not in file.lower()]

            if not scripts:
                console.print(f"No SQL scripts found in {sql_dir}.", style="bold red")
                continue
        except Exception as e:
            console.print(f"Error reading SQL scripts in {sql_dir}: {str(e)}", style="bold red")
            continue

        if not Confirm.ask(f"Run [bold blue]{sql_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow] (skip={skip}, debug={debug})?"):
            console.print("[bold red]Skipping this directory[/bold red]")
            continue

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
            task = progress.add_task(f"[cyan]Executing SQL Scripts in {sql_dir}", total=len(scripts))
            for file in scripts:
                script_task = progress.add_task(f"[yellow]Running {file}[/yellow]")
                sql_runner(
                    os.path.join(sql_dir, file),
                    server,
                    database,
                    script_task,
                    progress,
                    username=username,
                    password=password
                )
                progress.update(task, advance=1)

                if debug:
                    progress.stop()
                    if not Confirm.ask("[yellow]DEBUG MODE is active. Continue?[/yellow]"):
                        console.print("Exiting", style="bold red")
                        return
                    progress.start()

        # Backup prompt after all scripts are executed
        if backup or Confirm.ask("SQL scripts completed. Backup database?"):
            try:
                backup_database_helper(server=server, database=database)
            except Exception as e:
                console.print(f"Error during backup: {str(e)}", style="bold red")