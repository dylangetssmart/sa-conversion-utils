# External
import sys
import os
import argparse
from importlib.resources import files
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt

# Module imports
# from sql_runner import sql_runner
from sa_conversion_utils.db_utils import restore_db, backup_db, create_db
from sa_conversion_utils.run import exec_conv
from sa_conversion_utils.mapping import generate_mapping
from sa_conversion_utils.import_flat_file import main as import_flat_file
from sa_conversion_utils.psql_to_csv import main as convert_psql_to_csv
from .utilities.migration_logger import log_migration_step

console = Console()

# Load environment variables
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(os.getcwd(), '.env'))
SERVER = os.getenv('SERVER')
SOURCE_DB = os.getenv('SOURCE_DB')
SA_DB = os.getenv('TARGET_DB')

# def execute_with_logging(func, args):
#     start_time = datetime.now()
#     output_errors = None
#     sub_command = args.subcommand
#     function_name = args.func.__name__
#     database = getattr(args, 'database', None) or SA_DB if hasattr(args, 'database') else None
#     # print(args.series)

#     # Don't log when a parent command is run by itself (shows help)
#     if function_name == '<lambda>':
#         return

#     def get_relevant_args(sub_command):
#         match sub_command:
#             case 'run':
#                 return args.series
#             case 'backup':
#                 return args.message
#             case _:
#                 return ''

#     try:
#         func(args)
#         status = "Completed"
#     except Exception as e:
#         status = "Failed"
#         output_errors = str(e)
    
#     end_time = datetime.now()
#     log_migration_step(
#         database,
#         sub_command,
#         function_name,
#         get_relevant_args(sub_command),
#         status,
#         start_time,
#         end_time,
#         output_errors
#         )

def map(args):
    options = {
        'server': args.server or SERVER,
        'database': args.db or SOURCE_DB
    }
    generate_mapping(options)

def backup(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        'output': args.output or os.path.join(os.getcwd(),'backups'),
        'message': args.message
    }
    backup_db(options)

def run(args):
    # Prompt.ask("Enter script series to run", choices=['conv', 'map','init','utilities'])
    # print(args)
    # if not args.all and not args.series:
    #     print("Error: The 'run' command requires the 'series' argument unless '--all' is specified.")
    #     return
    # print(args.subcommand, args.func.__name__)
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        'phase': args.phase,
        'group': args.group,
        'backup': args.backup,
        'skip': args.skip,
        'debug': args.debug
        # 'sequence': args.seq,
        # 'series': args.series,
        # 'run_all': args.all,
        # 'init': args.init,
        # 'map': args.map,
        # 'post': args.post,
    }
    exec_conv(options)

def restore(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        'virgin': args.virgin
    }
    restore_db(options)

def create(args):
    options = {
        'server': args.server or SERVER,
        'name': args.name
    }
    create_db(options)

def encrypt(args):
    exe_path = r"C:\LocalConv\_utils\SSNEncryption\SSNEncryption.exe"
    try:
        # Execute the SSNEncryption.exe
        result = os.system(exe_path)
        
        if result == 0:
            print("SSN encryption completed successfully.")
        else:
            print(f"SSN encryption failed with exit code {result}.")
    except Exception as e:
        print(f"An error occurred while running SSN encryption: {str(e)}")

def handle_import_flat_file(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        'input_path': args.input,
        # 'table': args.table,
        'chunk_size': args.chunk
    }
    import_flat_file(options)

def handle_convert_psql_to_csv(args):  
    options = {
        'server': args.server,
        'database': args.database,
        'username': args.username,
        'password': args.password,
        'output': args.output
    }
    convert_psql_to_csv(options)

