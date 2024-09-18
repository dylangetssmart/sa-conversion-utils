import os
import pandas as pd
import time
from sqlalchemy import create_engine
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

# from ..utils.count_lines import count_lines_mmap
from sa_conversion_utils.utils.count_lines import count_lines_mmap

import sys
sys.setrecursionlimit(50000)  # Increase the limit as needed

console = Console()
encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']

def clean_csv(file_path):
    """
    \x00 -> NUL
    """
    for encoding in encodings:
        try:
            # Step 1: Remove NUL characters from the CSV file
            with open(file_path, 'r', encoding=encoding) as file:
                text = file.read().replace("\x00", "")
    
            # Write the cleaned text back to the file
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(text)

            # If successful, break out of the loop
            print(f"File cleaned successfully with encoding: {encoding}")
            return

        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            console.print(f"[yellow]Encoding error {file_path} with {encoding}. Error: {e}")
            continue
    raise ValueError(f"Unable to clean the file {file_path} with known encodings.")

# Function to read CSV with fallback encoding
def read_csv_with_fallback(file_path):
    for encoding in encodings:
        try:
            # return pd.read_csv(file_path, encoding=encoding, low_memory=False)
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
            return df, encoding
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            # console.print(f"[yellow]Encoding error {file_path} with {encoding}. Error: {e}")
            continue
    raise ValueError(f"Unable to read the file {file_path} with known encodings.")

def import_csv_to_sql(engine, table_name, file_path):
    start_time = time.time()
    file_name = os.path.basename(file_path)
    line_count = count_lines_mmap(file_path)

    records_imported = 0  # Initialize default values
    record_diff = line_count  # Initialize to max possible difference
    # Clean the file before reading
    clean_csv(file_path)

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        # TextColumn("[progress.percentage]{percentage:>6.1f}%"),
        # TextColumn("[progress.description]{task}")
    ) as progress:
        task = progress.add_task(f"Importing {file_name}", total=None)  # Total is unknown initially
        try:
            df, encoding_used = read_csv_with_fallback(file_path)

            if not df.empty:
                df.to_sql(table_name, engine, if_exists='append', index=False)
                progress.update(task, advance=len(df))  # Update progress based on DataFrame size

            console.print(f"[green]Success: Imported {file_name} into table {table_name} (encoding: {encoding_used}).")

        except Exception as e:
            console.print(f"[red]Failure: Could not import {file_name}. Error: {e}")

# Function to process either a single file or all files in a directory
def process_csv_files(engine, table_name, input_path):
    """
    Processes CSV files, importing them into a SQL database.
    
    If input_path is a directory, it imports all .csv files found in the directory.
    If input_path is a file, it imports the single CSV file.
    """

    # If input_path is a directory
    if os.path.isdir(input_path):      
        if Confirm.ask(f'{input_path} looks like a directory. Import all .csv files within?'):
            csv_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.csv')]
            if not csv_files:
                console.print(f"[yellow]No CSV files found in the directory: {input_path}")
                return
            with Progress(
                BarColumn(),
                SpinnerColumn()
                # TextColumn("[progress.percentage]{percentage:>6.1f}%"),
                # TextColumn("[progress.description]{task}",)
            ) as progress:
                for csv_file in csv_files:
                    task = progress.add_task(f"Importing {os.path.basename(csv_file)}", total=None)  # Total is unknown initially
                    import_csv_to_sql(engine, table_name, csv_file)
            # for csv_file in csv_files:
            #     table_name = os.path.splitext(os.path.basename(csv_file))[0]
            #     import_csv_to_sql(engine, table_name, csv_file)
    
    # If input_path is a file
    elif os.path.isfile(input_path):  
        if input_path.endswith('.csv'):
            # Derive the table name from the file name if table_name is not provided
            derived_table_name = table_name or os.path.splitext(os.path.basename(input_path))[0]
            import_csv_to_sql(engine, derived_table_name, input_path)
        else:
            console.print(f"[yellow]The specified file is not a CSV: {input_path}")
    else:
        console.print(f"[red]Invalid input path: {input_path}")

def main(options):
    server = options.get('server')
    database = options.get('database')
    table_name = options.get('table')
    input_path = options.get('input_path')
    conn_str = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
    engine = create_engine(conn_str)

    process_csv_files(engine, table_name, input_path)

    # Progress bar lives here

if __name__ == "__main__":
    options = {
        'server': 'DylanS\\MSSQLSERVER2022',
        'database': 'ShinerLitify',
        'input_path': 'C:\\LocalConv\\Litify-Shiner\\data\\litify_pm__lit_Note__c.csv',
        # 'table': 'test'
    }
    main(options)
