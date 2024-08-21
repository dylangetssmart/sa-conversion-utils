import pandas as pd
from sqlalchemy import create_engine
import os

# Variables for database connection
# db_server = "DYLANS"
# db_name = "NeedlesSLF"

# Directory containing SQL files and output directory
sql_dir = '../sql-scripts/mapping'
output_dir = '../sql-scripts/mapping'

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

    # Save DataFrames to Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

def generate_mapping(options):
    server = options.get('server')
    database = options.get('database')
    conn_str = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

    # Get the current working directory
    base_dir = os.path.dirname(__file__)
    
    # Construct full paths using relative paths
    full_sql_dir = os.path.abspath(os.path.join(base_dir, sql_dir))
    # full_output_dir = os.path.abspath(os.path.join(base_dir, output_dir))
    
    # Ensure output directory exists
    # os.makedirs(full_output_dir, exist_ok=True)
    
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
    
    # Iterate over SQL files
    for filename in os.listdir(full_sql_dir):
        if filename.endswith('.sql'):
            full_file_path = os.path.join(full_sql_dir, filename)
            sheet_name = os.path.splitext(filename)[0]  # Use filename without extension as sheet name
            try:
                with open(full_file_path, 'r') as file:
                    query = file.read().strip()
                    # Choose additional columns based on file or content type
                    if 'party_roles' in filename.lower():
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
    
    parent_dir_name = os.path.basename(os.path.abspath(os.path.join(base_dir, os.pardir)))

    # Save all DataFrames to a single Excel file
    output_filename = f'{parent_dir_name} Mapping Template.xlsx'
    output_path = os.path.join(base_dir, output_filename)
    save_to_excel(dataframes, base_dir)
    
    print(f'Saved results to {output_path}')

# if __name__ == "__main__":
#     main()
