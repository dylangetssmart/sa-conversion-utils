import os
import argparse
import pandas as pd
import logging

from rich.console import Console
from rich.prompt import Confirm
from dotenv import load_dotenv

from ..utils.create_engine import main as create_engine
from ..utils.sanitize_utils import sanitize_dataframe
from ..logging.logger_config import logger_config

console = Console()
logger = logger_config(name=__name__, log_file="map.log", level=logging.DEBUG, rich_console=console)

def execute_query(query, engine, additional_columns=None):
    """
    Use pandas read_sql_query to execute a SQL query and return the result as a DataFrame.
    """
    try:
        if not query:
            logger.warning("Query is empty.")
            return pd.DataFrame()

        df = pd.read_sql_query(query, engine)
        if additional_columns:
            for col, default_value in additional_columns.items():
                if col not in df.columns:
                    df[col] = default_value
        return df
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return pd.DataFrame()

def save_to_excel(dataframes, output_path):
    """
    Save multiple DataFrames to an Excel file with different sheets.
    """
    if not dataframes:
        logger.warning("No data to save.")
        return

    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                sanitized_df = sanitize_dataframe(df)
                sanitized_df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"Excel file saved successfully to: {output_path}")
        console.print(f"[green]Excel file saved successfully to: {output_path}[/green]")
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        console.print(f"[red]Permission denied: {e}[/red]")
    except Exception as e:
        logger.error(f"An error occurred while saving the Excel file: {e}")
        console.print(f"[red]An error occurred while saving the Excel file: {e}[/red]")

def process_sql_files(mapping_dir, engine, special_columns_map):
    """
    Process SQL files in the mapping directory and execute their queries.
    """
    PRIORITY_ORDER = [
        'Case Types',
        'Case Staff',
        'Party Roles',
        'Value Codes',
        'Intake'
    ]

    all_sql_files = [f for f in os.listdir(mapping_dir) if f.endswith('.sql')]

    def sort_key(filename):
        sheet_name = os.path.splitext(filename)[0]
        try:
            return (PRIORITY_ORDER.index(sheet_name), sheet_name)
        except ValueError:
            return (float('inf'), sheet_name)

    sorted_files = sorted(all_sql_files, key=sort_key)
    dataframes = {}

    for filename in sorted_files:
        if filename.endswith('.sql'):
            full_file_path = os.path.join(mapping_dir, filename)
            sheet_name = os.path.splitext(filename)[0]
            try:
                with open(full_file_path, 'r') as file:
                    query = file.read().strip()

                    additional_columns = None
                    for pattern, columns in special_columns_map.items():
                        if pattern in filename.lower():
                            additional_columns = columns
                            break

                    df = execute_query(query, engine, additional_columns=additional_columns)

                    if not df.empty:
                        dataframes[sheet_name] = df
                    else:
                        logger.warning(f"Empty DataFrame for SQL file: {filename}")
            except Exception as e:
                logger.error(f"Failed to read SQL file {filename}: {e}")
    return dataframes

def map(args: argparse.Namespace):
    """
    Run mapping scripts and save results to an Excel file.
    """
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
    
    server = args.server or os.getenv("SERVER")
    database = args.database or os.getenv("TARGET_DB")
    input_dir = args.input

    if not Confirm.ask(f"Run [bold blue]{input_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow]?"):
        logger.info("Execution cancelled.")
        return

    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        console.print(f"[red]Input directory does not exist: {input_dir}[/red]")
        return

    engine = create_engine(server=server, database=database)

    special_columns_map = {
        'party roles': {
            "SA Role": None,
            "SA Party": None
        },
        'value codes': {
            "SmartAdvocate Screen": None,
            "SmartAdvocate Section": None,
            "SmartAdvocate Field": None,
            "Contact Role": None,
            "Contact Category": None,
            "Contact Type": None,
            "Comment": None
        },
        'user': {
            "SmartAdvocate Screen": None,
            "SmartAdvocate Section": None,
            "SmartAdvocate Field": None,
            "Contact Role": None,
            "Contact Category": None,
            "Contact Type": None,
            "Comment": None
        },
        'case staff': {
            'SmartAdvocate Role': None
        }
    }

    dataframes = process_sql_files(input_dir, engine, special_columns_map)

    output_filename = f"{os.path.basename(os.getcwd())} Data Mapping.xlsx"
    output_path = os.path.join(os.getcwd(), output_filename)
    save_to_excel(dataframes, output_path)

    logger.info(f"Saved results to {output_path}")

def setup_parser(subparsers):
    """
    Adds the 'map' subcommand to the main parser.
    """
    map_parser = subparsers.add_parser("map", help="Run mapping scripts and create an Excel file.")
    map_parser.add_argument(
        "-s", "--server",
        metavar="",
        help="SQL Server."
    )
    map_parser.add_argument(
        "-d", "--database",
        metavar="",
        help="Database."
    )
    map_parser.add_argument(
        "-i", "--input",
        required=True,
        metavar="",
        help="Path to the input folder containing mapping scripts."
    )
    map_parser.set_defaults(func=map)