def validate_args(args):
    # Make `group` required only if `phase` is 'conv'
    if args.phase == 'conv' and not args.group:
        print("error: the following argument is required for 'conv' phase: group")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='SmartAdvocate Data Conversion CLI.')
    subparsers = parser.add_subparsers(
        title="operations",
        dest='subcommand'
        # help='sub-command help'
    )

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: backup
    backup_parser = subparsers.add_parser('backup', help='Backup database')
    backup_parser.add_argument('-s', '--server', help='Server name. Defaults to SERVER from .env', metavar='')
    backup_parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env', metavar='')
    backup_parser.add_argument('-o', '--output', help='Output directory. Defaults to /backups', metavar='')
    backup_parser.add_argument('-m', '--message', help='Optional message to include in the filename', metavar='')
    backup_parser.set_defaults(func=backup)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: restore
    restore_parser = subparsers.add_parser('restore', help='Restore database')
    restore_parser.add_argument('-s', '--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    restore_parser.add_argument('-d', '--database', help='Name of database to restore. If not supplied, defaults to TARGET_DB from .env.', metavar='')
    restore_parser.add_argument('-v', '--virgin', action='store_true', help='Restore the specified databse to a virgin SA database.')
    restore_parser.set_defaults(func=restore)

    # --------------------------------------------------------------------------------------------------------------------------------------------- 
    # Command: map
    mapping_parser = subparsers.add_parser('map', help='Generate Excel mapping template.')
    mapping_parser.add_argument('system', nargs='?',help='SQL Script sequence to execute.', choices=['needles'], type=str)
    mapping_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    mapping_parser.add_argument('-d', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    mapping_parser.set_defaults(func=map)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: run
    run_parser = subparsers.add_parser('run', help='Run SQL scripts')
    # Arguments ---------------
    run_parser.add_argument(
        'phase',
        choices=['map', 'conv', 'post'],
        metavar='phase',
        help='The phase of SQL scripts to run: {map, conv, post}'
    )
    run_parser.add_argument(
        'group',
        nargs='?',
        choices=['config', 'contact', 'case', 'udf', 'misc', 'intake'],
        metavar='group',
        help='The specific group of scripts to run (required if phase = conv): {config, contact, case, udf, misc, intake}'
    )
    # run_parser.add_argument('-se', '--series', type=int, choices=range(0,10), help='Select the script series to execute.')
    # Flags -------------------
    run_parser.add_argument('-s','--server', help='SQL Server. If omitted, defaults to SERVER from .env', metavar='')
    run_parser.add_argument('-d', '--database', help='Database. If omitted, defaults to SA_DB from .env', metavar='')
    run_parser.add_argument('-bu', '--backup', action='store_true', help='Backup database after script execution')
    run_parser.add_argument('--skip', action='store_true', help='Enable skipping scripts with "skip" in the filename')
    run_parser.add_argument('--debug', action='store_true', help='Pauses execution after each script')
    run_parser.add_argument('--all', action='store_true', help='Run all groups in the "conv" phase')
    # run_parser.add_argument('-i', '--init', action='store_true', help='Run SQL scripts in the "init" directory.')
    # run_parser.add_argument('-m', '--map', action='store_true', help='Run SQL scripts in the "map" directory.')
    # run_parser.add_argument('-p', '--post', action='store_true', help='Run SQL scripts in the "post" directory.')
    run_parser.set_defaults(func=run)
    
    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: encrypt
    encrypt_parser = subparsers.add_parser('encrypt', help='Run SSN Encryption')
    encrypt_parser.set_defaults(func=encrypt)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: import
    import_parser = subparsers.add_parser("import", help="Import data into SQL")
    import_subparsers = import_parser.add_subparsers(title="Convert Variants", dest="convert_variant")

    # Subcommand: flat file
    flat_file_parser = import_subparsers.add_parser("flat-file", help="Import data from flat files to SQL")
    flat_file_parser.add_argument('-s','--server', help='Server name. Defaults to SERVER from .env.', metavar='')
    flat_file_parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env.', metavar='')
    flat_file_parser.add_argument("-i", "--input", required=True, help="Path to CSV file or directory")
    # flat_file_parser.add_argument("-t", "--table", help="Table name in the database")
    flat_file_parser.add_argument("-c", "--chunk", type=int, default=2000, help="Chunk (row) size for processing. Defaults to 2,000 rows at a time")
    flat_file_parser.set_defaults(func=handle_import_flat_file)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: export
    export_parser = subparsers.add_parser("export", help="Convert data from one type to another, such as .csv to sql")
    export_subparsers = export_parser.add_subparsers(title="Convert Variants", dest="convert_variant")

    # Subcommand: convert psql-to-csv
    psql_to_csv_parser = import_subparsers.add_parser("psql-csv", help="Convert PostgreSQL to CSV")
    psql_to_csv_parser.add_argument("-s", "--server", required=True, help="PostgreSQL hostname")
    psql_to_csv_parser.add_argument("-d", "--database", required=True, help="PostgreSQL database name")
    psql_to_csv_parser.add_argument("-u", "--username", required=True, help="PostgreSQL username")
    psql_to_csv_parser.add_argument("-p", "--password", required=True, help="PostgreSQL password")
    psql_to_csv_parser.add_argument("-o", "--output", required=True, help="Output path for .csv files")
    psql_to_csv_parser.set_defaults(func=handle_convert_psql_to_csv)

    args = parser.parse_args()

    # Validate arguments
    if args.subcommand == 'run':
        validate_args(args)

    if 'func' not in args:
        parser.print_help()
    else:
        args.func(args)

if __name__ == "__main__":
    main()
