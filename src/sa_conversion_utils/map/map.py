import os
import re
import pandas as pd
from rich.console import Console
from rich.prompt import Confirm
from sa_conversion_utils.utilities.create_engine import main as create_engine
from sa_conversion_utils.utilities.setup_logger import setup_logger

logger = setup_logger(__name__, log_file="map.log")

console = Console()

# Utility functions
def clean_string(value):
    """Remove non-printable or control characters from a string."""
    if isinstance(value, str):
        return re.sub(r'[\x00-\x1F\x7F-\x9F]', '', value)
    return value

def sanitize_dataframe(df):
    """Sanitize a DataFrame by cleaning its string values."""
    return df.map(clean_string)

def execute_query(query, engine, additional_columns=None):
    """Execute a SQL query and return the result as a DataFrame."""
    try:

        # Remove USE statement from the query
        # query = re.sub(r'^\s*USE\s+\S+.*$', '', query, flags=re.IGNORECASE | re.MULTILINE).strip()
        # query = re.split(r'^\s*GO\s*$', query, flags=re.MULTILINE | re.IGNORECASE)

        if not query:
            logger.warning("Query is empty after removing USE statement.")
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

def process_sql_files(mapping_dir, engine, user_columns, party_role_columns):
    """Process SQL files in the mapping directory and execute their queries."""
    PRIORITY_ORDER = [
        'Case Types',
        'Case Staff',
        'Party Roles',
        'Value Codes',
        'Intake'
    ]

    # 1. Get all .sql filenames
    all_sql_files = [f for f in os.listdir(mapping_dir) if f.endswith('.sql')]

    # 2. Sort filenames by PRIORITY_ORDER first, then alphabetically
    def sort_key(filename):
        sheet_name = os.path.splitext(filename)[0]
        try:
            return (PRIORITY_ORDER.index(sheet_name), sheet_name)
        except ValueError:
            return (float('inf'), sheet_name)

    sorted_files = sorted(all_sql_files, key=sort_key)

    dataframes = {}

    # for filename in os.listdir(mapping_dir):
    for filename in sorted_files:
        if filename.endswith('.sql'):
            full_file_path = os.path.join(mapping_dir, filename)
            sheet_name = os.path.splitext(filename)[0]
            try:
                with open(full_file_path, 'r') as file:
                    query = file.read().strip()

                    if 'Party Roles' in filename.lower():
                        df = execute_query(query, engine, additional_columns=party_role_columns)
                    elif 'Value Codes' in filename.lower() or 'user' in filename.lower():
                        df = execute_query(query, engine, additional_columns=user_columns)
                    else:
                        df = execute_query(query, engine)

                    if not df.empty:
                        dataframes[sheet_name] = df
                    else:
                        logger.warning(f"Empty DataFrame for SQL file: {filename}")
            except Exception as e:
                logger.error(f"Failed to read SQL file {filename}: {e}")
    return dataframes

def map(options):
    """Main function to process SQL files and save results to an Excel file."""
    server = options.get('server')
    database = options.get('database')
    input_dir = options.get('input')

    if not Confirm.ask(f"Run [bold blue]{input_dir}[/bold blue] -> [bold yellow]{server}.{database}[/bold yellow]"):
        logger.info(f"Execution skipped for {input_dir}.")
        return

    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        console.print(f"[red]Input directory does not exist: {input_dir}[/red]")
        return

    engine = create_engine(server=server, database=database)

    user_columns = {
        "SmartAdvocate Section": None,
        "SmartAdvocate Screen": None,
        "SmartAdvocate Field": None,
        "Contact Role": None,
        "Contact Category": None,
        "Contact Type": None,
        "Comment": None
    }

    party_role_columns = {
        "SA Role": None,
        "SA Party": None
    }

    # Process SQL files
    dataframes = process_sql_files(input_dir, engine, user_columns, party_role_columns)

    # Save results to Excel
    parent_dir_name = os.path.basename(os.path.abspath(os.getcwd()))
    output_filename = f'{parent_dir_name} Data Mapping.xlsx'
    output_path = os.path.join(os.getcwd(), output_filename)
    save_to_excel(dataframes, output_path)

    console.print(f"[green]Saved results to {output_path}[/green]")
    logger.info(f"Saved results to {output_path}")

if __name__ == "__main__":
    """Command-line interface entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Process SQL files and save results to an Excel file.")
    parser.add_argument("-s", "--server", required=True, help="SQL Server")
    parser.add_argument("-d", "--database", required=True, help="Database")
    parser.add_argument("-i", "--input", required=True, help="Path to the input folder containing SQL files.")
    
    args = parser.parse_args()

    options = {
        'server': args.server,
        'database': args.database,
        'input': args.input
    }

    map(options)