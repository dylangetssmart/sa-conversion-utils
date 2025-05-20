# psql_to_csv.py
import psycopg2
import os
from typing import List, Optional
from sa_conversion_utils.utils.logging.setup_logger import setup_logger

# logger = setup_logger(__name__)


def export_tables_to_csv(
    conn: psycopg2.extensions.connection,
    output_dir: str,
    table_names: Optional[List[str]] = None,
    delimiter: str = ',',
    quotechar: str = '"',
    null_string: str = '',
    header: bool = True,
    encoding: str = 'utf8',
) -> None:
    """
    Exports all tables in a PostgreSQL database (or a specified subset) to individual CSV files.

    Args:
        conn: A psycopg2 connection object.  Ensure the user connected with this connection has
              the necessary permissions to execute COPY TO on the tables.
        output_dir: The directory where the CSV files will be created.  The directory must exist
                    and be writable.
        table_names: An optional list of table names to export. If None, all user-tables in the
                      database will be exported.
        delimiter: The delimiter character for the CSV files (default: ',').
        quotechar: The character used to quote fields (default: '"').
        null_string: The string to use for null values in the CSV files (default: '').
        header: Whether to include a header row in the CSV files (default: True).
        encoding: The character encoding to use for the CSV files (default: 'utf8').
    """
    if not os.path.exists(output_dir):
        raise ValueError(f"Output directory '{output_dir}' does not exist.")
    if not os.path.isdir(output_dir):
        raise ValueError(f"'{output_dir}' is not a directory.")
    if not os.access(output_dir, os.W_OK):
        raise PermissionError(f"Cannot write to directory '{output_dir}'.".format(output_dir=output_dir))

    cursor = conn.cursor()

    try:
        if table_names is None:
            # Fetch all user table names if no specific tables are provided
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE';"  # Consider only 'BASE TABLE'
            )
            tables = [row[0] for row in cursor.fetchall()]
        else:
            tables = table_names

        for table_name in tables:
            # Construct the COPY TO command
            copy_sql = f"COPY {table_name} TO STDOUT WITH (FORMAT CSV, DELIMITER '{delimiter}', QUOTE '{quotechar}', NULL '{null_string}', HEADER {str(header).upper()}, ENCODING '{encoding}')"

            # Construct the output file path
            file_path = os.path.join(output_dir, f"{table_name}.csv")

            try:
                with open(file_path, 'w', encoding=encoding) as f:
                    cursor.copy_expert(copy_sql, f)  # Use copy_expert for file output
                print(f"Table '{table_name}' successfully exported to '{file_path}'")
            except Exception as e:
                print(f"Error exporting table '{table_name}': {e}")

    finally:
        cursor.close()
    # Note: It's the caller's responsibility to close the connection.  We do NOT close it here.