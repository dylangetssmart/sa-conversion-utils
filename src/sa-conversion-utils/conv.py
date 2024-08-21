# External
import os
import argparse
import re
# import importlib.resources
from importlib.resources import files
from dotenv import load_dotenv

# Lib
from smart_conversion.lib.exec_conv import exec_conv
from smart_conversion.lib.sql_runner import sql_runner
from smart_conversion.lib.mapping import generate_mapping
from smart_conversion.lib.db_utils import restore_db, backup_db, create_db

# Load environment variables
load_dotenv()
SERVER = os.getenv('SERVER')
SOURCE_DB = os.getenv('SOURCE_DB')
SA_DB = os.getenv('TARGET_DB')

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# https://jwodder.github.io/kbits/posts/pypkg-data/

def read(args):
    print('read')
    pkg = files('smart_conversion')
    pkg_data_file = pkg / ''
    # print(files('sql.conv'))
    # with importlib.resources.files(__package__).joinpath('sql/conv') as sql_dir:
    #     for file in os.listdir(sql_dir):
    #         if file.endswith('.sql'):
    #             print(file)

def map(args):
    options = {
        'server': args.srv or SERVER,
        'database': args.db or SA_DB
    }
    generate_mapping(options)

def backup(args):
    options = {
        'server': args.srv or SERVER,
        'database': args.db or SA_DB,
        'directory': args.dir or os.path.join(os.getcwd(),'backups'),
        'sequence': args.seq
    }
    backup_db(options)

def exec(args):
    options = {
        'server': args.srv or SERVER,
        'database': args.db or SA_DB,
        'sequence': args.seq,
        'backup': args.bu,
        'run_all': args.all
    }
    exec_conv(options)

def restore(args):
    options = {
        'server': args.srv or SERVER,
        'database': args.db or SA_DB,
        'virgin': args.virgin
    }
    restore_db(options)

def init(args):
    # options = {
    #     'server': args.srv or SERVER,
    #     'database': args.db or SA_DB,
    #     'system': args.system
    # }

    # initialize(options)
    server = args.srv or SERVER
    database = args.db or SOURCE_DB
    init_dir = os.path.join(BASE_DIR, 'sql-scripts', 'initialize-needles')
    sql_pattern = re.compile(r'^.*\.sql$', re.I)

    print(f'Initializing Needles database {server}.{database}...')
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
                # print(f'Executing script: {sql_file_path}')
                sql_runner(sql_file_path, server, database)
    except Exception as e:
        print(f'Error reading directory {init_dir}\n{str(e)}')

def create(args):
    options = {
        'server': args.server or SERVER,
        'name': args.name
    }
    create_db(options)

def main():
    # Main entry point for the CLI.
    parser = argparse.ArgumentParser(description='Needles Conversion CLI.')
    subparsers = parser.add_subparsers(
        title="conversion operations",
        # help='sub-command help'
    )

    # Backup DB
    backup_parser = subparsers.add_parser('backup', help='Create database backups.')
    backup_parser.add_argument('seq', help='Sequence to stamp on .bak file.')
    backup_parser.add_argument('-dir', help='Backup directory.', metavar='')
    backup_parser.add_argument('-srv', help='Server name.', metavar='')
    backup_parser.add_argument('-db', help='Database to backup.', metavar='')
    backup_parser.set_defaults(func=backup)

    # Execute conversion
    exec_parser = subparsers.add_parser('exec', help='Run SQL scripts.')
    exec_parser.add_argument('seq', nargs='?',help='SQL Script sequence to execute.', choices=range(0,10), type=int)
    # exec_parser.add_argument('seq', help='Script sequence to execute.', choices=['0','1','2','3','4','5','a','p','q'])
    exec_parser.add_argument('-bu', action='store_true', help='Backup SA database after script execution.')
    exec_parser.add_argument('-srv', help='Server name.', metavar='')
    exec_parser.add_argument('-db', help='Database to execute against.', metavar='')
    exec_parser.add_argument('-a', '--all', action='store_true', help='Execute all sql scripts.')
    exec_parser.set_defaults(func=exec)

    # Restore DB
    restore_db_parser = subparsers.add_parser('restore', help='Restore a database from a backup file.')
    restore_db_parser.add_argument('-srv', help='Server name.', metavar='')
    restore_db_parser.add_argument('-db', help='Database to restore. Defaults to SA_DB', metavar='')
    restore_db_parser.add_argument('-v', '--virgin', action='store_true', help='Restore to virgin state.')
    restore_db_parser.set_defaults(func=restore)

    # Initiliaze Needles DB
    initialize_needles_parser = subparsers.add_parser('init', help='Initialize Needles database with functions and indexes.')
    initialize_needles_parser.add_argument('-srv', help='Server name.', metavar='')
    initialize_needles_parser.add_argument('-db', help='Needles database to initialize.', metavar='')
    initialize_needles_parser.set_defaults(func=init)

    # Generate Mapping Template
    mapping_parser = subparsers.add_parser('map', help='Generate Excel mapping template.')
    mapping_parser.set_defaults(func=map)

    # Create DB
    create_db_parser = subparsers.add_parser('create', help='Create a SQL Server database.')
    create_db_parser.add_argument('-s', '--server', help='Server name.', metavar='')
    create_db_parser.add_argument('name', help='Database name.', metavar='name')
    create_db_parser.set_defaults(func=create)

    # Read 
    read_parser = subparsers.add_parser('read', help='read sql scripts for testing.')
    read_parser.set_defaults(func=read)

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
