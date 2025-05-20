import os
import subprocess
import sys
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.utils.user_config import load_user_config, REQUIRED_ENV_VARS

logger = setup_logger(__name__, log_file="export.log")

# Reserved SQL keywords that need quoting
RESERVED_KEYWORDS = {"order", "from", "group", "select", "active", "default", "to", "primary"}

# Optional: Columns to exclude per table
EXCLUDE_COLUMNS = {
    "user_profile": ["email_signature"]
}

def add_export_parser(subparsers):
    """Add the export command to the parser."""
    env_config = load_user_config(REQUIRED_ENV_VARS)

    export_parser = subparsers.add_parser("export", help="Export Postgres tables to CSV files.")
    export_parser.add_argument("-s", "--server", default=env_config["PG_HOST"], help="Postgres server hostname")
    export_parser.add_argument("-d", "--database", default=env_config["PG_DB"], help="Postgres database name")
    export_parser.add_argument("-u", "--username", default=env_config["PG_USER"], help="Postgres username")
    export_parser.add_argument("-p", "--password", default=env_config["PG_PASSWORD"], help="Postgres password")
    export_parser.add_argument("-o", "--output", required=True, help="Path to output folder for CSVs")
    export_parser.set_defaults(func=handle_export_command)

def handle_export_command(args):
    """CLI dispatcher function for the 'export' command."""
    config = {
        'host': args.server,
        'database': args.database,
        'username': args.username,
        'password': args.password,
        'output': args.output
    }
    export_postgres_to_csv(config)

def export_postgres_to_csv(config: dict):
    """Export Postgres tables to CSV files."""
    host = config['host']
    database = config['database']
    username = config['username']
    password = config['password']
    output_dir = os.path.abspath(config['output'])
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Exporting tables from '{database}' on host '{host}' into '{output_dir}'")
    os.environ["PGPASSWORD"] = password

    try:
        tables = fetch_table_list(host, database, username, output_dir)
        for table in tables:
            export_table_to_csv(host, database, username, table, output_dir)
    finally:
        del os.environ["PGPASSWORD"]

def fetch_table_list(host, database, username, output_dir):
     
    tables_file = os.path.join(output_dir, "tables.txt")
    query = (
        "COPY (SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE') TO STDOUT"
    )

    with open(tables_file, 'w') as f:
        subprocess.run(
            ["psql", "-h", host, "-d", database, "-U", username, "-c", query],
            stdout=f, check=True
        )

    with open(tables_file, 'r') as f:
        tables = [line.strip() for line in f if line.strip()]

    logger.info(f"Found {len(tables)} tables to export.")
    return sorted(tables)

def get_table_columns(host, database, username, table):
    query = (
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_name = '{table}' AND table_schema = 'public';"
    )
    result = subprocess.run(
        ["psql", "-h", host, "-d", database, "-U", username, "-t", "-A", "-c", query],
        capture_output=True, text=True, check=True
    )
    columns = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return columns

def export_table_to_csv(host, database, username, table, output_dir):
    try:
        columns = get_table_columns(host, database, username, table)

        # Filter out excluded columns
        if table in EXCLUDE_COLUMNS:
            columns = [col for col in columns if col not in EXCLUDE_COLUMNS[table]]

        # Quote reserved keywords
        safe_columns = [f'"{col}"' if col in RESERVED_KEYWORDS else col for col in columns]
        column_str = ', '.join(safe_columns)
        query = f"SELECT {column_str} FROM {table}"

        copy_cmd = f"COPY ({query}) TO STDOUT WITH DELIMITER ',' CSV HEADER;"
        csv_path = os.path.join(output_dir, f"{table}.csv")

        with open(csv_path, 'w') as f:
            subprocess.run(
                ["psql", "-h", host, "-d", database, "-U", username, "-c", copy_cmd],
                stdout=f, check=True
            )

        logger.info(f"✅ Exported: {table}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to export {table}: {e}")
    except Exception as e:
        logger.error(f"⚠️ Unexpected error exporting {table}: {e}")
