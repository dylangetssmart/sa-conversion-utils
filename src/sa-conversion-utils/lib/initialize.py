"""

# Create blank db
# Restore virgin SA db
# Execute system appropriate initialization scripts

Needles
    1. 

Litify
    1. import:  csv_to_sql.py

"""

import os
import re
from lib.sql_runner import sql_runner
# from lib.create_db import create_database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def initialize(options):
    server = options.get('server')
    database = options.get('database')
    system = options.get('system')

    # Restore virgin SA


    if system == 'needles':
        """
        1. 
        2. 
        3. 
        """
        init_dir = os.path.join(BASE_DIR, 'sql-scripts', 'initialize-needles')
        sql_pattern = re.compile(r'^.*\.sql$', re.I)
        try:
            # List all files in the initialization directory
            all_files = os.listdir(init_dir)
            # Filter files that match the SQL pattern
            files = [file for file in all_files if sql_pattern.match(file)]

            if not files:
                print(f'No scripts found in {init_dir}.')
            else:
                for file in files:
                    sql_file_path = os.path.join(init_dir, file)
                    sql_runner(sql_file_path, server, database)
        except Exception as e:
            print(f'Error reading directory {init_dir}\n{str(e)}')
    elif system == 'another_system':  # Add more conditions for other system types
        # Perform different initialization tasks for other systems
        pass
    else:
        print(f'Unsupported system type: {system}')