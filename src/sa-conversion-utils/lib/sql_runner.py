import subprocess
import os
from datetime import datetime
from .logger import log_message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, '../logs')
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
    script_name = os.path.basename(script_path)
    output_file_path = os.path.join(LOGS_DIR, f'{datetime_str}_{script_name}.out')
    
    try:
        result = subprocess.run(
            ['sqlcmd', '-S', server, '-E', '-d', database, '-i', script_path, '-b', '-h', '-1'],
            capture_output=True, text=True, check=True
        )
        
        result_output = f'\n{result.stdout}' if result.stdout else ''
        log_script_result(script_name, result_output, success=True)
        # print(f'SUCCESS - {script_name}')
        progress.console.print(f"[green]PASS: {script_name}")
    
    except subprocess.CalledProcessError as e:
        error_output = e.stdout + e.stderr if e.stdout or e.stderr else str(e)
        
        with open(output_file_path, 'w') as output_file:
            output_file.write(error_output)
        
        log_script_result(script_name, f'Error Output:\n{error_output}', success=False)
        # print(f'FAIL - {script_name}')
        progress.console.print(f"[red]FAIL: {script_name}")
    
    progress.update(script_task)
    progress.remove_task(script_task)
