import os
import argparse
import pandas as pd
from rich.console import Console
from rich.prompt import Confirm
from dotenv import load_dotenv

from sa_conversion_utils.utils.create_engine import main as create_engine
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.utils.sanitize_utils import sanitize_dataframe

logger = setup_logger(__name__, log_file="map.log")
console = Console()
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))


def execute_query(query, engine, additional_columns=None):
    """Use pandas read_sql_query to execute a SQL query and return the result as a DataFrame."""
    try:

        # Remove USE statement from the query
        # query = re.sub(r'^\s*USE\s+\S+.*$', '', query, flags=re.IGNORECASE | re.MULTILINE).strip()
        # query = re.split(r'^\s*GO\s*$', query, flags=re.MULTILINE | re.IGNORECASE)

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
    """Save multiple DataFrames to an Excel file with different sheets."""
    if not dataframes:
        logger.warning("No data to save.")
        return

    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                sanitized_df = sanitize_dataframe(df)
                sanitized_df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"Excel file saved successfully to: {output_path}")
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"An error occurred while saving the Excel file: {e}")

def process_sql_files(mapping_dir, engine, special_columns_map):
    """Process SQL files in the mapping directory and execute their queries."""
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

                    # Find matching special columns by filename pattern
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

def map(options):
    """Run mapping scripts and save results to an Excel file."""
    server = options.get("server") or os.getenv("SERVER")
    database = options.get("database") or os.getenv("TARGET_DB")
    input_dir = options.get('input')

    if not Confirm.ask(f"Run [bold blue]{input_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow]"):
        logger.info(f"Execution cancelled.")
        return

    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        console.print(f"[red]Input directory does not exist: {input_dir}[/red]")
        return

    engine = create_engine(server=server, database=database)

    # Map filename patterns to their special columns
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

    # Process SQL files
    dataframes = process_sql_files(input_dir, engine, special_columns_map)

    # Save results to Excel
    output_filename = f"{os.path.basename(os.getcwd())} Data Mapping.xlsx"
    output_path = os.path.join(os.getcwd(), output_filename)
    save_to_excel(dataframes, output_path)

    logger.info(f"Saved results to {output_path}")
    console.print(f"[green]Saved results to {output_path}[/green]")

# if __name__ == "__main__":
#     """Command-line interface entry point."""
#     import argparse
#     parser = argparse.ArgumentParser(description="Process SQL files and save results to an Excel file.")
#     parser.add_argument("-s", "--server", required=True, help="SQL Server")
#     parser.add_argument("-d", "--database", required=True, help="Database")
#     parser.add_argument("-i", "--input", required=True, help="Path to the input folder containing SQL files.")
    
#     args = parser.parse_args()

#     options = {
#         'server': args.server,
#         'database': args.database,
#         'input': args.input
#     }

#     map(options)

""" CLI Integration """
def handle_map_command(args):
    options = {
        "server": args.server,
        "database": args.database,
        "input": args.input,
    }
    map(options)


def add_map_parser(subparsers):
    map_parser = subparsers.add_parser("map", help="Run mapping scripts and create Excel file.")
    map_parser.add_argument("-s", "--server", help="SQL Server")
    map_parser.add_argument("-d", "--database", help="Database")
    map_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input folder containing mapping scripts.",
    )
    map_parser.set_defaults(func=handle_map_command)


def main():
    parser = argparse.ArgumentParser(
        description="Process SQL files and execute them in order."
    )
    subparsers = parser.add_subparsers(help="Available commands")
    add_map_parser(subparsers)
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()