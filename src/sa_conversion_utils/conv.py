# External
import os
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm

# Module imports
from sa_conversion_utils.utilities.setup_logger import setup_logger
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.database.restore import restore_db
from sa_conversion_utils.run.run import run
from sa_conversion_utils.map.map import map as generate_mapping
from sa_conversion_utils.convert.flat_to_sql import main as import_flat_file
from sa_conversion_utils.convert.psql_to_csv import main as convert_psql_to_csv

logger = setup_logger(__name__, log_file="sami.log")
console = Console()

# Load environment variables
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(os.getcwd(), '.env'))
SERVER = os.getenv('SERVER')
SOURCE_DB = os.getenv('SOURCE_DB')
SA_DB = os.getenv('TARGET_DB')
SQL_DIR = os.getenv('SQL_DIR')

def map(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database or SOURCE_DB,
         'input': args.input
    }
    generate_mapping(options)    

def backup(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        'output': args.output or os.path.join(os.getcwd(),'_backups'),
        'message': args.message
        # 'phase': args.phase,
        # 'group': args.group
    }
    backup_db(options)

"""
##############################################################################
run
"""

# def run_conv(args):
#     if not args.type:
#         args.type = Prompt.ask(
#             "[bold green]Select script group[/bold green]",
#             choices=["init", "contact", "case", "intake", "misc", "udf", "all", "vanilla", "exit"],
#             default="contact"
#         )

#     match args.type:
#         case 'exit':
#             console.print("[bold red]Exiting[/bold red]")
#             return
#         case 'all':
#             args.all = True
#             args.vanilla = False
#             # input_path = f"sql\\conv\\"
#             input_path = os.path.join(SQL_DIR, 'conv')
#             if Confirm.ask("[bold green]Run all conversion scripts[/bold green]"):
#                 run_common(args, input_path, is_all = True)
#         case 'vanilla':
#             args.vanilla = True
#             args.all = True
#             # input_path = f"sql\\conv\\"
#             input_path = os.path.join(SQL_DIR, 'conv')
#             if Confirm.ask("[bold green]Run vanilla conversion[/bold green]"):                
#                 run_common(args, input_path, is_all = True)
#         case _:
#             # input_path = f"sql\\conv\\{args.type}"
#             input_path = os.path.join(SQL_DIR, 'conv', f'{args.type}')
#             if Confirm.ask(f"[bold green]Run {args.type} scripts[/bold green]"):
#                 run_common(args, input_path, is_all = False)

# def run_init(args):
#     if Confirm.ask("[bold green]Run scripts in sql/init[/bold green]"):
#         run_common(args, 'sql/init')

# def run_post(args):
#     if Confirm.ask("[bold green]Run scripts in sql/post[/bold green]"):
#         run_common(args, 'sql/post')

def run_common(args, input_path = None):
    """Execute common logic for all commands."""
    # print(args)
    # Use input_path from argument or passed explicitly
    # input_path = input_path or args.input

    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        'username': args.username,
        'password': args.password,
        'dev': args.dev,
        'debug': args.debug,
        'input': args.input or input_path,
        'use_metadata': args.metadata
    }
    run(options)

def restore(args):
    options = {
        'server': args.server or SERVER,
        'database': args.database or SA_DB,
        'message': args.message,
        'virgin': args.virgin
    }
    restore_db(options)

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
        'username': args.username,
        'password': args.password,
        'input_path': args.input,
        'chunk_size': args.chunk,
        'if_exists': args.exists
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

