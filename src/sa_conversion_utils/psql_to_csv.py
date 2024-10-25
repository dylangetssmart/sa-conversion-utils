import os
import subprocess
import sys

"""
1. get list of all tables, output to tables.txt
2. COPY data from each table to csv file
"""

# CONSTANTS

# Dictionary to exclude specific columns for specific tables
exclude_columns = {
        'user_profile': ['email_signature'],
    }

# Create the postgres_data directory inside the current working directory
current_dir = os.getcwd()
data_dir = os.path.join(current_dir, "postgres_data")  # Create a subdirectory 'postgres_data'


# Store a list of keywords that will break the query
# will be surrounded with double quotes in the query
reserved_keywords = ["order", "from", "group", "select", "active", "default", "to", "primary"]

def get_table_columns(hostname, database, username, table):
    
    """
    Query to fetch column names for the given table
    -t > Turn off printing of column names and result row count footers, etc.
        https://www.postgresql.org/docs/current/app-psql.html#APP-PSQL-OPTION-TUPLES-ONLY
    -A > Switches to unaligned output mode.
        https://www.postgresql.org/docs/current/app-psql.html#APP-PSQL-OPTION-NO-ALIGN
    """
    command = [
        "psql", "-h", hostname, "-d", database, "-U", username, "-t", "-A", "-c", 
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND table_schema = 'public';"
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=True)
    columns = [line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith("column_name")]

    return columns

def fetch_tables(hostname, database, username):
    # print("Fetching table list ...")
    tables_file = os.path.join(data_dir, "tables.txt")
    # tables_file = "tables.txt"
    command = ["psql", "-h", hostname, "-d", database, "-U", username, "-c", 
               "copy (select table_name from information_schema.tables where table_schema='public') to STDOUT;"]
    
    try:
        with open(tables_file, 'w') as f:
            subprocess.run(command, stdout=f, check=True)
    except subprocess.CalledProcessError:
        print("Failed to fetch table list.")
        sys.exit(4)

    print("Fetching tables ...")
    with open(tables_file, 'r') as f:
        tables = [line.strip() for line in f.readlines() if line.strip()]

    # Add a second column "Has Data"
    # tables = [f"{table}, 1" for table in sorted(tables)]
    tables = sorted(tables)

    # Optionally write the modified tables back to tables.txt (if needed)
    # with open(tables_file, 'w') as f:
    #     f.write('\n'.join(tables) + '\n')

    return tables

def copy_data(hostname, database, username, tables):

    # Create a directory to store the CSV files, named after the database
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    for table in tables:
        csv_file = os.path.join(data_dir, f"{table}.csv")
        # print(f"Fetching table: {table} ...")

        try:
            # Fetch column names for the table
            columns = get_table_columns(hostname, database, username, table)

            # Check for reserved keywords and wrap them in double quotes
            columns = [f'"{col}"' if col in reserved_keywords else col for col in columns]

            # Construct the query with properly escaped columns
            query = f"SELECT {', '.join(columns)} FROM {table}"

            command = ["psql", "-h", hostname, "-d", database, "-U", username, "-c", 
                       f"COPY ({query}) TO STDOUT WITH DELIMITER ',' CSV HEADER;"]

            with open(csv_file, 'w') as f:
                subprocess.run(command, stdout=f, check=True)
                print(f"PASS: {table}")

        except subprocess.CalledProcessError as e:
            print(f"FAIL: {table}:\n     {e}")
        except Exception as e:
            print(f"Unexpected error occurred for {table}: {e}")

    # Copy each table's data to a CSV file in the postgres_data directory
    # for table in tables:
    #     csv_file = os.path.join(data_dir, f"{table}.csv")
    #     print(f"Fetching data for table {table} ...")

    #     # Fetch all columns of the table
    #     columns = get_table_columns(hostname, database, username, table)

    #     # Check if we need to exclude any columns for this table
    #     if table in exclude_columns:
    #         excluded_columns = exclude_columns[table]
    #         included_columns = [col for col in columns if col not in excluded_columns]
    #     else:
    #         included_columns = columns

    #     # Build the query with selected columns
    #     column_str = ', '.join(included_columns)
    #     query = f"SELECT {column_str} FROM {table}"

    #     # Properly enclose the query in parentheses for the COPY command
    #     copy_command = f"COPY ({query}) TO STDOUT WITH DELIMITER ',' CSV HEADER;"

    #     command = ["psql", "-h", hostname, "-d", database, "-U", username, "-c", copy_command]

    #     try:
    #         with open(csv_file, 'w') as f:
    #             result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE)
    #             if result.returncode != 0:
    #                 print(f"Error occurred while copying data for {table}: {result.stderr.decode()}")
    #                 sys.exit(result.returncode)
    #     except subprocess.CalledProcessError:
    #         print(f"Failed to fetch data for table {table}")
    #         sys.exit(4)

def main(options):
    """
    1. get tables
    2. COPY TO for each table
    """
    host = options.get('server')
    database = options.get('database')
    username = options.get('username')
    password = options.get('password')
    output_path = options.get('output')

    # Store password in environment variables so that psql doesn't ask on each query
    os.environ["PGPASSWORD"] = password
    
    if not os.path.exists(os.path.join(output_path, data_dir)):
        os.makedirs(os.path.join(output_path, data_dir))
    print(f"Data will be stored in {data_dir}")

    # Fetch list of tables
    tables = fetch_tables(host, database, username)

    # Copy data to csv
    copy_data(host, database, username, tables)

    # delete password
    del os.environ["PGPASSWORD"]

if __name__ == "__main__":

    options = {
        'host': 'localhost',
        'database': 'joelbieber_backup',
        'username': 'postgres',
        'password': 'SAsuper',
        'output': r'D:\Needles-JoelBieber'
    }

    # if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
    #     print("usage: python script.py [DB_NAME]")
    #     print("default DB_NAME is your username")
    #     sys.exit()

    # db_name = sys.argv[1] if len(sys.argv) > 1 else None
    main(options)
