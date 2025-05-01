import subprocess
import os
import time
import logging

# Setup directories and logging
BASE_DIR = os.getcwd()
LOGS_DIR = os.path.join(BASE_DIR, '_logs')
os.makedirs(LOGS_DIR, exist_ok=True)
RUN_LOG = os.path.join(LOGS_DIR, 'run.log')

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File Handler (logs everything INFO and above)
file_handler = logging.FileHandler(os.path.join(LOGS_DIR, "run.log"))
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s")
file_handler.setFormatter(file_formatter)

# Console Handler (only ERROR and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_formatter = logging.Formatter("%(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s")
console_handler.setFormatter(console_formatter)

# Attach handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def sql_runner(script_path: str, server: str, database: str, username=None, password=None):
    """
    Executes a SQL script using sqlcmd.

    Args:
        script_path (str): Path to the SQL script.
        server (str): SQL Server name.
        database (str): Database name.
        username (str, optional): SQL username.
        password (str, optional): SQL password.

    Returns:
        None
    """
    start_time = time.time()
    script_name = os.path.basename(script_path)

    logger.debug(f"Starting execution of script: {script_name}")
    logger.debug(f"Script path: {script_path}")
    logger.debug(f"Server: {server}, Database: {database}")

    # Build the command
    cmd = ['sqlcmd', '-S', server, '-d', database, '-i', script_path, '-b', '-h', '-1']
    
    # Use Windows Authentication if no username/password is provided
    if username and password:
        cmd += ['-U', username, '-P', password]
        logger.debug("Using SQL authentication.")
    else:
        cmd.append('-E')  # Use Trusted Connection
        logger.debug("Using Windows authentication (Trusted Connection).")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        duration = time.time() - start_time
        output = result.stdout.strip() if result.stdout else "(No output)"
        msg = f"PASS: {script_name} in {duration:.2f}s\n{output}"
        logger.debug(msg)

    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        output = (e.stdout or '') + (e.stderr or '')
        output = output.strip() if output else str(e)

        logger.error(f"FAIL: {script_name} in {duration:.2f}s\n{output}")

        raise RuntimeError(f"ERROR: {script_name}") from e

    except Exception as e:
        logger.exception(f"Unexpected error while executing script: {script_name}")
        raise
# For manual test runs
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a SQL script using sql_runner.")
    parser.add_argument("script_path", help="Path to the .sql script")
    parser.add_argument("server", help="SQL Server name")
    parser.add_argument("database", help="Database name")
    parser.add_argument("-U", "--username", help="SQL username (optional)")
    parser.add_argument("-P", "--password", help="SQL password (optional)")

    args = parser.parse_args()

    sql_runner(
        script_path=args.script_path,
        server=args.server,
        database=args.database,
        username=args.username,
        password=args.password
    )