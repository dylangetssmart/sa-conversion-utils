import os
from typing import List, Tuple
from rich.console import Console

def collect_files(input_path: str, console: Console) -> Tuple[List[str], str]:
    data_files = []

    # If input path is a directory, collect all CSV and TXT files
    if os.path.isdir(input_path):
        data_files = [
            os.path.join(input_path, f) for f in os.listdir(input_path)
            if f.lower().endswith(('.csv', '.txt', '.exp')) and f != 'import_log.txt' and os.path.getsize(os.path.join(input_path, f)) > 0
        ]
        if not data_files:
            message = f"[yellow]No CSV or TXT files found in the directory: {input_path}"
            console.print(message)
            return data_files, message
    # If input path is a file, check if it is a CSV or TXT
    elif os.path.isfile(input_path):
        if input_path.lower().endswith(('.csv', '.txt', '.exp')) and os.path.getsize(input_path) > 0:
            data_files = [input_path]
        else:
            message = f"[yellow]The specified file is not a CSV or TXT: {input_path}"
            console.print(message)
            return data_files, message
    else:
        message = f"[red]Invalid input path: {input_path}"
        console.print(message)
        return data_files, message

    message = f"[green]Collected {len(data_files)} files from {input_path}"
    console.print(message)
    return data_files, message