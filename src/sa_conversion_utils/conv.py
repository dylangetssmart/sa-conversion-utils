# External
import os
import argparse
import re
from importlib.resources import files
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Import modules
from .database.sql_runner import sql_runner
from .database.db_utils import restore_db, backup_db, create_db
from .migrate.run import exec_conv
from .migrate.mapping import generate_mapping
from .migrate.initialize import initialize
from .migrate.convert import main as convert

# Create a Rich console object
console = Console()

# Constants
BASE_DIR = os.path.dirname(__file__)

# Load environment variables from the current working directory
load_dotenv(os.path.join(os.getcwd(), '.env'))

# Debugging: Print environment variables to check if they're loaded
# for key, value in os.environ.items():
#     if key in ['SERVER', 'SOURCE_DB', 'TARGET_DB']:
#         print(f'{key}: {value}')

# Load environment variables
SERVER = os.getenv('SERVER')
SOURCE_DB = os.getenv('SOURCE_DB')
SA_DB = os.getenv('TARGET_DB')

def read(args):
    print(SERVER, SOURCE_DB, SA_DB)
    # pkg = files('smart_conversion')
    # pkg_data_file = pkg / ''
    # print(files('sql.conv'))
    # with importlib.resources.files(__package__).joinpath('sql/conv') as sql_dir:
    #     for file in os.listdir(sql_dir):
    #         if file.endswith('.sql'):
    #             print(file)

def map(args):
    options = {
        'server': args.server or SERVER,
        'database': args.db or SOURCE_DB
    }
    generate_mapping(options)

def backup(args):
    options = {
        'server': args.server or SERVER,
        'database': args.db or SA_DB,
        'directory': args.dir or os.path.join(os.getcwd(),'backups'),
        'message': args.message
    }
    backup_db(options)

def run(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        # 'sequence': args.seq,
        'series': args.series,
        'backup': args.backup,
        'run_all': args.all,
        'init': args.init,
        'map': args.map
    }
    exec_conv(options)

def restore(args):
    options = {
        'server': args.server or SERVER,
        'name': args.name or SA_DB,
        'virgin': args.virgin
    }
    restore_db(options)

# def init(args):
#     options = {
#         'server': args.srv or SERVER,
#         'database': args.db or SA_DB,
#         'system': args.system
#     }
#     initialize(options)

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

