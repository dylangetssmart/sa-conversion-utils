import os
import pandas as pd
import time
from sqlalchemy import create_engine, exc, String, Integer, Float, DateTime, text
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

# Load environment variables
load_dotenv()
SERVER = os.getenv('SERVER')
LITIFY_DB = os.getenv('SOURCE_DB') # Import data to the source_db

# Set up the database connection using SQLAlchemy
connection_string = f'mssql+pyodbc://{SERVER}/{LITIFY_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
engine = create_engine(connection_string)

# Function to check if the database exists
def check_database_exists(engine, db_name):
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT database_id FROM sys.databases WHERE name = :db_name"), {'db_name': db_name})
        return result.scalar() is not None

# Check if the database exists before proceeding
if not check_database_exists(engine, LITIFY_DB):
    console = Console()
    console.print(f"[red]Error: Database '{LITIFY_DB}' does not exist on the server '{SERVER}'.")
    exit(1)

# Path to the directory containing the CSV files
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_directory = os.path.join(base_dir, 'data')

# Path to the .txt file containing CSV file information
info_file_path = os.path.join(csv_directory, 'AllCSV_NumLines.txt')

# Path to save the progress Excel file
import_log_file_path = os.path.join(os.path.join(os.getcwd(),'logs'),'import_log.xlsx')

console = Console()

# Parse the .txt file to get the list of files with data status
files_with_data = {}
with open(info_file_path, 'r', encoding='utf-16') as file:
    for line in file:
        parts = line.split()
        if len(parts) >= 4 and parts[3] == '1':
            file_path = os.path.join(parts[0], parts[1])
            file_name = os.path.basename(file_path)
            files_with_data[file_name] = {
                'line_count': int(parts[4])  # Number of lines from source file
            }

# DataFrame to record import progress
import_log_df = pd.DataFrame(columns=[
    'File Name', 'Lines in Source', 'Records Imported', 'Difference',
    'Time to Import (s)', 'Status', 'Timestamp', 'Encoding'
])

# Function to read CSV with fallback encoding
def read_csv_with_fallback(file_path):
    encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']
    for encoding in encodings:
        try:
            # return pd.read_csv(file_path, encoding=encoding, low_memory=False)
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
            return df, encoding
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            # console.print(f"[yellow]Encoding error {file_path} with {encoding}. Error: {e}")
            continue
    raise ValueError(f"Unable to read the file {file_path} with known encodings.")

