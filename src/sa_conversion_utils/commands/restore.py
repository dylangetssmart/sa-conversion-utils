# Standard Library Imports
import os
import subprocess
import tkinter as tk
import argparse
import logging
from dotenv import load_dotenv

# Third Party Imports
from tkinter import filedialog
from rich.console import Console
from rich.prompt import Confirm

# Global Constants
logger = logging.getLogger(__name__)
console = Console()

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file
DEFUALT_SERVER = os.getenv("SERVER")
DEFAULT_DB = os.getenv("TARGET_DB")

# Find a directory named "backup" in the current working directory.
# If not found, use a default path in "backups".
backup_dir_in_cwd = os.path.join(os.getcwd(), "backups")
DEFAULT_BACKUP_DIR = backup_dir_in_cwd if os.path.isdir(backup_dir_in_cwd) else os.path.join(os.getcwd(), "backups")


def select_bak_backup_file():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    initial_dir = os.path.join(os.getcwd(), "backups")
    backup_file = filedialog.askopenfile(
        title="Select the .bak backup_file to restore",
        filetypes=[("SQL Backup backup_files", "*.bak")],
        initialdir=initial_dir,
    )
    if backup_file:
        return backup_file.name  # Return the path to the file
    return None


def restore(args: argparse.Namespace):
    server = args.server
    database = args.database
    backup_dir = args.backup_dir

    if not server:
        logger.error("Missing SQL Server argument")
        raise ValueError("Missing SQL Server argument")
    if not database:
        logger.error("Missing database argument")
        raise ValueError("Missing database argument")

    # Open a file dialog to select the backup file.
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    backup_file = filedialog.askopenfilename(
        title="Select the .bak backup file to restore",
        filetypes=[("SQL Backup files", "*.bak")],
        initialdir=backup_dir,
    )

    if not backup_file:
        console.print("[red]No backup file selected. Exiting restore operation.[/red]")
        return

    console.print(f"[green]Backup file found: {backup_file}[/green]")

    if Confirm.ask(
        f"Restore [magenta]{server}[/magenta].[cyan]{database}[/cyan] using [yellow]{backup_file}[/yellow]?"
    ):
        console.print(f"Reverting database: {server}.{database}")

        # Put the database in single user mode
        logger.debug(f"Putting database {database} in single user mode ...")
        console.print(f"\nPutting database {database} in single user mode ...")
        try:
            subprocess.run(
                [
                    "sqlcmd",
                    "-S",
                    server,
                    "-Q",
                    f"ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;",
                    "-b",
                    "-d",
                    "master",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.error(f"Failed to set database {database} to single user mode. Exiting script.")
            console.print(
                f"Failed to set database {database} to single user mode. Exiting script."
            )
            return

        # Restore the database
        print(f"\nRestoring database {database} from {backup_file} ...")
        try:
            subprocess.run(
                [
                    "sqlcmd",
                    "-S",
                    server,
                    "-Q",
                    f"RESTORE DATABASE [{database}] FROM DISK='{backup_file}' WITH REPLACE, RECOVERY;",
                    "-b",
                    "-d",
                    "master",
                ],
                check=True,
            )
            logger.info(f"Database {database} restored successfully from {backup_file}.")
            console.print(f"Database {database} restored successfully from {backup_file}.")
        except subprocess.CalledProcessError:
            logger.error(f"Database restore failed. Check the SQL server error log for details.")
            console.print(
                "Database restore failed. Check the SQL server error log for details."
            )
            return

        # Set the database back to multi-user mode
        logger.debug(f"Putting database {database} back in multi-user mode ...")
        console.print(f"\nPutting database {database} back in multi-user mode ...")
        try:
            subprocess.run(
                [
                    "sqlcmd",
                    "-S",
                    server,
                    "-Q",
                    f"ALTER DATABASE [{database}] SET MULTI_USER;",
                    "-b",
                    "-d",
                    "master",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.error(f"Failed to set database {database} back to multi-user mode. Manual intervention may be required.")
            console.print(f"Failed to set database {database} back to multi-user mode. Manual intervention may be required.")
        finally:
            logger.info(f"Restore operation completed for {server}.{database}")
            console.print(f"[green]Restore operation completed for {server}.{database}[/green]")


def setup_parser(subparsers):
    """
    Configures the parser for the 'restore' subcommand.
    """
    restore_parser = subparsers.add_parser("restore", help="Restore a database from a backup file.")
    restore_parser.add_argument(
        "-s",
        "--server",
        default=DEFUALT_SERVER,
        help="SQL Server")
    restore_parser.add_argument(
        "-d",
        "--database",
        default=DEFAULT_DB,
        help="Database to restore"
    )
    restore_parser.add_argument(
        "--backup-dir",
        default="backups",
        help="Directory where backup files are stored",
    )
    restore_parser.set_defaults(func=restore)