# def validate_args(args):
#     # Make `group` required only if `phase` is 'conv'
#     if args.phase == 'conv' and not args.group:
#         print("error: the following argument is required for 'conv' phase: group")
#         sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='SmartAdvocate Data Conversion CLI.')

    # Global flags
    parser.add_argument('-s', '--server', help='Server name. Defaults to SERVER from .env', metavar='')
    parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env', metavar='')
    parser.add_argument('-u', '--username', help='SQL Server username. If omitted, a trusted connection is used.', metavar='')
    parser.add_argument('-p', '--password', help='SQL Server password. If omitted, a trusted connection is used.', metavar='')
    parser.add_argument('-o', '--output', help='Output directory.', metavar='')
    
    # Subcommands
    subparsers = parser.add_subparsers(
        title="operations",
        dest='subcommand'
    )
    subparsers.required = True

    """ ---------------------------------------------------------------------------------------------------------------------------------------------
    Command: backup
    """
    backup_parser = subparsers.add_parser('backup', help='Backup database')
    backup_parser.add_argument('-s', '--server', help='Server name. Defaults to SERVER from .env', metavar='')
    backup_parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env', metavar='')
    # Flags
    backup_parser.add_argument('-o', '--output', help='Output directory. Defaults to /backups', metavar='')
    backup_parser.add_argument('-m', '--message', help='Optional message to include in the filename', metavar='')
    backup_parser.add_argument('--phase', help='Script phase for filename lookup', metavar='')
    backup_parser.add_argument('--group', help='Script group for filename lookup. Only applicable if phase is "conv"', metavar='')
    backup_parser.set_defaults(func=backup)

    """ ---------------------------------------------------------------------------------------------------------------------------------------------
    Command: restore
    """
    restore_parser = subparsers.add_parser('restore', help='Restore database')
    restore_parser.add_argument('-s', '--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    restore_parser.add_argument('-d', '--database', help='Name of database to restore. If not supplied, defaults to TARGET_DB from .env.', metavar='')
    restore_parser.add_argument('-m', '--message', help='Message to search for in filename', metavar='')
    restore_parser.add_argument('-v', '--virgin', action='store_true', help='Use hardcoded virgin SA database')
    restore_parser.set_defaults(func=restore)

    """ ---------------------------------------------------------------------------------------------------------------------------------------------
    Command: generate-mapping
    """
    mapping_parser = subparsers.add_parser('map', help='Run SQL scripts in \\map and output the results to Excel.')
    # mapping_parser.add_argument('system', help='SQL Script sequence to execute.', choices=['needles'], type=str)
    # mapping_parser.add_argument('-s','--server', help='Server name. If not supplied, defaults to SERVER from .env.', metavar='')
    # mapping_parser.add_argument('-d', '--database', help='Database to execute against. If not supplied, defaults to SA_DB from .env.', metavar='')
    mapping_parser.add_argument('-i', '--input', help='Input path of sql scripts', metavar='')
    mapping_parser.set_defaults(func=map)

    """ ---------------------------------------------------------------------------------------------------------------------------------------------
    Command: run
    """
    run_parser = subparsers.add_parser('run', help='Run SQL scripts')
    # run_subparsers = run_parser.add_subparsers(title="run subcommands", dest="subcommand")
    run_parser.add_argument('-i', '--input', help='Input path of sql scripts', metavar='')
    run_parser.add_argument('--dev', action='store_true', help='Include scripts prefixed with _dev_, which are skipped by default')
    run_parser.add_argument('--debug', action='store_true', help='Pauses execution after each script')
    run_parser.add_argument('--metadata', action='store_true', help='Pauses execution after each script')
    run_parser.set_defaults(func=run_common)
    # run_subparsers.required = False

    # Subcommand: run > conv
    # conv_parser = run_subparsers.add_parser('conv', help='Run scipts in /sql/conv/')
    # conv_parser.add_argument("--type", type=str, choices=["init", "contact", "case", "intake", "misc", "udf", "all", "vanilla"], help="Type of conversion")
    # conv_parser.set_defaults(func=run_conv)

    # Subcommand: run > map
    # map_parser = run_subparsers.add_parser('map', help='Execute mapping operations')
    # map_parser.set_defaults(func=run_map)

    # Subcommand: run > init
    # init_parser = run_subparsers.add_parser('init', help='Initialize configurations')
    # init_parser.set_defaults(func=run_init)

    # Subcommand: run > post
    # post_parser = run_subparsers.add_parser('post', help='Cleanup scripts')
    # post_parser.set_defaults(func=run_post)

    # Arguments
    # run_parser.add_argument('-ph','--phase',choices=['map', 'conv', 'post', 'test'],metavar='phase',help='The phase of SQL scripts to run: {map, conv, post}')
    # run_parser.add_argument('-gr','--group',nargs='?',choices=['config', 'contact', 'case', 'udf', 'misc', 'intake'],metavar='group',help='The specific group of scripts to run (required if phase = conv): {config, contact, case, udf, misc, intake}')
    # Flags -------------------
    # run_parser.add_argument('-s','--server', help='SQL Server. If omitted, defaults to SERVER from .env', metavar='')
    # run_parser.add_argument('-d', '--database', help='Database. If omitted, defaults to SA_DB from .env', metavar='')
    # run_parser.add_argument('-u', '--username', help='SQL Server username. If omitted, a trusted connection is used.', metavar='')
    # run_parser.add_argument('-p', '--password', help='SQL Server password. If omitted, a trusted connection is used.', metavar='')
    # # run_parser.add_argument('-i', '--input', help='Input path of sql scripts')
    # run_parser.add_argument('-bu', '--backup', action='store_true', help='Backup database after script execution')
    # run_parser.add_argument('--skip', action='store_true', help='Enable skipping scripts with "skip" in the filename')
    # run_parser.add_argument('--debug', action='store_true', help='Pauses execution after each script')
    # run_parser.add_argument('--all', action='store_true', help='Run all groups in the "conv" phase')
    # run_parser.set_defaults(func=run)
    
    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: encrypt
    encrypt_parser = subparsers.add_parser('encrypt', help='Run SSN Encryption')
    encrypt_parser.set_defaults(func=encrypt)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: import
    import_parser = subparsers.add_parser("import", help="Import data into SQL")
    import_subparsers = import_parser.add_subparsers(title="Convert Variants", dest="convert_variant")

    # Subcommand: flat file
    flat_file_parser = import_subparsers.add_parser("flat-file", help="Import data from flat files to SQL. Leave username and password blank to use windows authentication")
    flat_file_parser.add_argument('-s','--server', help='Server name. Defaults to SERVER from .env.', metavar='')
    flat_file_parser.add_argument('-d', '--database', help='Database name. Defaults to SA_DB from .env.', metavar='')
    flat_file_parser.add_argument('-u', '--username', help='SQL Server username', metavar='')
    flat_file_parser.add_argument('-p', '--password', help='SQL Sever password', metavar='')
    flat_file_parser.add_argument("-i", "--input", required=True, help="Path to CSV file or directory")
    flat_file_parser.add_argument("-c", "--chunk", type=int, default=10000, help="Number of rows to process at a time. Defaults = 2,000 rows. More = faster but uses more memory")
    flat_file_parser.add_argument("--exists", choices=['append', 'fail', 'replace'], default='replace', help="Specify how to handle existing tables: 'append' (default), 'fail', or 'replace'")
    flat_file_parser.set_defaults(func=handle_import_flat_file)

    # ---------------------------------------------------------------------------------------------------------------------------------------------
    # Command: export
    export_parser = subparsers.add_parser("export", help="Export data from a database")
    export_subparsers = export_parser.add_subparsers(title="Supported exports", dest="convert_variant")

    # Subcommand: convert psql-to-csv
    psql_to_csv_parser = export_subparsers.add_parser("psql-csv", help="Export PostgreSQL tables to .csv")
    psql_to_csv_parser.add_argument("-s", "--server", required=True, help="PostgreSQL hostname")
    psql_to_csv_parser.add_argument("-d", "--database", required=True, help="PostgreSQL database name")
    psql_to_csv_parser.add_argument("-u", "--username", required=True, help="PostgreSQL username")
    psql_to_csv_parser.add_argument("-p", "--password", required=True, help="PostgreSQL password")
    psql_to_csv_parser.add_argument("-o", "--output", required=True, help="Output path for .csv files")
    psql_to_csv_parser.set_defaults(func=handle_convert_psql_to_csv)

    args = parser.parse_args()

    # Validate arguments
    # if args.subcommand == 'run':
    #     validate_args(args)

    if 'func' not in args:
        parser.print_help()
    else:
        args.func(args)

if __name__ == "__main__":
    main()