# Function to import data from CSV to SQL Server
def import_csv_to_sql(file_path, table_name, total_task, file_task, progress):
    start_time = time.time()
    file_name = os.path.basename(file_path)
    line_count = files_with_data[file_name]['line_count'] - 1 # Account for header row

    records_imported = 0  # Initialize default values
    record_diff = line_count  # Initialize to max possible difference
    status = 'Unknown'  # Initialize status to unknown

    try:
        df, encoding_used = read_csv_with_fallback(file_path)
        if not df.empty:

            dtype_mapping = {}
            for col in df.columns:
                if df[col].isnull().all() and df[col].dtype in ['int64', 'float64']:
                    # Convert columns with all nulls to object (string)
                    df[col] = df[col].astype('object')
                else:
                    # Replace NaN values with None
                    df[col] = df[col].where(pd.notnull(df[col]), None)

                # Determine the SQL data type for each column
                if pd.api.types.is_integer_dtype(df[col]):
                    dtype_mapping[col] = Integer
                elif pd.api.types.is_float_dtype(df[col]):
                    dtype_mapping[col] = Float
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    dtype_mapping[col] = DateTime
                else:
                    dtype_mapping[col] = String

            # Convert int and float columns with all null values to object
                # for col in df.columns:
                #     if df[col].isnull().all() and df[col].dtype in ['int64', 'float64']:
                #         df[col] = df[col].astype('object')

            # Replace NaN values with an empty string in object columns
            # df = df.fillna('')

            # Convert all object columns to strings
            # object_columns = df.select_dtypes(include=['object']).columns
            # df[object_columns] = df[object_columns].astype(str)

            # Create a dtype mapping for SQLAlchemy
            # dtype_mapping = {col: String for col in df.columns}
                # dtype_mapping = {}
                # for col in df.columns:
                #     if pd.api.types.is_integer_dtype(df[col]):
                #         dtype_mapping[col] = Integer
                #     elif pd.api.types.is_float_dtype(df[col]):
                #         dtype_mapping[col] = Float
                #     elif pd.api.types.is_datetime64_any_dtype(df[col]):
                #         dtype_mapping[col] = DateTime
                #     else:
                #         dtype_mapping[col] = String
            
            # Write the DataFrame to the SQL table in chunks
            chunk_size = 2000
            for i, chunk in enumerate(range(0, len(df), chunk_size)):
                df_chunk = df.iloc[chunk:chunk + chunk_size]
                try:
                    df_chunk.to_sql(
                        table_name, engine, index=False, if_exists='append', 
                        dtype=dtype_mapping  # Apply the dtype mapping
                    )
                    progress.update(file_task, advance=len(df_chunk))
                except exc.SQLAlchemyError as e:
                    progress.console.print(f"[red]SQLAlchemy Error during import of chunk {i} for {file_name}. Error: {e}")
                    raise
                except TypeError as e:
                    progress.console.print(f"[red]Type Error during import of chunk {i} for {file_name}. Error: {e}")
                    raise
                except ValueError as e:
                    progress.console.print(f"[red]Value Error during import of chunk {i} for {file_name}. Error: {e}")
                    raise
                except Exception as e:
                    progress.console.print(f"[red]General Exception during import of chunk {i} for {file_name}. Error: {e}")
                    raise

            records_imported = len(df)
            record_diff = line_count - records_imported
            status = 'Success'
            progress.console.print(f"[green]Success: Imported {file_name} into table {table_name}.")
        else:
            records_imported = 0
            status = 'Skipped: Empty'
            progress.console.print(f"[yellow]Skipped: {file_name} is empty.")

    except Exception as e:
        records_imported = 0
        status = f'Failure: {e}'
        progress.console.print(f"[red]Failure: Could not import {file_name}. Error: {e}")

    end_time = time.time()
    time_to_import = end_time - start_time
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Record import progress
    import_log_df.loc[len(import_log_df)] = [
        file_name,
        f"{line_count:,}",
        f"{records_imported:,}",
        record_diff,
        time_to_import,
        status,
        timestamp,
        encoding_used
    ]

    # Explicitly mark file task as complete
    progress.update(file_task, completed=line_count)
    progress.update(total_task, advance=1)
    progress.remove_task(file_task)

# Record start time
start_time = time.time()

# Setup progress bar for total import and each file
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    "•",
    TimeElapsedColumn(),
    "•",
    TextColumn("{task.completed:,}/{task.total:,} lines"),
    console=console,
) as progress:

    total_task = progress.add_task("[cyan]Importing CSV files", total=len(files_with_data))

    for file_name, data in files_with_data.items():
        file_path = os.path.join(csv_directory, file_name)
        table_name = os.path.splitext(file_name)[0]  # Use file name (without extension) as table name
        
        # Create a task for each file
        file_task = progress.add_task(f"[yellow]Importing {file_name}", total=data['line_count'])
        
        # Import CSV to SQL
        import_csv_to_sql(file_path, table_name, total_task, file_task, progress)

# Save progress to Excel
import_log_df.to_excel(import_log_file_path, index=False)

# Record the end time and calculate execution time
end_time = time.time()
execution_time_seconds = end_time - start_time

# Convert execution time to hours, minutes, and seconds
hours = int(execution_time_seconds // 3600)
minutes = int((execution_time_seconds % 3600) // 60)
seconds = int(execution_time_seconds % 60)

console.print(f"[bold green]Execution time: {hours} hours, {minutes} minutes, {seconds} seconds")
