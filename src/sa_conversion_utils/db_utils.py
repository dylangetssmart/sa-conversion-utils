import os
import sys
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from rich.console import Console
from rich.prompt import Confirm

console = Console()

def find_backup_file(database, phase=None, group=None, backup_dir='backups'):
    """
    Finds the most recent backup file based on the database, phase, and group.
    """
    # Generate the expected filename pattern
    pattern = f"{database}_{phase or '*'}_{group or '*'}_*.bak"
    backup_dir = os.path.join(os.getcwd(), backup_dir)
    
    # List all matching files in the backup directory
    matching_files = [
        f for f in os.listdir(backup_dir)
        if os.path.isfile(os.path.join(backup_dir, f)) and f.startswith(f"{database}_") and f.endswith(".bak")
    ]
    
    # Filter files based on the pattern
    filtered_files = [f for f in matching_files if f.startswith(f"{database}_{phase or ''}_{group or ''}")]
    
    # If exact match found, return the latest one based on date in the filename
    if filtered_files:
        filtered_files.sort(reverse=True)  # Sort files by latest date
        return os.path.join(backup_dir, filtered_files[0])
    
    # If no files match, return None
    return None

def select_bak_backup_file():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    initial_dir = os.path.join(os.getcwd(), 'backups')
    backup_file = filedialog.askopenfile(
        title="Select the .bak backup_file to restore",
        filetypes=[("SQL Backup backup_files", "*.bak")],
        initialdir=initial_dir
    )
    if backup_file:
        return backup_file.name  # Return the path to the file
    return None

def backup_db(options):
    server = options.get('server')
    database = options.get('database')
    output_path = options.get('output')
    # message = options.get('message')
    phase = options.get('phase')
    group = options.get('group')

    if not server:
        raise ValueError("Missing SQL Server argument")
    if not database:
        raise ValueError("Missing database argument")

    # Create the backup filename
    timestamp = datetime.now().strftime('%Y-%m-%d')
    if phase and group:
        filename = f"{database}_{phase}_{group}_{timestamp}.bak"
    elif phase:
        filename = f"{database}_{phase}_{timestamp}.bak"
    else:
        filename = f"{database}_{timestamp}.bak"

    backup_path = os.path.join(output_path, filename)

    # Ensure the backup directory exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Confirm the backup operation
    if Confirm.ask(f'Backup {server}.{database} to {backup_path}?'):
        backup_command = (
            f"sqlcmd -S {server} -Q \"BACKUP DATABASE [{database}] TO DISK = '{backup_path}' "
            f"WITH FORMAT, INIT, NAME = '{database} Full Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10\""
        )

        try:
            with console.status('Backing up database...'):
                subprocess.run(backup_command, check=True, shell=True)
            console.print(f"[green]Backup complete: {backup_path}.")
        except subprocess.CalledProcessError as error:
            console.print(f"[red]Error backing up database {database}: {error}")

def restore_db(options):
    server = options.get('server')
    database = options.get('database')
    phase = options.get('phase')
    group = options.get('group')
    backup_dir = options.get('backup_dir', 'backups')
    manual = options.get('manual', False) 

    if not server:
        print("Missing server parameter.")
        return

    if not database:
        print("Missing database parameter.")
        return

    console.status(
        f"[yellow]Looking for backup file for database: {database}, phase: {phase}, group: {group}...[/yellow]"
        )

    # If 'manual' is True, skip file matching and go straight to file selection
    if manual:
        console.print("[yellow]Skipping automatic file search. Please select a backup file manually.[/yellow]")
        backup_file = select_bak_backup_file()
        if not backup_file:
            console.print("[red]No backup file selected. Exiting[/red]")
            return
    else:
        # Find the backup file based on provided options
        backup_file = find_backup_file(database, phase, group, backup_dir)

        if not backup_file:
            console.print("[yellow]No backup file found matching the specified criteria. Please select the .bak backup file manually.[/yellow]")
            backup_file = select_bak_backup_file()

            if not backup_file:
                console.print("[red]No backup file selected. Exiting[/red]")
                return

    console.print(f"[green]Backup file found: {backup_file}[/green]")

    if Confirm.ask(f"Restore [magenta]{server}[/magenta].[cyan]{database}[/cyan] using [yellow]{backup_file}[/yellow]?"):
        print(f'Reverting database: {server}.{database}')

        # Put the database in single user mode
        print(f"\nPutting database {database} in single user mode ...")
        try:
            subprocess.run(
                ['sqlcmd', '-S', server, '-Q', f"ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;", '-b', '-d', 'master'],
                check=True
            )
        except subprocess.CalledProcessError:
            print(f"Failed to set database {database} to single user mode. Exiting script.")
            return

        # Restore the database
        print(f"\nRestoring database {database} from {backup_file} ...")
        try:
            subprocess.run(
                ['sqlcmd', '-S', server, '-Q', f"RESTORE DATABASE [{database}] FROM DISK='{backup_file}' WITH REPLACE, RECOVERY;", '-b', '-d', 'master'],
                check=True
            )
            print(f"Database {database} restored successfully from {backup_file}.")
        except subprocess.CalledProcessError:
            print("Database restore failed. Check the SQL server error log for details.")
            return

        # Set the database back to multi-user mode
        print(f"\nPutting database {database} back in multi-user mode ...")
        try:
            subprocess.run(
                ['sqlcmd', '-S', server, '-Q', f"ALTER DATABASE [{database}] SET MULTI_USER;", '-b', '-d', 'master'],
                check=True
            )
        except subprocess.CalledProcessError:
            print(f"Failed to set database {database} back to multi-user mode. Manual intervention may be required.")
        finally:
            console.print(f"[green]Restore operation completed for {server}.{database}[/green]")

def create_db(options):
    server = options.get('server')
    db_name = options.get('name')

    try:
        subprocess.run(
            ['sqlcmd', '-S', server, '-Q', f"CREATE DATABASE {db_name}", '-b'],
            check=True
        )
        console.print(f"[green]Succesfully created database {db_name}.")
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to create database {db_name}.")

    # cmd = f"sqlcmd" '-S,', {server}, '-Q', f"CREATE DATABASE {db_name}"
    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # if result.returncode == 0:
    #     print("Database created successfully")
    # else:
    #     print("Error creating database:", result.stderr)

    # try:
    #     engine = create_engine('mssql+pyodbc://DYLANS\\MSSQLSERVER2022/master?driver=SQL+SERVER&trusted_connection=yes') 
    #     with engine.connect() as conn:
    #         conn.execute("CREATE DATABASE MyNewDatabase")
    # except Exception as e:
    #     print(f"Error connecting to database: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <function_name>")
        return

    function_name = sys.argv[1]

    if function_name == "backup":
        options = {
            'directory': 'C:/Backups',
            'sequence': '001',
            'database': 'MyDatabase',
            'server': 'MyServer',
            'virgin': False
        }
        backup_db(options)
    elif function_name == "restore":
        options = {
            'server': 'MyServer',
            'database': 'MyDatabase',
            'virgin': False
        }
        restore_db(options)
    elif function_name == "create":
        options = {
            'server': 'MyServer',
            'database': 'MyDatabase',
            'db_name': 'NewDatabaseName'  # Provide a default name
        }
        create_db(options)
    else:
        print(f"Invalid function name: {function_name}")

# def main():
#     options = {
#         'directory': 'C:/Backups',
#         'sequence': '001',
#         'database': 'MyDatabase',
#         'server': 'MyServer',
#         'virgin': False
#     }

#     backup_db(options)
#     restore_db(options)
#     create_db(options)

if __name__ == "__main__":
    main()