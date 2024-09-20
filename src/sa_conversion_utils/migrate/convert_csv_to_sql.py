import os
import pandas as pd
import time
import mmap
from sqlalchemy import create_engine
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

from ..utils.count_lines import count_lines_mmap

console = Console()
encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']

# def count_lines_mmap(file_path):
#     with open(file_path, 'r') as f:
#         # Memory-map the file, size 0 means whole file
#         with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
#             # Count the number of newlines
#             return mm.read().count(b'\n')

def read_csv_with_fallback(file_path):
	# print(file_path)
	for encoding in encodings:
		try:
			df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
			return df, encoding
		except (UnicodeDecodeError, pd.errors.ParserError) as e:
			console.print(f"[yellow]Encoding error {file_path} with {encoding}. Error: {e}")
			continue
	raise ValueError(f"Unable to read the file {file_path} with known encodings.")

def convert(engine, file_path, table_name, progress, overall_task, file_task, chunk_size):
	file_name = os.path.basename(file_path)
	# chunk_size = 2000
	df, encoding = read_csv_with_fallback(file_path)
	# print(len(df), chunk_size)
	line_count = count_lines_mmap(file_path)

	if not df.empty:
		for i, chunk in enumerate(range(0, len(df), chunk_size)):
			df_chunk = df.iloc[chunk:chunk + chunk_size]
			try:
				df_chunk.to_sql(
					table_name,
					engine,
					index=False,
					if_exists='append'
				)
				progress.update(file_task, advance=len(df_chunk))
			except TypeError as e:
				progress.console.print(f"[red]Type Error during import of chunk {i} for {file_name}. Error: {e}")
				raise
			except ValueError as e:
				progress.console.print(f"[red]Value Error during import of chunk {i} for {file_name}. Error: {e}")
				raise
			except Exception as e:
				progress.console.print(f"[red]General Exception during import of chunk {i} for {file_name}. Error: {e}")
				raise
				
		progress.console.print(f"[green]Success: Imported {file_name} into table {table_name}.")
	else:
		progress.console.print(f"[yellow]Skipped: {file_name} is empty.")

    # Explicitly mark file task as complete
	progress.update(file_task, completed=line_count)
	progress.update(overall_task, advance=1)
	progress.remove_task(file_task)

def process(engine, csv_files, table_name_options, chunk_size):
	print(csv_files, 'process')
	with Progress(
		SpinnerColumn(),
		TextColumn("[progress.description]{task.description}"),
		BarColumn(),
		TaskProgressColumn(),
		"•",
		TimeElapsedColumn(),
		"•",
		TextColumn("{task.completed:,}/{task.total:,}"),
		console=console
	) as progress:
		overall_task = progress.add_task("[cyan]Importing CSV files", total=len(csv_files))

		for csv_file in csv_files:
			line_count = count_lines_mmap(csv_file)
			file_task = progress.add_task(f"Importing {os.path.basename(csv_file)}", total=line_count)
			table_name = table_name_options or os.path.splitext(os.path.basename(csv_file))[0]

			convert(engine, csv_file, table_name, progress, overall_task, file_task, chunk_size)

def main(options):
	server = options.get('server')
	database = options.get('database')
	table_name_options = options.get('table')
	input_path = options.get('input_path')
	chunk_size = options.get('chunk_size')
	conn_str = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
	engine = create_engine(conn_str)

	csv_files = []

    # If input_path is a directory
	if os.path.isdir(input_path):
		if Confirm.ask(f'Import all .csv files within directory [bold green]{input_path}[/bold green]?'):
			csv_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.csv')]
			if not csv_files:
				console.print(f"[yellow]No CSV files found in the directory: {input_path}")
				return
    # If input_path is a file
	elif os.path.isfile(input_path):
		if input_path.endswith('.csv'):	
			if Confirm.ask(f'Import {input_path}?'):
				csv_files = [input_path]  # Treat it as a single-file list for consistency
			else:
				console.print(f"[yellow]The specified file is not a CSV: {input_path}")
				return
	else:
		console.print(f"[red]Invalid input path: {input_path}")
		return

	if csv_files:
		# print(csv_files, 'main')
		process(engine, csv_files, table_name_options, chunk_size)

if __name__ == "__main__":
    options = {
        'server': 'DylanS\\MSSQLSERVER2022',
        'database': 'ShinerLitify',
        'input_path': 'D:\\ForTanya\\2024-09-06',
		'chunk_size': 2000
    }
    main(options)