def convert2(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database,
        'input_path': args.input,
        'table': args.table
    }
    convert(options)

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
    # Main entry point for the CLI.
    parser = argparse.ArgumentParser(description='SmartAdvocate Data Migration CLI.')
    subparsers = parser.add_subparsers(
        title="operations",
        # help='sub-command help'
    )

    """ ##############################################################################################################
    # Database Operations
        1. connect
        2. restore
        3. backup
        4. create (?)
    """ ##############################################################################################################

    # Parent command "db"
    db_parser = subparsers.add_parser('db', help="Database operations")
    db_subparsers = db_parser.add_subparsers(title="Database commands")

    # If no subcommand is provided for 'db', print rich help
    db_parser.set_defaults(func=lambda args: print_rich_help({
        "connect": "Connect to the database",
        "test": "Test database connection",
        "backup": "Create database backups",
        "restore": "Restore a database from a backup file"
    }, "Database Operations"))

    # subcommand > db connect
    connect_parser = db_subparsers.add_parser('connect', help='Connect to a database')
    # connect_parser

    # subcommand > db backup
    backup_parser = db_subparsers.add_parser('backup', help='Create database backups.')
    backup_parser.add_argument('-m', '--message', help='Message to stamp on the .bak file.')
    backup_parser.add_argument('-dir', help='Directory to save the backup in. If not supplied, defaults to /backups.', metavar='')
    backup_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    backup_parser.add_argument('-db', help='Name of database to backup. If not supplied, defaults to SA_DB from .env.', metavar='')
    backup_parser.set_defaults(func=backup)

    # subcommand > db restore
    restore_db_parser = db_subparsers.add_parser('restore', help='Restore a database from a backup file.')
    restore_db_parser.add_argument('-s', '--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    restore_db_parser.add_argument('-n', '--name', help='Name of database to restore. If not supplied, defaults to TARGET_DB from .env.', metavar='')
    restore_db_parser.add_argument('-v', '--virgin', action='store_true', help='Restore the specified databse to a virgin SA database.')
    restore_db_parser.set_defaults(func=restore)

    # Create DB
    # create_db_parser = subparsers.add_parser('create', help='Create a SQL Server database.')
    # create_db_parser.add_argument('-s', '--server', help='Server name.', metavar='')
    # create_db_parser.add_argument('name', help='Database name.', metavar='name')
    # create_db_parser.set_defaults(func=create)

    """ ##############################################################################################################
    Migration Operations 
        1. init
        2. map
        3. run
        4. encrypt
        5. convert
    """ ##############################################################################################################

    # Parent command "migrate"
    migrate_parser = subparsers.add_parser('migrate', help='Migration operations')
    migrate_subparsers = migrate_parser.add_subparsers(title='migrate commands')

    # If no subcommand is provided for 'migrate', print rich help
    migrate_parser.set_defaults(func=lambda args: print_rich_help({
        "init": "Connect to the database",
        "map": "Test database connection",
        "run": "Create database backups",
        "encrypt": "Restore a database from a backup file",
        "convert": "testing"
    }, "Database Operations"))

    # subcommand > init
    # init_parser = subparsers.add_parser('init', help='Initialize Needles database with functions and indexes.')
    # init_parser.add_argument('-srv', help='Server name.', metavar='')
    # init_parser.add_argument('-db', help='Needles database to initialize.', metavar='')
    # init_parser.set_defaults(func=init)
    
    # subcommand > map
    mapping_parser = migrate_subparsers.add_parser('map', help='Generate Excel mapping template.')
    mapping_parser.add_argument('system', nargs='?',help='SQL Script sequence to execute.', choices=['needles'], type=str)
    mapping_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    mapping_parser.add_argument('-db', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    mapping_parser.set_defaults(func=map)

    # subcommand > run
    run_parser = migrate_subparsers.add_parser('run', help='Run SQL scripts.')
    # run_parser.add_argument('seq', nargs='?',help='SQL Script sequence to execute.', choices=range(0,10), type=int)
    # run_parser.add_argument('seq', help='Script sequence to execute.', choices=['0','1','2','3','4','5','a','p','q'])
    run_parser.add_argument('-bu', '--backup', action='store_true', help='Backup SA database after script execution.')
    run_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    run_parser.add_argument('-db', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    run_parser.add_argument('-a', '--all', action='store_true', help='Run all sql scripts.')
    run_parser.add_argument('-i', '--init', action='store_true', help='Run SQL scripts in the "init" directory.')
    run_parser.add_argument('-m', '--map', action='store_true', help='Run SQL scripts in the "mapping" directory.')
    run_parser.add_argument('-se', '--series', type=int, choices=range(0,10), help='Run SQL scripts in the "mapping" directory.')
    run_parser.set_defaults(func=run)
    
    # subcommand > encrypt
    encrypt_parser = migrate_subparsers.add_parser('encrypt', help='Run SSN Encryption utility.')
    encrypt_parser.set_defaults(func=encrypt)

    # Migrate subcommand > convert
    convert_parser = migrate_subparsers.add_parser('convert', help='convert csv to sql')
    convert_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    convert_parser.add_argument('-d', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    convert_parser.add_argument('-t', '--table', help='Table name. If input is a directory, tables will be named after each .csv file imported.')
    convert_parser.add_argument('-i', '--input', help='Input path - file or directory to convert.')
    convert_parser.set_defaults(func=convert2)


    # Read 
    # read_parser = subparsers.add_parser('read', help='read sql scripts for testing.')
    # read_parser.set_defaults(func=read)



    args = parser.parse_args()

    if 'func' not in args:
        # parser.print_help()
         print_rich_help({
            "db": "Database operations",
            "migrate": "Migration operations"
        }, "SmartAdvocate Migration CLI")
    else:
        args.func(args)
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
