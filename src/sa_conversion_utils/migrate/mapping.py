import pandas as pd
from sqlalchemy import create_engine
import os
import re
from dotenv import load_dotenv
from ..utils.confirm import confirm_execution
# Variables for database connection
# db_server = "DYLANS"
# db_name = "NeedlesSLF"

# Directory containing SQL files and output directory
# sql_dir = '../sql/mapping'
# output_dir = '../sql/mapping'

# Load environment variables
load_dotenv()
# SERVER = os.getenv('SERVER')
# LITIFY_DB = os.getenv('SOURCE_DB') # Import data to the source_db
SQL_DIR = os.getenv('SQL_DIR', 'default_sql_dir')

# WORKING_DIR = os.path.join(os.getcwd(),SQL_SCRIPTS_DIR)

# Get the current working directory
base_dir = os.getcwd()

mapping_dir = os.path.join(os.getcwd(),SQL_DIR,'mapping')

def clean_string(value):
    if isinstance(value, str):
        # Remove any non-printable or control characters
        return re.sub(r'[\x00-\x1F\x7F-\x9F]', '', value)
    return value

def sanitize_dataframe(df):
    return df.map(clean_string)

def execute_query(query, engine, additional_columns=None):
    # Executes a SQL query and returns the result as a DataFrame with additional columns.
    try:
        df = pd.read_sql_query(query, engine)
        print(f"Query executed successfully.")
        
        # Add additional columns if provided
        if additional_columns:
            for col, default_value in additional_columns.items():
                if col not in df.columns:
                    df[col] = default_value
        
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()

def save_to_excel(dataframes, output_path):
    # Saves multiple DataFrames to an Excel file with different sheets.
    if not dataframes:
        print("No data to save.")
        return
    
    print(f"Attempting to save Excel file to: {output_path}")

    # Save DataFrames to Excel
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                # df.to_excel(writer, sheet_name=sheet_name, index=False)
                # Sanitize DataFrame before saving
                sanitized_df = sanitize_dataframe(df)
                sanitized_df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Excel file saved successfully to: {output_path}")
    except PermissionError as e:
        print(f"Permission denied: {e}")
    except Exception as e:
        print(f"An error occurred while saving the Excel file: {e}")


def generate_mapping(options):
    server = options.get('server')
    database = options.get('database')
    # conn_str = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    conn_str = f"mssql+pyodbc://sa:SAsuper@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

    """
    add an argument to use windows auth or accept a password (from .env)
    
    """


    custom_message = f"generate mapping template"
    if not confirm_execution(server, database, custom_message):
        return

    # Create SQLAlchemy engine
    engine = create_engine(conn_str)
    
    # Create a dictionary to store DataFrames for each query
    dataframes = {}
    
    # Define additional columns for general data and party roles
    general_columns = {
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
    
    # Iterate over SQL files in full_sql_dir
    for filename in os.listdir(mapping_dir):
        if filename.endswith('.sql'):
            full_file_path = os.path.join(mapping_dir, filename)
            sheet_name = os.path.splitext(filename)[0]  # Use filename without extension as sheet name
            try:
                with open(full_file_path, 'r') as file:
                    query = file.read().strip()
                    # Choose additional columns based on file or content type
                    if 'party_role' in filename.lower():
                        df = execute_query(query, engine, additional_columns=party_role_columns)
                    else:
                        df = execute_query(query, engine, additional_columns=general_columns)
                    
                    if not df.empty:
                        dataframes[sheet_name] = df
                    else:
                        print(f"Empty DataFrame for SQL file: {filename}")
            except Exception as e:
                print(f"Failed to read SQL file {filename}: {e}")
    
    # Debug print statements
    print(f"Queries executed: {len(dataframes)}")
    for name in dataframes:
        print(f"DataFrame '{name}' shape: {dataframes[name].shape}")
    
    parent_dir_name = os.path.basename(os.path.abspath(base_dir))
    # parent_dir_name = os.path.basename(os.path.abspath(os.path.join(base_dir, os.pardir)))

    # Save all DataFrames to a single Excel file
    output_filename = f'{parent_dir_name} Mapping Template.xlsx'
    output_path = os.path.join(base_dir, output_filename)
    save_to_excel(dataframes, output_path)
    
    print(f'Saved results to {output_path}')

# if __name__ == "__main__":
#     main()
