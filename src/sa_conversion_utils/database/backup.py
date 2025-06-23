import os
import subprocess
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm, Prompt

import argparse
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.config.user_config import load_user_config, REQUIRED_ENV_VARS
from sa_conversion_utils.utils.validate_dir import validate_dir

from dotenv import load_dotenv

logger = setup_logger(__name__, log_file="backup.log")
console = Console()
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file

def add_backup_parser(subparsers):
    """Add the backup command to the parser."""
    # env_config = load_user_config(REQUIRED_ENV_VARS)
    # logger.debug(f"Loaded environment config: {env_config}")

    backup_parser = subparsers.add_parser("backup", help="Backup SQL Server database.")
    backup_parser.add_argument("-s", "--server", help="SQL Server")
    backup_parser.add_argument("-d", "--database", help="Database")
    backup_parser.add_argument(
        "-o",
        "--output",
        default=os.path.join(os.getcwd(), "_backups"),
        help="Output path for the backup file.",
    )
    backup_parser.add_argument(
        "-m", "--message", help="Message to include in the backup filename."
    )
    backup_parser.set_defaults(func=handle_backup_command)


def handle_backup_command(args):
    """CLI dispatcher function for 'backup' subcommand."""
    options = {
        "server": args.server or os.getenv("SERVER"),
        "database": args.database or os.getenv("TARGET_DB"),
        "output": args.output,
        "message": args.message,
    }
    backup_db(options)


def backup_db(config: dict):
    print(config)
    print(os.getenv("SERVER"), os.getenv("TARGET_DB"))
    server = config.get("server")
    database = config.get("database")
    output_path = config.get("output")
    message = config.get("message")

    # Lazy load environment variables with defaults
    # server = server or os.getenv("SERVER")
    # database = database or os.getenv("TARGET_DB")

    if not server:
        logger.error("Missing SQL Server argument")
        raise ValueError("Missing SQL Server argument")
    if not database:
        logger.error("Missing database argument")
        raise ValueError("Missing database argument")
    if not message:
        message = Prompt.ask("Message to include in backup filename")

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


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Process SQL files and execute them in order."
    )
    subparsers = parser.add_subparsers(help="Available commands")

    # Add the 'run' command and its arguments
    add_backup_parser(subparsers)

    # Parse arguments and dispatch to the appropriate function
    args = parser.parse_args()

    # Call the function set by the parser (i.e., handle_run_command)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
