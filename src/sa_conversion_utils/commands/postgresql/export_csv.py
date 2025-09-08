import psycopg
import os
import argparse
import logging
from typing import List, Optional
from rich.prompt import Confirm
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn

logger = logging.getLogger(__name__)
console = Console()

def export_csv(args: argparse.Namespace):
    """
    Connects to a PostgreSQL database and exports tables to CSV using COPY TO.
    """
    server = args.server
    database = args.database
    user = args.user
    password = args.password
    output_dir = args.output_dir
    table_names = args.tables
    if_exists = args.if_exists

    os.makedirs(output_dir, exist_ok=True)
    conn_str = f"host={server} dbname={database} user={user} password={password}"

    # Separate tables to include and exclude
    tables_to_include = {t for t in table_names if not t.startswith('!')} if table_names else set()
    tables_to_exclude = {t[1:] for t in table_names if t.startswith('!')} if table_names else set()

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                # First, get all public tables from the database
                cursor.execute(
                    """
                    SELECT tablename
                    FROM pg_catalog.pg_tables
                    WHERE schemaname = 'public';
                    """
                )
                all_public_tables = {table[0] for table in cursor.fetchall()}

                # Determine the final list of tables to export
                if tables_to_include:
                    tables_to_export = tables_to_include.intersection(all_public_tables)
                    if tables_to_include - all_public_tables:
                        missing_tables = tables_to_include - all_public_tables
                        console.print(f"[yellow]Warning: The following tables were requested but do not exist: {', '.join(missing_tables)}[/yellow]")
                else:
                    tables_to_export = all_public_tables

                # Now, filter out any tables the user wants to exclude
                tables_to_export = tables_to_export - tables_to_exclude
                
                if not tables_to_export:
                    console.print("[yellow]No tables to export after applying filters.[/yellow]")
                    return

                console.print(f"[bold blue]Tables to export:[/bold blue] {', '.join(sorted(list(tables_to_export)))}")
                if tables_to_exclude:
                    console.print(f"[bold blue]Tables to exclude:[/bold blue] {', '.join(sorted(list(tables_to_exclude)))}")

                # Show the selected if-exists strategy
                console.print(f"[bold blue]If exists strategy:[/bold blue] {if_exists}")

                if not Confirm.ask(f"Export tables from {server}.{database} to csv?"):
                    console.print("[red]Export aborted.[/red]")
                    return

                # Use Rich Progress to show the export status
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
                    overall_task = progress.add_task(f"[cyan]Exporting tables from {database}", total=len(tables_to_export))
                
                    for table_name in sorted(list(tables_to_export)):
                        file_path = os.path.join(output_dir, f"{table_name}.csv")

                        if if_exists == 'skip' and os.path.exists(file_path):
                            progress.console.print(f"  [yellow]Skipping {table_name}, file already exists.[/yellow]")
                            progress.advance(overall_task)
                            continue

                        progress.update(overall_task, description=f"[cyan]Exporting {table_name}")

                        try:
                            with open(file_path, "wb") as f:
                                with cursor.copy(
                                    f"COPY {table_name} TO STDOUT WITH CSV HEADER"
                                ) as copy:
                                    for data in copy:
                                        f.write(data)
                            progress.console.print(f"  [green]✅ Exported {table_name} to {file_path}[/green]")
                        except psycopg.Error as e:
                            progress.console.print(f"[bright-red]  ❌ Error exporting {table_name}: {e}[/bright-red]")
                        
                        progress.advance(overall_task)

    except psycopg.OperationalError as e:
         console.print(f"[red]Connection failed: {e}[/red]")
         return

    console.print("[bright-green]All tables exported.[/bright-green]")

def setup_parser(subparsers):
    """
    Adds the 'export' subcommand to the 'postgresql' parser.
    """
    export_parser = subparsers.add_parser(
        "export-csv", help="Export PostgreSQL tables to .csv"
    )
    export_parser.add_argument(
        "-s",
        "--server",
        required=True,
        help="PostgreSQL server hostname."
    )
    export_parser.add_argument(
        "-d",
        "--database",
        required=True,
        help="Name of the database to connect to."
    )
    export_parser.add_argument(
        "-U",
        "--user",
        required=True,
        help="PostgreSQL username."
    )
    export_parser.add_argument(
        "-P",
        "--password",
        required=True,
        help="PostgreSQL password."
    )
    export_parser.add_argument(
        "-o",
        "--output-dir",
        default="./exports",
        help="Directory to save CSV files. (default: /exports)"
    )
    export_parser.add_argument(
        "-t",
        "--tables",
        nargs="*",
        help="Space-separated list of tables to export. Use `!tablename` to exclude. Exports all public tables if omitted."
    )
    export_parser.add_argument(
        "--if-exists",
        choices=['overwrite', 'skip'],
        default='overwrite',
        help="Action to take if the CSV file already exists (default: overwrite)."
    )
    export_parser.set_defaults(func=export_csv)
