# External
import os
import argparse
from importlib.resources import files
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

# Module imports
# from sql_runner import sql_runner
from sa_conversion_utils.db_utils import restore_db, backup_db, create_db
from sa_conversion_utils.run import exec_conv
from sa_conversion_utils.mapping import generate_mapping
from sa_conversion_utils.csv_to_sql import main as convert_csv_to_sql
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
    # print(args)
    # if not args.all and not args.series:
    #     print("Error: The 'run' command requires the 'series' argument unless '--all' is specified.")
    #     return
    # print(args.subcommand, args.func.__name__)
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        # 'sequence': args.seq,
        'series': args.series,
        'backup': args.backup,
        'run_all': args.all,
        'init': args.init,
        'map': args.map,
        'post': args.post,
        'skip': args.skip
    }
    exec_conv(options)

    # Anticipate user needs.
    # If the --backup flag was not used, provide a second chance to perform a backup.
    # if not args.backup:
    #     if Confirm.ask("The migration has been completed. Would you like to perform a backup now?"):
    #         backup_options = {
    #             'server': args.server or SERVER,
    #             'database': args.database or SA_DB,
    #             'directory': args.dir or os.path.join(os.getcwd(),'backups'),
    #             'message': 'Backup after migration'
    #         }
    #         backup_db(backup_options)

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

def convert_csv_to_sql(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database,
        'input_path': args.input,
        'table': args.table,
        'chunk_size': args.chunk
    }
    convert_csv_to_sql(options)

def convert_psql_to_csv(args):  
    options = {
        'server': args.server,
        'database': args.database,
        'username': args.username,
        'password': args.password,
        'output': args.output
    }
    convert_psql_to_csv(options)

# Initialize the command help dictionary
command_help = {
    'db': {},
    'migrate': {}
}

def populate_command_help(parser, parent_command):
    """Populate command_help dictionary based on the parser."""
    for subcommand, details in parser._subparsers._actions[0].choices.items():
        description = details.description if details.description else "No description provided"
        flags = ', '.join([f'-{arg.dest}' for arg in details._actions if arg.dest != 'help'])
        command_help[parent_command][subcommand] = {
            'description': description,
            'flags': flags
        }

