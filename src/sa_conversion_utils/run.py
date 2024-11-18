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
    # phase = options.get('phase')
    # group = options.get('group')
    input_dir = options.get('input')
    backup = options.get('backup', False)
    skip = options.get('skip', False)
    debug = options.get('debug', False)
    run_all = options.get('all', False)

    skip_confirm = False

    sql_dir = os.path.join(BASE_DIR, input_dir)

    # Map short group names to actual folder names
    # group_mapping = {
    #     'config': '0_config',
    #     'contact': '1_contact',
    #     'case': '2_case',
    #     'udf': '3_udf',
    #     'misc': '4_misc',
    #     'intake': '5_intake'
    # }

    # available_groups = list(group_mapping.values())

    # # If input directory is specified, use it directly and skip phase/group logic
    # if input_dir:
    #     sql_dir = os.path.join(BASE_DIR, input_dir)
    #     console.print(f"[cyan]Using custom input directory: {sql_dir}[/cyan]")
    #     groups_to_run = [None]  # Skip group processing
    # else:
    #     if phase == 'conv':
    #         if run_all:
    #             groups_to_run = available_groups
    #         elif group:
    #             # Map user input to the correct folder name
    #             mapped_group = group_mapping.get(group.lower())
    #             if mapped_group:
    #                 groups_to_run = [mapped_group]
    #             else:
    #                 console.print(f"[bold red]Error: Group '{group}' not found. Available groups are: {', '.join(group_mapping.keys())}[/bold red]")
    #                 return
    #         else:
    #             console.print("[bold red]Error: You must specify a group or use '--all' when phase is 'conv'.[/bold red]")
    #             return
    #     else:
    #         groups_to_run = [None]

    # # Process groups if no input directory is provided
    # if not input_dir:
    #     for grp in groups_to_run:
    #         # Construct the SQL directory path using phase and group
    #         sql_dir = os.path.join(SQL_DIR, phase, grp) if grp else os.path.join(SQL_DIR, phase)
    #         console.print(f"[cyan]Processing group: {grp} in directory: {sql_dir}[/cyan]")

    # Get list of SQL files
    try:
        scripts = [file for file in os.listdir(sql_dir) if file.lower().endswith('.sql')]

        # Omit files with "skip" in the name if the skip option is True
        if skip:
            scripts = [file for file in scripts if 'skip' not in file.lower()]

        if not scripts:
            console.print(f'No SQL scripts found in {sql_dir}.', style="bold red")
            return
    except Exception as e:
        console.print(f'Error reading SQL scripts: {str(e)}', style="bold red")
        return

    try:
        if not skip_confirm:
            if not Confirm.ask(f"Run [bold blue]{sql_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow]"):
                console.print('Exiting')
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
                task = progress.add_task(f"[cyan]Executing SQL Scripts", total=len(scripts))
                for file in scripts:
                    script_task = progress.add_task(f"[yellow]Running {file}")
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
                    
        # Backup process
        try:
            if backup:
                backup_database_helper(server=server, database=database)
                # backup_db({
                #     'database': database,
                #     'output': os.path.join(BASE_DIR, 'backups'),
                #     'server': server,
                #     'phase': phase,
                #     'group': group
                # })
            else:
                if Confirm.ask("SQL scripts completed. Backup database?"):
                    backup_database_helper(server=server, database=database)
                    # backup_db({
                    #     'database': database,
                    #     'output': os.path.join(BASE_DIR, 'backups'),
                    #     'server': server,
                    #     'message': message
                    #     # 'phase': phase,
                    #     # 'group': group
                    # })
        except Exception as e:
            console.print(f'Error during backup: {str(e)}', style="bold red")

    except Exception as e:
        console.print(f'Error during SQL script execution: {str(e)}', style="bold red")
        return
