import os
import argparse
import logging

# Commands
from .commands.backup import setup_parser as backup_parser
from .commands.restore import setup_parser as restore_parser
from .commands.run.run import setup_parser as run_parser
from .extract_highrise.main import add_extract_highrise_parser
# from .commands.map import map as generate_mapping
from .commands.encrypt import setup_parser as encrypt_parser
from .commands.postgresql.export_csv import setup_parser as export_postgresql_csv_parser
# from .commands.sqlserver.import_csv import setup_parser as import_sqlserver_csv_parser

# Utils
# from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from .logging.logger_config import logger_config

# External
from rich.console import Console
from dotenv import load_dotenv


logger_config()
logger = logging.getLogger(__name__)

# logger = setup_logger(__name__, log_file="sami.log")
console = Console()
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # Load environment variables from .env file





# def handle_import_flat_file(args):
#     options = {
#         "server": args.server or os.getenv('SERVER'),
#         "database": args.database or os.getenv('SOURCE_DB'),
#         "username": args.username,
#         "password": args.password,
#         "input_path": args.input,
#         "chunk_size": args.chunk,
#         "if_exists": args.exists,
#     }
#     import_flat_file(options)


# def handle_convert_psql_to_csv(args):
#     options = {
#         "server": args.server,
#         "database": args.database,
#         "username": args.username,
#         "password": args.password,
#         "output": args.output,
#     }
#     convert_psql_to_csv(options)


# def merge_args_with_env(args) -> dict:
#     return {
#         "server": args.server or os.getenv('SERVER'),
#         "database": args.database or os.getenv('SOURCE_DB'),
#         "username": args.username,
#         "password": args.password,
#         "output": args.output,
#     }


def main():
    """
    Main CLI entry point
    """
    logger.debug("Starting CLI application")

    # Setup CLI argument parser
    parser = argparse.ArgumentParser(description="SmartAdvocate Data Conversion Utilities.")
    subparsers = parser.add_subparsers(title="operations", dest="subcommand")
    subparsers.required = True

    # General subcommands
    backup_parser(subparsers)
    restore_parser(subparsers)
    add_extract_highrise_parser(subparsers)
    run_parser(subparsers)
    encrypt_parser(subparsers)

    # PostgreSQL export command and its subcommands
    postgresql_parser = subparsers.add_parser('postgresql', help='PostgreSQL specific commands.')
    postgresql_subparsers = postgresql_parser.add_subparsers(
        title="Supported exports",
        dest="export_command",
        required=True
    )
    export_postgresql_csv_parser(postgresql_subparsers)

    # # SQL Server import command and its subcommands
    # import_parser = subparsers.add_parser('import', help='SQL Server specific commands..')
    # import_subparsers = import_parser.add_subparsers(
    #     title="Supported imports",
    #     dest="import_command",
    #     required=True
    # )
    # import_sqlserver_csv_parser(import_subparsers)

    # Command: map
    # mapping_parser = subparsers.add_parser("map", help="Run SQL scripts in \\map and output the results to Excel.")
    # # mapping_parser.add_argument('system', help='SQL Script sequence to execute.', choices=['needles'], type=str)
    # # mapping_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    # # mapping_parser.add_argument('-d', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    # mapping_parser.add_argument("-i", "--input", help="Input path of sql scripts", metavar="")
    # mapping_parser.set_defaults(func=map)



    # command: export
    # add_export_parser(subparsers)
    # export_parser = subparsers.add_parser('export', help='Export data from a database')

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: encrypt
    # encrypt_parser = subparsers.add_parser("encrypt", help="Run SSN Encryption")
    # encrypt_parser.set_defaults(func=encrypt)

    # # ---------------------------------------------------------------------------------------------------------------------------------------------
    # # Command: import
    # import_parser = subparsers.add_parser("import", help="Import data into SQL")
    # import_subparsers = import_parser.add_subparsers(
    #     title="Convert Variants", dest="convert_variant"
    # )

    # # Subcommand: flat file
    # flat_file_parser = import_subparsers.add_parser(
    #     "flat-file",
    #     help="Import data from flat files to SQL. Leave username and password blank to use windows authentication",
    # )
    # flat_file_parser.add_argument(
    #     "-s", "--server", help="Server name. Defaults to SERVER from .env.", metavar=""
    # )
    # flat_file_parser.add_argument(
    #     "-d",
    #     "--database",
    #     help="Database name. Defaults to SA_DB from .env.",
    #     metavar="",
    # )
    # flat_file_parser.add_argument(
    #     "-u", "--username", help="SQL Server username", metavar=""
    # )
    # flat_file_parser.add_argument(
    #     "-p", "--password", help="SQL Sever password", metavar=""
    # )
    # flat_file_parser.add_argument(
    #     "-i", "--input", required=True, help="Path to CSV file or directory"
    # )
    # flat_file_parser.add_argument(
    #     "-c",
    #     "--chunk",
    #     type=int,
    #     default=10000,
    #     help="Number of rows to process at a time. Defaults = 2,000 rows. More = faster but uses more memory",
    # )
    # flat_file_parser.add_argument(
    #     "--exists",
    #     choices=["append", "fail", "replace"],
    #     default="replace",
    #     help="Specify how to handle existing tables: 'append' (default), 'fail', or 'replace'",
    # )
    # flat_file_parser.set_defaults(func=handle_import_flat_file)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: export
    # export_parser = subparsers.add_parser("export", help="Export data from a database")
    # export_subparsers = export_parser.add_subparsers(
    #     title="Supported exports", dest="convert_variant"
    # )

    # # Subcommand: convert psql-to-csv
    # psql_to_csv_parser = export_subparsers.add_parser(
    #     "psql-csv", help="Export PostgreSQL tables to .csv"
    # )
    # psql_to_csv_parser.add_argument(
    #     "-s", "--server", required=True, help="PostgreSQL hostname"
    # )
    # psql_to_csv_parser.add_argument(
    #     "-d", "--database", required=True, help="PostgreSQL database name"
    # )
    # psql_to_csv_parser.add_argument(
    #     "-u", "--username", required=True, help="PostgreSQL username"
    # )
    # psql_to_csv_parser.add_argument(
    #     "-p", "--password", required=True, help="PostgreSQL password"
    # )
    # psql_to_csv_parser.add_argument(
    #     "-o", "--output", required=True, help="Output path for .csv files"
    # )
    # psql_to_csv_parser.set_defaults(func=handle_convert_psql_to_csv)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

    # if "func" not in args:
    #     parser.print_help()
    # else:
    #     args.func(args)

if __name__ == "__main__":
    main()