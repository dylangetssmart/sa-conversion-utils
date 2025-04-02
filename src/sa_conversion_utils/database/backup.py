import os
import sys
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from rich.console import Console
from rich.prompt import Confirm

console = Console()


# https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/create-a-full-database-backup-sql-server?view=sql-server-ver16#TsqlProcedure
# https://learn.microsoft.com/en-us/sql/t-sql/statements/backup-transact-sql?view=sql-server-ver16


def backup_db(options):
    server = options.get('server')
    database = options.get('database')
    output_path = options.get('output')
    message = options.get('message')
    
    if not server:
        raise ValueError("Missing SQL Server argument")
    if not database:
        raise ValueError("Missing database argument")

    # Create the backup filename
    timestamp = datetime.now().strftime('%Y-%m-%d')

    if message:
        filename = f"{database}_{message}_{timestamp}.bak"
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
            f"WITH NOFORMAT, NOINIT, NAME = '{database} Full Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10\""
        )

        try:
            with console.status('Backing up database...'):
                subprocess.run(backup_command, check=True, shell=True)
            console.print(f"[green]Backup complete: {backup_path}.")
        except subprocess.CalledProcessError as error:
            console.print(f"[red]Error backing up database {database}: {error}")