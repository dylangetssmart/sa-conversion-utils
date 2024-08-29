# External
import os
import argparse
import re
from importlib.resources import files
from dotenv import load_dotenv

# Import modules
from .database.sql_runner import sql_runner
from .database.db_utils import restore_db, backup_db, create_db
from .conversion.exec_conv import exec_conv
from .conversion.mapping import generate_mapping
from .conversion.initialize import initialize

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
        'message': args.m
    }
    backup_db(options)

def exec(args):
    options = {
        'server': args.server or SERVER,
        'database': args.db or SA_DB,
        'sequence': args.seq,
        'backup': args.bu,
        'run_all': args.all
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

def encrypt_ssn(args):
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

def main():
    # Main entry point for the CLI.
    parser = argparse.ArgumentParser(description='SmartAdvocate Conversion CLI.')
    subparsers = parser.add_subparsers(
        title="conversion operations",
        # help='sub-command help'
    )

    # Backup DB
    backup_parser = subparsers.add_parser('backup', help='Create database backups.')
    backup_parser.add_argument('-m', '--message', help='Message to stamp on the .bak file.')
    backup_parser.add_argument('-dir', help='Directory to save the backup in. If not supplied, defaults to /backups.', metavar='')
    backup_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    backup_parser.add_argument('-db', help='Name of database to backup. If not supplied, defaults to SA_DB from .env.', metavar='')
    backup_parser.set_defaults(func=backup)

    # Execute conversion
    exec_parser = subparsers.add_parser('exec', help='Run SQL scripts.')
    exec_parser.add_argument('seq', nargs='?',help='SQL Script sequence to execute.', choices=range(0,10), type=int)
    # exec_parser.add_argument('seq', help='Script sequence to execute.', choices=['0','1','2','3','4','5','a','p','q'])
    exec_parser.add_argument('-bu', action='store_true', help='Backup SA database after script execution.')
    exec_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    exec_parser.add_argument('-db', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    exec_parser.add_argument('-a', '--all', action='store_true', help='Execute all sql scripts.')
    exec_parser.set_defaults(func=exec)

    # Restore DB
    restore_db_parser = subparsers.add_parser('restore', help='Restore a database from a backup file.')
    restore_db_parser.add_argument('-s', '--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    restore_db_parser.add_argument('-n', '--name', help='Name of database to restore. If not supplied, defaults to TARGET_DB from .env.', metavar='')
    restore_db_parser.add_argument('-v', '--virgin', action='store_true', help='Restore the specified databse to a virgin SA database.')
    restore_db_parser.set_defaults(func=restore)

    # Initiliaze Needles DB
    # init_parser = subparsers.add_parser('init', help='Initialize Needles database with functions and indexes.')
    # init_parser.add_argument('-srv', help='Server name.', metavar='')
    # init_parser.add_argument('-db', help='Needles database to initialize.', metavar='')
    # init_parser.set_defaults(func=init)

    # Generate Mapping Template
    mapping_parser = subparsers.add_parser('map', help='Generate Excel mapping template.')
    mapping_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    mapping_parser.add_argument('-db', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    mapping_parser.set_defaults(func=map)

    # Create DB
    create_db_parser = subparsers.add_parser('create', help='Create a SQL Server database.')
    create_db_parser.add_argument('-s', '--server', help='Server name.', metavar='')
    create_db_parser.add_argument('name', help='Database name.', metavar='name')
    create_db_parser.set_defaults(func=create)

    # Read 
    read_parser = subparsers.add_parser('read', help='read sql scripts for testing.')
    read_parser.set_defaults(func=read)

    # Add a subparser for SSN Encryption
    ssn_encrypt_parser = subparsers.add_parser('encrypt_ssn', help='Run SSN Encryption utility.')
    ssn_encrypt_parser.set_defaults(func=encrypt_ssn)

    args = parser.parse_args()

    if 'func' not in args:
        parser.print_help()
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
