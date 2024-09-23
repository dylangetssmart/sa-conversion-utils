import subprocess
import os
import time
from datetime import datetime
from ..utils.logger import log_message, log_error
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

BASE_DIR = os.getcwd()
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
# LOGS_DIR = os.path.join(BASE_DIR, '../logs')
datetime_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
LOG_FILE = os.path.join(LOGS_DIR, f'error_log_{datetime_str}.txt')

def log_script_result(script_name: str, result_output: str, success: bool):
    status = 'SUCCESS' if success else 'FAIL'
    with open(LOG_FILE, 'a') as log_file:
        log_message(log_file.name, f'{status} - {script_name}')
        log_message(log_file.name, f'    Timestamp: {datetime.now().strftime("%Y-%m-%d_%H-%M")}')
        log_message(log_file.name, result_output)
        log_message(log_file.name, '---------------------------------------------------------------------------------------')

def sql_runner(script_path: str, server: str, database: str, script_task, progress):
    start_time = time.time()
    script_name = os.path.basename(script_path)
    output_file_path = os.path.join(LOGS_DIR, f'{datetime_str}_{script_name}.out')
    
    try:
        result = subprocess.run(
            ['sqlcmd', '-S', server, '-E', '-d', database, '-i', script_path, '-b', '-h', '-1'],
            capture_output=True, text=True, check=True
        )
        
        result_output = f'\n{result.stdout}' if result.stdout else ''
        end_time = time.time()
        time_to_import = end_time - start_time
        minutes, seconds = divmod(time_to_import, 60)

        if progress:  # Use progress.console if progress object exists
            progress.console.print(f"[green]PASS: {script_name} in {minutes:.0f}m {seconds:.0f}s")    
            progress.update(script_task)
            progress.remove_task(script_task)
        else:
            print(f"[green]PASS: {script_name} in {minutes:.0f}m {seconds:.0f}s")

        # print(f"[green]PASS: {script_name} in {minutes:.0f}m {seconds:.2f}s")
        # progress.console.print(f"[green]PASS: {script_name} in {time_to_import}")
    
        log_script_result(script_name, result_output, success=True)
        # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    except subprocess.CalledProcessError as e:
        error_output = e.stdout + e.stderr if e.stdout or e.stderr else str(e)
        
        with open(output_file_path, 'w') as output_file:
            output_file.write(error_output)
        
        log_script_result(script_name, f'Error Output:\n{error_output}', success=False)
        # print(f'FAIL - {script_name}')

        if progress:  # Use progress.console if progress object exists
            progress.console.print(f"[red]FAIL: {script_name}")
        else:
            print(f"[red]FAIL: {script_name}")

        # progress.console.print(f"[red]FAIL: {script_name}")
    


# Main block
if __name__ == "__main__":
    # Example usage
    script_path = input("Enter the path to the SQL script: ")
    server = input("Enter the SQL Server name: ")
    database = input("Enter the database name: ")
    script_task = None  # Set appropriate script task if needed
    progress = None  # Set appropriate progress object if needed

    # Call the function
    sql_runner(script_path, server, database, script_task, progress)

    # with Progress(
    #     SpinnerColumn(),
    #     TextColumn("[progress.description]{task.description}"),
    #     BarColumn(),
    #     TaskProgressColumn(),
    #     "•",
    #     TimeElapsedColumn(),
    #     "•",
    #     TextColumn("{task.completed:,}/{task.total:,}"),
    #     console=console
    # ) as progress:
    #     task = progress.add_task(f"[cyan]Executing SQL Scripts Sequence: {series}", total=len(scripts))
    # for file in scripts:
    # script_task = progress.add_task(f"[yellow]Running {file}")
    # sql_runner(
    # os.path.join(sql_dir, file),
    # server,
    # database,
    # script_task,
    # progress
    # )
    # progress.update(task, advance=1)