# External
import os
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm

# Module imports
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.config.user_config import load_user_config
from sa_conversion_utils.database.backup import add_backup_parser
from sa_conversion_utils.database.restore import add_restore_parser
from sa_conversion_utils.run.run import add_run_parser
from sa_conversion_utils.map.map import map as generate_mapping
from sa_conversion_utils.export.export_old import add_export_parser
from sa_conversion_utils.config.config import add_config_parser
from sa_conversion_utils.convert.flat_to_sql import main as import_flat_file
from sa_conversion_utils.convert.psql_to_csv import main as convert_psql_to_csv

from sa_conversion_utils.export.export import add_export_parser


logger = setup_logger(__name__, log_file="sami.log")
console = Console()
BASE_DIR = os.path.dirname(__file__)
load_dotenv()

""" Load environment variables from .env file """
# config = load_user_config({
#     "SERVER": "Enter the SQL Server name",
#     "SOURCE_DB": "Enter the source database name",
#     "TARGET_DB": "Enter the target SmartAdvocate DB name",
#     "SQL_DIR": "Enter the SQL directory path",

# })

# logger.debug(f"Config loaded from .env file: \n{config}")
# # for k, v in config.items():
# #     print(f"{k} = {v}")

# SERVER = config["SERVER"]
# SOURCE_DB = config["SOURCE_DB"]
# SA_DB = config["TARGET_DB"]
# SQL_DIR = config["SQL_DIR"]

# SERVER = "dylans\\msqlserver2022"
# SOURCE_DB = "VanceLawFirm_Needles"
# SA_DB = "VanceLawFirm_SA"
# SQL_DIR = "needles\\conversion"


def map(args):
    options = {
        "server": args.server or os.getenv('SERVER'),
        "database": args.database or os.getenv('SOURCE_DB'),
        "input": args.input,
    }
    generate_mapping(options)


def encrypt(args):
    exe_path = r"C:\LocalConv\_utils\SSNEncryption\SSNEncryption.exe"
    try:
        # Execute the SSNEncryption.exe
        result = os.system(exe_path)

        if result == 0:
            print("SSN encryption completed successfully.")
        else:
            print(f"SSN encryption failed with exit code {result}.")
    except Exception as e:
        print(f"An error occurred while running SSN encryption: {str(e)}")


def handle_import_flat_file(args):
    options = {
        "server": args.server or os.getenv('SERVER'),
        "database": args.database or os.getenv('SOURCE_DB'),
        "username": args.username,
        "password": args.password,
        "input_path": args.input,
        "chunk_size": args.chunk,
        "if_exists": args.exists,
    }
    import_flat_file(options)


def handle_convert_psql_to_csv(args):
    options = {
        "server": args.server,
        "database": args.database,
        "username": args.username,
        "password": args.password,
        "output": args.output,
    }
    convert_psql_to_csv(options)


def merge_args_with_env(args) -> dict:
    return {
        "server": args.server or os.getenv('SERVER'),
        "database": args.database or os.getenv('SOURCE_DB'),
        "username": args.username,
        "password": args.password,
        "output": args.output,
    }


def main():
    parser = argparse.ArgumentParser(description="SmartAdvocate Data Conversion CLI.")

    # Global flags
    # parser.add_argument('-s', '--server', help='Server name. Defaults to SERVER from .env', metavar='')
    # parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env', metavar='')
    # parser.add_argument('-u', '--username', help='SQL Server username. If omitted, a trusted connection is used.', metavar='')
    # parser.add_argument('-p', '--password', help='SQL Server password. If omitted, a trusted connection is used.', metavar='')
    # parser.add_argument('-o', '--output', help='Output directory.', metavar='')

    # Subcommands
    subparsers = parser.add_subparsers(title="operations", dest="subcommand")
    subparsers.required = True

    # Command: export
    add_export_parser(subparsers)

    # Command: config
    add_config_parser(subparsers)

    # Command: backup
    add_backup_parser(subparsers)

    # Command: restore
    add_restore_parser(subparsers)

    # Command: map
    mapping_parser = subparsers.add_parser(
        "map", help="Run SQL scripts in \\map and output the results to Excel."
    )
    # mapping_parser.add_argument('system', help='SQL Script sequence to execute.', choices=['needles'], type=str)
    # mapping_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    # mapping_parser.add_argument('-d', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    mapping_parser.add_argument(
        "-i", "--input", help="Input path of sql scripts", metavar=""
    )
    mapping_parser.set_defaults(func=map)

    # Command: run
    add_run_parser(subparsers)

    # command: export
    # add_export_parser(subparsers)
    # export_parser = subparsers.add_parser('export', help='Export data from a database')

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: encrypt
    encrypt_parser = subparsers.add_parser("encrypt", help="Run SSN Encryption")
    encrypt_parser.set_defaults(func=encrypt)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: import
    import_parser = subparsers.add_parser("import", help="Import data into SQL")
    import_subparsers = import_parser.add_subparsers(
        title="Convert Variants", dest="convert_variant"
    )

    # Subcommand: flat file
    flat_file_parser = import_subparsers.add_parser(
        "flat-file",
        help="Import data from flat files to SQL. Leave username and password blank to use windows authentication",
    )
    flat_file_parser.add_argument(
        "-s", "--server", help="Server name. Defaults to SERVER from .env.", metavar=""
    )
    flat_file_parser.add_argument(
        "-d",
        "--database",
        help="Database name. Defaults to SA_DB from .env.",
        metavar="",
    )
    flat_file_parser.add_argument(
        "-u", "--username", help="SQL Server username", metavar=""
    )
    flat_file_parser.add_argument(
        "-p", "--password", help="SQL Sever password", metavar=""
    )
    flat_file_parser.add_argument(
        "-i", "--input", required=True, help="Path to CSV file or directory"
    )
    flat_file_parser.add_argument(
        "-c",
        "--chunk",
        type=int,
        default=10000,
        help="Number of rows to process at a time. Defaults = 2,000 rows. More = faster but uses more memory",
    )
    flat_file_parser.add_argument(
        "--exists",
        choices=["append", "fail", "replace"],
        default="replace",
        help="Specify how to handle existing tables: 'append' (default), 'fail', or 'replace'",
    )
    flat_file_parser.set_defaults(func=handle_import_flat_file)

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

    if "func" not in args:
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
