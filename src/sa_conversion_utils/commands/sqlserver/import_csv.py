# External
import os
import argparse
import logging
import pandas as pd
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

# Absolute import for standalone context
from sa_conversion_utils.utils.detect_encoding import detect_encoding
from sa_conversion_utils.commands.backup import backup
from sa_conversion_utils.utils.create_engine import main as create_engine
from sa_conversion_utils.utils.detect_delimiter import detect_delimiter

console = Console()
encodings = ['ISO-889-1', 'latin1', 'cp1252', 'utf-8']
logger = logging.getLogger(__name__)

def import_csv(args: argparse.Namespace):
    """
    Connects to a SQL Server database and imports tables from CSV files.
    """
    server = args.server
    database = args.database
    input_path = args.input_path
    chunk_size = args.chunk_size
    if_exists = args.if_exists
    extensions = args.extensions if args.extensions else ('.csv', '.txt', '.exp')

    logger.debug(f"Starting import process for {input_path} to {server}.{database}")

    engine = create_engine(server=server, database=database)

    data_files = []

    # If input path is a directory, collect all CSV and TXT files
    if os.path.isdir(input_path):
        data_files = [
            os.path.join(input_path, f) for f in os.listdir(input_path)
            if f.lower().endswith(tuple(extensions)) and os.path.getsize(os.path.join(input_path, f)) > 0
        ]
        if not data_files:
            logger.warning(f"No files with specified extensions found in the directory: {input_path}")
            return
        
    # If input path is a file, check if it is a CSV or TXT
    elif os.path.isfile(input_path):
        if input_path.lower().endswith(tuple(extensions)) and os.path.getsize(input_path) > 0:
            data_files = [input_path]
        else:
            logger.warning(f"The specified file does not have one of the required extensions: {input_path}")
            return
    else:
        logger.error(f"Invalid input path: {input_path}")
        return

    logger.debug(f"Found {len(data_files)} files to import from {input_path}")
        
    # Show the selected if-exists strategy
    console.print(f"[bold]If exists strategy:[/bold] {if_exists}")

    if not Confirm.ask(f"Import {len(data_files)} files to [bold cyan]{server}.{database}[/bold cyan]?"):
        console.print("[red]Import aborted.[/red]")
        return
    
    # Use Rich Progress to show the import status
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        "•",
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
        overall_task = progress.add_task(f"[cyan]Importing files to {database}", total=len(data_files))
        
        for file_path in sorted(list(data_files)):
            file_name = os.path.basename(file_path)

            progress.update(overall_task, description=f"[cyan]Importing {file_name}")

            try:
                # Read the CSV file into a pandas DataFrame
                detected_encoding = detect_encoding(file_path)
                detected_delimiter = detect_delimiter(file_path, detected_encoding)
                try:
                    df = pd.read_csv(file_path, encoding=detected_encoding, dtype=str, delimiter=detected_delimiter)
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='cp1252', dtype=str, delimiter=detected_delimiter)

                # Check if the DataFrame is empty (contains only a header)
                if df.empty:
                    # logger.warning(f"Skipping {file_name} - empty or only contains header.")
                    progress.console.print(f"  ℹ️  Skipping {file_name} - empty or only contains header.")
                    continue

                table_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Use to_sql with the if_exists argument
                df.to_sql(table_name, engine, index=False, if_exists=if_exists, chunksize=chunk_size)
                logger.debug(f"Successfully imported {file_name} to table {table_name}.")
                progress.console.print(f"[green]  ✅ Imported {file_name} to {table_name}[/green]")
            except Exception as e:
                # logger.error(f"Error importing {file_name}: {e}")
                progress.console.print(f"[bright_red]  ❌ Error importing {file_name}: {e}[/bright_red]")
            finally:
                progress.advance(overall_task)

    # logger.info("All tables imported.")
    console.print("[bright-green]All tables imported.[/bright-green]")
    
    # Ask the user if they would like to backup the database
    if Confirm.ask(f"Import completed. Backup {database}?"):
        backup_options = {
            'server': server,
            'database': database,
            'output': input_path,
        }
        backup(backup_options)


def setup_parser(subparsers):
    """
    Adds the 'import' subcommand to the 'sql-server' parser.
    """
    import_parser = subparsers.add_parser(
        "import-csv", help="Import CSV files to SQL Server."
    )
    import_parser.add_argument(
        "-s",
        "--server",
        required=True,
        metavar="",
        help="SQL Server hostname."
    )
    import_parser.add_argument(
        "-d",
        "--database",
        required=True,
        metavar="",
        help="Name of the database to connect to."
    )
    import_parser.add_argument(
        "-i",
        "--input-path",
        required=True,
        metavar="",
        help="Directory containing the CSV files to import."
    )
    import_parser.add_argument(
        "-c",
        "--chunk-size",
        type=int,
        default=50000,
        metavar="",
        help="Number of rows to write to the database at a time (default: 50000)."
    )
    import_parser.add_argument(
        "-x",
        "--extensions",
        nargs='*',
        metavar="",
        help="Space-separated list of file extensions to include (e.g., .csv .txt)."
    )
    import_parser.add_argument(
        "--if-exists",
        choices=['fail', 'replace', 'append'],
        default='append',
        metavar="",
        help="Action to take if the table already exists (default: append)."
    )
    import_parser.set_defaults(func=import_csv)
