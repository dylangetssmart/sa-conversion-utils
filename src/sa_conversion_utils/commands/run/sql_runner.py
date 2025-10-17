import subprocess
import os
import time
import logging

BASE_DIR = os.getcwd()
logger = logging.getLogger("run")

def run_sql_script(
        script_path: str,
        server: str,
        database: str,
        username=None,
        password=None,
        progress=None,
    ):
    """
    Executes a SQL script using sqlcmd.

    Args:
        script_path (str): Path to the SQL script.
        server (str): SQL Server name.
        database (str): Database name.
        username (str, optional): SQL username.
        password (str, optional): SQL password.
    """
    start_time = time.time()
    script_name = os.path.basename(script_path)

    # logger.debug(f"Running {script_name}")
    # logger.debug(f"Script path: {script_path}")
    # logger.debug(f"Server: {server}, Database: {database}")

    # Build the command
    cmd = ['sqlcmd', '-S', server, '-d', database, '-i', script_path, '-b', '-h', '-1']
    
    # Use Windows Authentication if no username/password is provided
    if username and password:
        cmd += ['-U', username, '-P', password]
        # logger.debug("Using SQL authentication.")
    else:
        cmd.append('-E')  # Use Trusted Connection
        # logger.debug("Using Windows authentication (Trusted Connection).")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )

        duration = time.time() - start_time
        output = result.stdout.strip() if result.stdout else "(No output)"

        logger.info(f"PASS: {script_name}")
        # logger.debug(f"Script completed in {duration:.2f}s")    
        # logger.debug(f"Script output: \n {output}")

        # if progress:
        #     progress.console.print(f"[green]PASS: {script_name} ")

    except subprocess.CalledProcessError as e:
        output = (e.stdout or '') + (e.stderr or '')
        output = output.strip() if output else str(e)

        logger.error(f"FAIL: {script_name}")
        logger.debug(f"{output} \n")

        # if progress:
        #     progress.console.print(f"[red]FAIL: {script_name} ")

    except Exception as e:
        logger.exception(f"Unexpected error in {script_name}")
        raise