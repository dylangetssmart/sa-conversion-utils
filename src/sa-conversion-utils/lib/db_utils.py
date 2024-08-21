import os
import sys
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from rich.console import Console

console = Console()

def select_bak_backup_file():
    root = tk.Tk()
    root.withdraw()
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
    directory = options.get('directory')
    sequence = options.get('sequence')
    database = options.get('database')
    server = options.get('server')

    if not server:
        raise ValueError("Server environment variable is not set.")

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_path1 = os.path.join(directory, f'{database}-aftersequence-{sequence}_{timestamp}.bak')
    # backup_path2 = os.path.join(directory, f'{database_name2}-after-{sequence}_{timestamp}.bak')

    # Ensure the backup directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    backup_command1 = f"sqlcmd -S {server} -Q \"BACKUP DATABASE [{database}] TO DISK = '{backup_path1}' WITH FORMAT, INIT, NAME = '{database} Full Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10\""

    try:
        subprocess.run(backup_command1, check=True, shell=True)
        print(f"Backup for {database} completed successfully at {directory}.")
    except subprocess.CalledProcessError as error:
        print(f"Error backing up database {database}:", error)

def restore_db(options):
    server = options.get('server')
    database = options.get('database')
    virgin = options.get('virgin', False)

    if not server:
        print("Missing server parameter.")
        return

    if not database:
        print("Missing database parameter.")
        return

    if virgin:
        backup_file = r"C:\LocalConv\_virgin\SADatabase\SADatabase\SAModel_backup_2024_07_25_010001_5737827.bak"
    else:
        # Prompt user to select .bak backup_file using backup_file dialog
        print("Select the .bak backup_file to restore:")
        backup_file = select_bak_backup_file()

        if not backup_file:
            print("No backup_file selected. Exiting script.")
            return

    print(f'Revert database: {server}.{database}')

    # Put the database in single user mode
    print(f"\nPutting database {database} in single user mode ...")
    try:
        subprocess.run(
            ['sqlcmd', '-S', server, '-Q', f"ALTER database [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;", '-b', '-d', 'master'],
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"Failed to set database {database} to single user mode. Exiting script.")
        return

    # Restore the database
    print(f"\nRestoring database {database} from {backup_file} ...")
    try:
        subprocess.run(
            ['sqlcmd', '-S', server, '-Q', f"RESTORE database [{database}] FROM DISK='{backup_file}' WITH REPLACE, RECOVERY;", '-b', '-d', 'master'],
            check=True
        )
        print(f"database {database} restored successfully from {backup_file}.")
    except subprocess.CalledProcessError:
        print("database restore failed. Check the SQL server error log for details.")
        return

    # Set the database back to multi-user mode
    print(f"\nPutting database {database} back in multi-user mode ...")
    try:
        subprocess.run(
            ['sqlcmd', '-S', server, '-Q', f"ALTER database [{database}] SET MULTI_USER;", '-b', '-d', 'master'],
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"Failed to set database {database} back to multi-user mode. Manual intervention may be required.")

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