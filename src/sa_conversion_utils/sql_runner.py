import subprocess
import os
import time
from datetime import datetime
from .utilities.logger import log_message, log_error
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

BASE_DIR = os.getcwd()
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
datetime_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
LOG_FILE = os.path.join(LOGS_DIR, f'error_log_{datetime_str}.txt')

def log_script_result(script_name: str, result_output: str, success: bool):
    status = 'SUCCESS' if success else 'FAIL'
    with open(LOG_FILE, 'a') as log_file:
        log_message(log_file.name, f'{status} - {script_name}')
        log_message(log_file.name, f'    Timestamp: {datetime.now().strftime("%Y-%m-%d_%H-%M")}')
        log_message(log_file.name, result_output)
        log_message(log_file.name, '---------------------------------------------------------------------------------------')

def sql_runner(script_path: str, server: str, database: str, script_task, progress, username=None, password=None):
    start_time = time.time()
    script_name = os.path.basename(script_path)
    output_file_path = os.path.join(LOGS_DIR, f'{datetime_str}_{script_name}.out')

    # Build the command
    cmd = ['sqlcmd', '-S', server, '-d', database, '-i', script_path, '-b', '-h', '-1']
    
    # Use Windows Authentication if no username/password is provided
    if username and password:
        cmd += ['-U', username, '-P', password]
    else:
        cmd.append('-E')  # Use Trusted Connection

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, check=True
        )

        result_output = f'\n{result.stdout}' if result.stdout else ''
        end_time = time.time()
        minutes, seconds = divmod(end_time - start_time, 60)

        if progress:
            progress.console.print(f"[green]PASS: {script_name} in {minutes:.0f}m {seconds:.0f}s")
            progress.update(script_task)
            progress.remove_task(script_task)
        else:
            print(f"[green]PASS: {script_name} in {minutes:.0f}m {seconds:.0f}s")

        log_script_result(script_name, result_output, success=True)

    except subprocess.CalledProcessError as e:
        error_output = e.stdout + e.stderr if e.stdout or e.stderr else str(e)
        
        with open(output_file_path, 'w') as output_file:
            output_file.write(error_output)
        
        log_script_result(script_name, f'Error Output:\n{error_output}', success=False)

        if progress:
            progress.console.print(f"[red]ERR: {script_name}")
            progress.update(script_task)
            progress.remove_task(script_task)
        else:
            print(f"[red]ERR: {script_name}")

# Main block
if __name__ == "__main__":
    script_path = input("Enter the path to the SQL script: ")
    server = input("Enter the SQL Server name: ")
    database = input("Enter the database name: ")
    script_task = None
    progress = None

    # Call the function
    sql_runner(script_path, server, database, script_task, progress)