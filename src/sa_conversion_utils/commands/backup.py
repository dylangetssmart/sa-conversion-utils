import os
import subprocess
import argparse
import logging

from sa_conversion_utils.utils.validate_dir import validate_dir
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm, Prompt
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
console = Console()

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file
DEFUALT_SERVER = os.getenv("SERVER")
DEFAULT_DB = os.getenv("TARGET_DB")

# Find a directory named "backup" in the current working directory.
# If not found, use a default path in "workspace/backups".
backup_dir_in_cwd = os.path.join(os.getcwd(), "backup")
DEFAULT_OUTPUT = backup_dir_in_cwd if os.path.isdir(backup_dir_in_cwd) else os.path.join(os.getcwd(), "workspace\\backups")


def backup(args: argparse.Namespace):
    server = args.server
    database = args.database
    output_path = args.output
    message = args.message

    if not server:
        logger.error("Missing SQL Server argument")
        raise ValueError("Missing SQL Server argument")
    if not database:
        logger.error("Missing database argument")
        raise ValueError("Missing database argument")

    # Prompt for message if not provided
    if not message:
        message = Prompt.ask("Enter a message to include in backup filename")

    # Create the backup filename
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"{database}_{message}_{timestamp}.bak"
    backup_path = os.path.join(output_path, filename)

    # Check if the output directory exists, and create it if it doesn't
    if not validate_dir(output_path, logger, create_if_missing=True):
        logger.error(f"Failed to create backup directory: {output_path}")
        raise ValueError(f"Failed to create backup directory: {output_path}")

    # Confirm the backup operation
    # https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/create-a-full-database-backup-sql-server?view=sql-server-ver16#TsqlProcedure
    # https://learn.microsoft.com/en-us/sql/t-sql/statements/backup-transact-sql?view=sql-server-ver16
    if Confirm.ask(f"Backup {server}.{database} to {backup_path}?"):
        backup_command = (
            f"sqlcmd -S {server} -Q \"BACKUP DATABASE [{database}] TO DISK = '{backup_path}' "
            f"WITH NOFORMAT, INIT, NAME = '{database} Full Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10\""
        )

        try:
            with console.status("Backing up database..."):
                subprocess.run(backup_command, check=True, shell=True)
            console.print(f"[green]Backup complete: {backup_path}.")
        except subprocess.CalledProcessError as error:
            console.print(f"[red]Error backing up database {database}: {error}")


def setup_parser(subparsers):
    """
    Configures the parser for the 'backup' subcommand.
    """
    backup_parser = subparsers.add_parser("backup", help="Backup SQL Server database.")
    backup_parser.add_argument(
        "-s",
        "--server",
        default=DEFUALT_SERVER,
        help="SQL Server"
    )
    backup_parser.add_argument(
        "-d",
        "--database",
        default=DEFAULT_DB,    
        help="Database"
    )
    backup_parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output path for the backup file.",
    )
    backup_parser.add_argument(
        "-m",
        "--message",
        default="manual_backup",
        help="Message to include in the backup filename."
    )
    backup_parser.set_defaults(func=backup)