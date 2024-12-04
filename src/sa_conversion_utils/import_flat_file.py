# External
import os
import re
import csv
from datetime import datetime
import pandas as pd
# from sqlalchemy import create_engine
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.table import Table

# Internal imports
try:
	from .utilities.count_lines import count_lines_mmap
	from .utilities.detect_encoding import detect_encoding
	from .utilities.logger import log_message
	from .db_utils import backup_db
	from .utilities.create_engine import main as create_engine
except ImportError:
	# Absolute import for standalone context
	from sa_conversion_utils.utilities.count_lines import count_lines_mmap
	from sa_conversion_utils.utilities.detect_encoding import detect_encoding
	from sa_conversion_utils.utilities.logger import log_message
	from sa_conversion_utils.db_utils import backup_db
	from sa_conversion_utils.utilities.create_engine import main as create_engine

console = Console()
encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']

def replace_newlines_with_pipe(df):
    # Apply replacement for all string columns in the DataFrame using map on each column
    return df.apply(lambda col: col.map(lambda x: re.sub(r'\r\n|\n', '|', x) if isinstance(x, str) else x))

def read_csv_with_fallback(file_path):
	detected_encoding = detect_encoding(file_path)
	all_encodings = [detected_encoding] + encodings

	for encoding in all_encodings:
		try:
			# Detect delimiter from the first line with the given encoding
			with open(file_path, 'r', encoding=encoding) as file:
				sample = file.readline()
				sniffer = csv.Sniffer()
				try:
					dialect = sniffer.sniff(sample)
					delimiter = dialect.delimiter
				except csv.Error:
					delimiter = ','  # Default to comma if detection fails
				# console.print(f"[blue]Detected delimiter '{delimiter}' for {os.path.basename(file_path)}")

			# Read the file into DataFrame with detected settings
			df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, low_memory=False)
			return df, encoding, delimiter

		except (UnicodeDecodeError, pd.errors.ParserError) as e:
			console.print(f"[yellow]Error reading {os.path.basename(file_path)} with encoding {encoding}: {e}")

	raise ValueError(f"Unable to read the file {os.path.basename(file_path)} with detected or fallback encodings.")

def convert(engine, file_path, table_name, progress, overall_task, file_task, chunk_size, log_file):
	# print(log_file)
	file_name = os.path.basename(file_path)
	df, encoding, delimiter = read_csv_with_fallback(file_path)
	df = replace_newlines_with_pipe(df)
	line_count = count_lines_mmap(file_path)

	if log_file:
		start_time = datetime.now().strftime('%Y-%m-%d %H:%M')
		log_message(log_file, f"Begin import: {start_time}")

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
				if log_file:
					log_message(log_file, f"FAIL: {file_name} | {encoding} | Error during import of chunk {i}: {e}")
			except ValueError as e:
				progress.console.print(f"[red]Value Error during import of chunk {i} for {file_name}. Error: {e}")
				if log_file:
					log_message(log_file, f"FAIL: {file_name} | {encoding} | Value Error during import of chunk {i}. Error: {e}")
				raise
			except Exception as e:
				progress.console.print(f"[red]General Exception during import of chunk {i} for {file_name}. Error: {e}")
				if log_file:
					log_message(log_file, f"FAIL: {file_name} | {encoding} | General Exception during import of chunk {i}. Error: {e}")
				raise
				
		progress.console.print(f"[green]PASS: {file_name}")
		if log_file:
			log_message(log_file, f"PASS: {file_name} | {encoding}")

	else:
		progress.console.print(f"[yellow]SKIP: {file_name} is empty.")
		if log_file:
			log_message(log_file, f"S: {file_name} | {encoding} | empty file")

    # Explicitly mark file task as complete
	progress.update(file_task, completed=line_count)
	progress.update(overall_task, advance=1)
	progress.remove_task(file_task)


def main(options):
	server = options.get('server')
	database = options.get('database')
	table_name_options = options.get('table')
	input_path = options.get('input_path')
	chunk_size = options.get('chunk_size')
	conn_str = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
	# conn_str = r'mssql+pyodbc://sa:SAsuper11050@72.52.250.51/testTanya?driver=ODBC+Driver+17+for+SQL+Server'
	# engine = create_engine(conn_str)

	engine = create_engine(server=server,database=database,windows_auth=True)

	data_files = []
	file_summary = {}

	# Collect data files for import
	if os.path.isdir(input_path):
		data_files = [
			os.path.join(input_path, f) for f in os.listdir(input_path)
			if f.lower().endswith(('.csv', '.txt', '.exp')) and f != 'import_log.txt'
		]
		if not data_files:
			console.print(f"[yellow]No CSV or TXT files found in the directory: {input_path}")
			return
	elif os.path.isfile(input_path):
		if input_path.lower().endswith(('.csv', '.txt', '.exp')):
			data_files = [input_path]
		else:
			console.print(f"[yellow]The specified file is not a CSV or TXT: {input_path}")
			return
	else:
		console.print(f"[red]Invalid input path: {input_path}")
		return

	# Create file summary without reading
	for data_file in data_files:
		file_type = os.path.splitext(data_file)[1]
		if file_type not in file_summary:
			file_summary[file_type] = 0
		file_summary[file_type] += 1

	# Display summary table
	summary_table = Table(title="File Import Summary")
	summary_table.add_column("File Type", style="cyan", justify="left")
	summary_table.add_column("Count", style="green", justify="right")

	for file_type, count in file_summary.items():
		summary_table.add_row(file_type, str(count))

	console.print(summary_table)

    # Confirm import for all files in summary
	if Confirm.ask(f"Import all files to [bold cyan]{server}.{database}[/bold cyan]"):
		log_file = None
		if Confirm.ask("Do you want to output a log file?"):
			log_file = os.path.join(input_path, 'import_log.txt')

		with Progress(
			SpinnerColumn(),
			TextColumn("[progress.description]{task.description}"),
			BarColumn(),
			TaskProgressColumn(),
			"•",
			TimeElapsedColumn(),
			"•",
			TextColumn("{task.completed:,}/{task.total:,}"),
			TextColumn(f"Chunk size: {chunk_size:,} rows"),
			console=console
		) as progress:
			overall_task = progress.add_task("[cyan]Importing data files", total=len(data_files))
			# log_file = os.path.join(input_path, 'import_log.txt')

			for data_file in data_files:
				line_count = count_lines_mmap(data_file)
				file_task = progress.add_task(f"Importing {os.path.basename(data_file)}", total=line_count)
				table_name = table_name_options or os.path.splitext(os.path.basename(data_file))[0]

                # Start conversion
				convert(engine, data_file, table_name, progress, overall_task, file_task, chunk_size, log_file)

	if len(data_files) > 0:
		if Confirm.ask("Import completed. Backup database?"):
			backup_options = {
				'server': server,
				'database': database,
				'output': input_path,
				# 'message': message  # Can be None if not provided
			}
			backup_db(backup_options)

if __name__ == "__main__":
    options = {
        'server': 'DylanS\\MSSQLSERVER2022',
        'database': 'test',
        'input_path': r"C:\Users\dsmith\Downloads\CMCLIENT.EXP",
        # 'input_path': r"D:\Needles-JoelBieber\trans\Grow Path\PostgreSQL data - joelbieber_backup",
		'chunk_size': 10000
    }
    main(options)