def print_rich_help(subcommands, title):
    """Prints help using a rich table."""
    table = Table(title=title, title_style="bold cyan")
    table.add_column("Command", style="magenta", no_wrap=True)
    table.add_column("Description", style="green")
    
    # Add subcommands and descriptions to the table
    for subcommand, description in subcommands.items():
        table.add_row(subcommand, description)
    
    # Print the table using Rich console
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description='SmartAdvocate Data Conversion CLI.')
    subparsers = parser.add_subparsers(
        title="operations",
        dest='subcommand'
        # help='sub-command help'
    )

    # Command: backup
    backup_parser = subparsers.add_parser('backup', help='Backup database')
    backup_parser.add_argument('-s', '--server', help='Server name. Defaults to SERVER from .env', metavar='')
    backup_parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env', metavar='')
    backup_parser.add_argument('-o', '--output', help='Output directory. Defaults to /backups', metavar='')
    backup_parser.add_argument('-m', '--message', help='Optional message to include in the filename', metavar='')
    backup_parser.set_defaults(func=backup)

    # Command: restore
    restore_parser = subparsers.add_parser('restore', help='Restore database')
    restore_parser.add_argument('-s', '--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    restore_parser.add_argument('-d', '--database', help='Name of database to restore. If not supplied, defaults to TARGET_DB from .env.', metavar='')
    restore_parser.add_argument('-v', '--virgin', action='store_true', help='Restore the specified databse to a virgin SA database.')
    restore_parser.set_defaults(func=restore)

    # Command: map
    mapping_parser = subparsers.add_parser('map', help='Generate Excel mapping template.')
    mapping_parser.add_argument('system', nargs='?',help='SQL Script sequence to execute.', choices=['needles'], type=str)
    mapping_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    mapping_parser.add_argument('-d', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    mapping_parser.set_defaults(func=map)

    # Command: run
    run_parser = subparsers.add_parser('run', help='Run SQL scripts')
    run_parser.add_argument('-se', '--series', type=int, choices=range(0,10), help='Select the script series to execute.')
    run_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    run_parser.add_argument('-d', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    run_parser.add_argument('-bu', '--backup', action='store_true', help='Backup SA database after script execution.')
    run_parser.add_argument('-a', '--all', action='store_true', help='Run all sql scripts.')
    run_parser.add_argument('-i', '--init', action='store_true', help='Run SQL scripts in the "init" directory.')
    run_parser.add_argument('-m', '--map', action='store_true', help='Run SQL scripts in the "map" directory.')
    run_parser.add_argument('-p', '--post', action='store_true', help='Run SQL scripts in the "post" directory.')
    run_parser.add_argument('--skip', action='store_true', help='Enable skipping scripts with "skip" in the filename.')
    run_parser.set_defaults(func=run)
    
    # Command: encrypt
    encrypt_parser = subparsers.add_parser('encrypt', help='Run SSN Encryption')
    encrypt_parser.set_defaults(func=encrypt)

    # Command: convert
    convert_parser = subparsers.add_parser("convert", help="Convert data from one type to another, such as .csv to sql")
    convert_subparsers = convert_parser.add_subparsers(title="Convert Variants", dest="convert_variant")
    # convert_parser = subparsers.add_parser('convert', help='convert csv to sql')
    # convert_parser.add_argument('-s','--server', help='Server name. Defaults to SERVER from .env.', metavar='')
    # convert_parser.add_argument('-d', '--database', help='Database to execute against. Defaults to SA_DB from .env.', metavar='')
    # convert_parser.add_argument('-t', '--table', help='Table name. If ommited, tables will use file names.')
    # convert_parser.add_argument('-i', '--input', help='Input path. Supports file or directory.')
    # convert_parser.add_argument('-c', '--chunk', type=int, help='Chunk size used in processing .csv files. Default = 2,000', default=2000)
    # convert_parser.set_defaults(func=convert_csv_to_sql)

    # Subcommand: convert csv-to-sql
    csv_to_sql_parser = convert_subparsers.add_parser("csv-to-sql", help="Convert CSV to SQL")
    csv_to_sql_parser.add_argument('-s','--server', help='Server name. Defaults to SERVER from .env.', metavar='')
    csv_to_sql_parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env.', metavar='')
    csv_to_sql_parser.add_argument("-i", "--input", required=True, help="Path to CSV file or directory")
    # csv_to_sql_parser.add_argument("-t", "--table", help="Table name in the database")
    csv_to_sql_parser.add_argument("-c", "--chunk", type=int, default=2000, help="Chunk (row) size for processing. Defaults to 2,000 rows at a time")
    csv_to_sql_parser.set_defaults(func=convert_csv_to_sql)

    # Subcommand: convert psql-to-csv
    psql_to_csv_parser = convert_subparsers.add_parser("psql-to-csv", help="Convert PostgreSQL to CSV")
    
    psql_to_csv_parser.add_argument("-s", "--server", required=True, help="PostgreSQL hostname")
    psql_to_csv_parser.add_argument("-d", "--database", required=True, help="PostgreSQL database name")
    psql_to_csv_parser.add_argument("-u", "--username", required=True, help="PostgreSQL username")
    psql_to_csv_parser.add_argument("-p", "--password", required=True, help="PostgreSQL password")
    psql_to_csv_parser.add_argument("-o", "--output", required=True, help="Output path for .csv files")
    psql_to_csv_parser.set_defaults(func=convert_psql_to_csv)

    args = parser.parse_args()
    if 'func' not in args:
        parser.print_help()
    else:
        args.func(args)

    # Get the invoked subcommand's title
    # if args.subcommand:
    #     print(f'Invoked subcommand: {args.subcommand}')
    # else:
    #     print('No subcommand invoked')

    # if 'func' not in args:
    #     # parser.print_help()
    #      print_rich_help({
    #         "db": "Database operations",
    #         "migrate": "Migration operations"
    #     }, "SmartAdvocate Migration CLI")
    # else:
    #     # args.func(args)
    #     execute_with_logging(args.func, args)


    # if 'func' not in args:
    #     parser.print_help()
    # else:
    #     if args.func == exec and args.all:
    #         # If --all is used, sequence is not required
    #         args.seq = None
    #     elif args.func == exec and args.seq is None:
    #         # If sequence is not provided and --all is not used
    #         parser.error("The 'exec' command requires the 'seq' argument unless '--all' is specified.")

if __name__ == "__main__":
    main()
