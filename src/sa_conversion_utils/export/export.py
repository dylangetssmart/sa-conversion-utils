import os
import argparse
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.run.sql_runner import sql_runner
from sa_conversion_utils.run.sort_scripts import sort_scripts_using_metadata
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.utils.validate_dir import validate_dir
from sa_conversion_utils.config.user_config import load_user_config, REQUIRED_ENV_VARS
from .psql_to_csv import export_all_tables_to_csv
from rich.prompt import Prompt, Confirm
from rich.console import Console

logger = setup_logger(__name__, log_file="export.log")
console = Console()

def add_export_parser(subparsers):
    """Add the export command to the parser."""
    # env_config = load_user_config(REQUIRED_ENV_VARS)
    # logger.debug(f"Loaded environment config: {env_config}")

    export_parser = subparsers.add_parser("export", help="Export data from database.")
    export_parser.add_argument(
        "--source",
        choices=["psql", "sql"],
        required=True,
        help="Source database type (psql or sql).",
    )
    export_parser.add_argument(
        "--target",
        choices=["csv", "sql"],
        required=True,
        help="Destination format (csv or sql).",
    )
    export_parser.add_argument("-s", "--server", help="SQL Server")
    export_parser.add_argument("-d", "--database", help="Database")
    # export_parser.add_argument("-s", "--server", default=env_config["SERVER"], help="SQL Server")
    # export_parser.add_argument("-d", "--database", default=env_config["TARGET_DB"], help="Database")
    export_parser.add_argument(
        "-o", "--output", required=True, help="Path to the output folder."
    )
    export_parser.add_argument(
        "-t",
        "--tables",
        nargs="+",
        help="List of tables to export (space-separated). If not provided, all tables are exported.",
    )
    # export_parser.add_argument(
    #     "--delimiter", default=",", help="Delimiter for CSV export (default: ',')."
    # )
    # export_parser.add_argument(
    #     "--quotechar",
    #     default='"',
    #     help="Character used to quote fields in CSV (default: '\"').",
    # )
    # export_parser.add_argument(
    #     "--null_string",
    #     default="",
    #     help="String to represent NULL values in CSV (default: '').",
    # )
    # export_parser.add_argument(
    #     "--header",
    #     action="store_true",
    #     default=True,
    #     help="Include header row in CSV export.",
    # )
    # export_parser.add_argument(
    #     "--encoding",
    #     default="utf8",
    #     help="Character encoding for CSV files (default: 'utf8').",
    # )
    export_parser.set_defaults(func=handle_export_command)


def handle_export_command(args):
    """CLI dispatcher function for 'export' subcommand."""
    options = {
        "source": args.source,
        "target": args.target,
        "server": args.server,
        "database": args.database,
        "output": args.output,
        "tables": args.tables,
        # "delimiter": args.delimiter,
        # "quotechar": args.quotechar,
        # "null_string": args.null_string,
        # "header": args.header,
        # "encoding": args.encoding,
    }
    export(options)


def export(options):
    """
    Export data from a database to a specified format.

    Args:
        options (dict): A dictionary containing the export options.
    """
    source_type = options["source"]
    target_type = options["target"]
    server = options["server"]
    database = options["database"]
    output_dir = options["output"]
    table_names = options["tables"]
    # delimiter = options["delimiter"]
    # quotechar = options["quotechar"]
    # null_string = options["null_string"]
    # header = options["header"]
    # encoding = options["encoding"]

    validate_dir(output_dir, logger)  # Ensure the output directory is valid

    if source_type == "psql" and target_type == "csv":
        user = Prompt.ask("Database username")
        password = Prompt.ask("Database password")
        export_all_tables_to_csv(
            host=server,
            dbname=database,
            user=user,
            password=password,
            output_dir=output_dir,
            table_names=table_names,
        )
    # _export_psql_to_csv(
    #     server,
    #     database,
    #     output_dir,
    #     table_names,
    #     delimiter,
    #     quotechar,
    #     null_string,
    #     header,
    #     encoding,
    # )
    elif source_type == "sql" and target_type == "sql":
        #  Add your SQL to SQL export logic here.
        console.print("[bright-yellow]SQL to SQL export not yet implemented[/bright-yellow]")
        logger.error("SQL to SQL export not yet implemented")
    elif source_type == "sql" and target_type == "csv":
        # Add your SQL to CSV export.
        console.print("[bright-yellow]SQL to CSV export not yet implemented[/bright-yellow]")
        logger.error("SQL to CSV export not yet implemented")
    elif source_type == "psql" and target_type == "sql":
        # Add your psql to sql export
        console.print("[bright-yellow]Postgres to SQL export not yet implemented[/bright-yellow]")
        logger.error("Postgres to SQL export not yet implemented")
    else:
        print(
            f"Error: Invalid combination of --source '{source_type}' and --target '{target_type}'"
        )
        logger.error(
            f"Invalid combination of --source '{source_type}' and --target '{target_type}'"
        )
        # raise ValueError(f"Invalid combination of --from '{from_type}' and --to '{to_type}'") # Removed the raise, so other commands can run


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Database migration and export utility."
    )
    subparsers = parser.add_subparsers(help="Available commands:")

    #  add_run_parser(subparsers) # Removed run command
    add_export_parser(subparsers)  # Add the new export command

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
