import psycopg
import os
from typing import List, Optional
from rich.prompt import Confirm
from rich.console import Console
from sa_conversion_utils.utils.logging.setup_logger import setup_logger

logger = setup_logger(__name__, log_file="export.log")
console = Console()


def export_all_tables_to_csv(
    host: str,
    dbname: str,
    user: str,
    password: str,
    output_dir: str = "./exports",
    table_names: Optional[List[str]] = None,
):
    """
    Connects to a PostgreSQL database and exports tables to CSV using COPY TO.
    """
    os.makedirs(output_dir, exist_ok=True)
    conn_str = f"host={host} dbname={dbname} user={user} password={password}"

    if Confirm.ask(f"Export all tables from {host} to csv"):
        logger.debug(f"Exporting all tables from {host} to csv")
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                if table_names is None:
                    # Fetch all table names in public schema
                    cursor.execute(
                        """
						SELECT tablename
						FROM pg_catalog.pg_tables
						WHERE schemaname = 'public';
					"""
                    )
                    tables = cursor.fetchall()
                    tables_to_export = [table[0] for table in tables]
                else:
                    tables_to_export = table_names

                for table_name in tables_to_export:
                    file_path = os.path.join(output_dir, f"{table_name}.csv")
                    print(f"Exporting {table_name} ...")

                    try:
                        with open(file_path, "wb") as f:
                            with cursor.copy(
                                f"COPY {table_name} TO STDOUT WITH CSV HEADER"
                            ) as copy:
                                for data in copy:
                                    f.write(data)
                                    logger.debug(
                                        f"Exported {table_name} to {file_path}"
                                    )
                    except psycopg.Error as e:
                        console.print(f"[bright-red]Error exporting {table_name}: {e}[bright-red]")
                        continue

        console.print("[bright-green]All tables exported.[bright-green]")
