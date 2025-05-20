# Standard Library Imports
import os
import subprocess
import tkinter as tk
import argparse

# Third Party Imports
from tkinter import filedialog
from rich.console import Console
from rich.prompt import Confirm

# Local Imports
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.config.user_config import load_user_config, REQUIRED_ENV_VARS
from sa_conversion_utils.utils.validate_dir import validate_dir

# Global Constants
logger = setup_logger(__name__, log_file="restore.log")
console = Console()

"""
Helper Functions
"""


def find_backup_file(database, message, backup_dir="_backups"):
    """
    Searches for backup file with the specified database name and optional message in the filename.
    """
    backup_dir = os.path.join(os.getcwd(), backup_dir)
    logger.debug(f"Searching for backup files in: {backup_dir}")

    # List all matching files in the backup directory
    matching_files = [
        f
        for f in os.listdir(backup_dir)
        if os.path.isfile(os.path.join(backup_dir, f))
        and f.startswith(f"{database}_")
        and f.endswith(".bak")
    ]
    logger.debug(f"Matching files: {matching_files}")

    # Filter files based on the pattern
    filtered_files = [f for f in matching_files if f"{message}" in f.lower()]
    # filtered_files = [f for f in matching_files if f.startswith(f"{database}_{phase or ''}_{group or ''}")]
    logger.debug(f"Filtered files: {filtered_files}")

    # If exact match found, return the latest one based on date in the filename
    if filtered_files:
        filtered_files.sort(reverse=True)  # Sort files by latest date
        return os.path.join(backup_dir, filtered_files[0])

    # If no files match, return None
    logger.debug(
        f"No matching backup file found for database: {database} with message: {message}"
    )
    return None


def select_bak_backup_file():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    initial_dir = os.path.join(os.getcwd(), "_backups")
    backup_file = filedialog.askopenfile(
        title="Select the .bak backup_file to restore",
        filetypes=[("SQL Backup backup_files", "*.bak")],
        initialdir=initial_dir,
    )
    if backup_file:
        return backup_file.name  # Return the path to the file
    return None


"""
Main 'restore' Function
"""


def restore_db(config: dict):
    server = config.get("server")
    database = config.get("database")
    message = config.get("message")
    backup_dir = config.get("backup_dir", "_backups")
    virgin = config.get("virgin", False)

    if not server:
        logger.error("Missing SQL Server argument")
        raise ValueError("Missing SQL Server argument")
    if not database:
        logger.error("Missing database argument")
        raise ValueError("Missing database argument")

    if virgin:
        backup_file = r"C:\LocalConv\_virgin\SADatabase\SA 2024-12-04.bak"
    else:
        # Find the backup file based on provided options
        backup_file = find_backup_file(database, message, backup_dir)

        if not backup_file:
            console.print(
                "[yellow]No backup file found matching the specified criteria. Please select the .bak backup file manually.[/yellow]"
            )
            backup_file = select_bak_backup_file()

            if not backup_file:
                console.print("[red]No backup file selected. Exiting[/red]")
                return

    console.print(f"[green]Backup file found: {backup_file}[/green]")

    if Confirm.ask(
        f"Restore [magenta]{server}[/magenta].[cyan]{database}[/cyan] using [yellow]{backup_file}[/yellow]?"
    ):
        print(f"Reverting database: {server}.{database}")

        # Put the database in single user mode
        print(f"\nPutting database {database} in single user mode ...")
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
            print(
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
            print(f"Database {database} restored successfully from {backup_file}.")
        except subprocess.CalledProcessError:
            print(
                "Database restore failed. Check the SQL server error log for details."
            )
            return

        # Set the database back to multi-user mode
        print(f"\nPutting database {database} back in multi-user mode ...")
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
            print(
                f"Failed to set database {database} back to multi-user mode. Manual intervention may be required."
            )
        finally:
            console.print(
                f"[green]Restore operation completed for {server}.{database}[/green]"
            )


"""
CLI Functions
"""


def handle_restore_command(args):
    """Handles the 'restore' command and calls the restore_db function."""
    config = {
        "server": args.server,
        "database": args.database,
        "message": args.message,
        "backup_dir": args.backup_dir,
        "virgin": args.virgin,
    }
    restore_db(config)


def add_restore_parser(subparsers):
    """Adds the backup restore command to the argument parser."""
    env_config = load_user_config(REQUIRED_ENV_VARS)
    logger.debug(f"Loaded environment config: {env_config}")

    restore_parser = subparsers.add_parser(
        "restore", help="Restore a database from a backup file"
    )
    restore_parser.add_argument(
        "--server", default=env_config["SERVER"], help="SQL Server instance"
    )
    restore_parser.add_argument(
        "--database", default=env_config["TARGET_DB"], help="Database to restore"
    )
    restore_parser.add_argument(
        "--message", help="Optional message to match in backup file"
    )
    restore_parser.add_argument(
        "--backup-dir",
        default="_backups",
        help="Directory where backup files are stored",
    )
    restore_parser.add_argument(
        "--virgin", action="store_true", help="Use virgin database backup"
    )
    restore_parser.set_defaults(func=handle_restore_command)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Process SQL files and execute them in order."
    )
    subparsers = parser.add_subparsers(help="Available commands")

    # Add the 'run' command and its arguments
    add_restore_parser(subparsers)

    # Parse arguments and dispatch to the appropriate function
    args = parser.parse_args()

    # Call the function set by the parser (i.e., handle_run_command)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
