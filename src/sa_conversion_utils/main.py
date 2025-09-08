import os
import argparse
import logging

# Commands
from .commands.backup import setup_parser as backup_parser
from .commands.restore import setup_parser as restore_parser
from .commands.run.run import setup_parser as run_parser
from .commands.extract_highrise.main import add_extract_highrise_parser
from .commands.map import setup_parser as map_parser
from .commands.encrypt import setup_parser as encrypt_parser
from .commands.postgresql.export_csv import setup_parser as export_postgresql_csv_parser
from .commands.sqlserver.import_csv import setup_parser as import_sqlserver_csv_parser
from .logging.logger_config import logger_config

# External
from rich.console import Console
# from dotenv import load_dotenv

console = Console()
logger_config(rich_console=console)
logger = logging.getLogger(__name__)

# load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file

def main():
    """
    Main CLI entry point
    """
    logger.debug("Starting CLI application")

    # Setup CLI argument parser
    parser = argparse.ArgumentParser(description="SmartAdvocate Data Conversion Utilities.")
    subparsers = parser.add_subparsers(title="operations", dest="subcommand")
    subparsers.required = True

    # General Commands
    backup_parser(subparsers)
    restore_parser(subparsers)
    add_extract_highrise_parser(subparsers)
    run_parser(subparsers)
    encrypt_parser(subparsers)
    map_parser(subparsers)

    # PostgreSQL export command and its subcommands
    postgresql_parser = subparsers.add_parser('postgresql', help='PostgreSQL specific commands.')
    postgresql_subparsers = postgresql_parser.add_subparsers(
        title="Supported exports",
        dest="export_command",
        required=True
    )
    export_postgresql_csv_parser(postgresql_subparsers)

    # SQL Server import command and its subcommands
    sqlserver_parser = subparsers.add_parser('sqlserver', help='SQL Server specific commands.')
    sqlserver_subparsers = sqlserver_parser.add_subparsers(
        title="Supported imports",
        dest="import_command",
        required=True
    )
    import_sqlserver_csv_parser(sqlserver_subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()