# External
import os
import logging
import re
import csv
from datetime import datetime
import pandas as pd
from tempfile import NamedTemporaryFile

# from sqlalchemy import create_engine
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.table import Table

# Internal imports
try:
	from ..utilities.count_lines import count_lines_mmap
	from ..utilities.detect_encoding import detect_encoding
	from ..logging.logger import log_message
	from ..database.db_utils import backup_db
	from ..utilities.create_engine import main as create_engine
	from ..utilities.collect_files import collect_files
	from ..utilities.detect_delimiter import detect_delimiter
except ImportError:
	# Absolute import for standalone context
	from sa_conversion_utils.utilities.count_lines import count_lines_mmap
	from sa_conversion_utils.utilities.detect_encoding import detect_encoding
	from sa_conversion_utils.logging.logger import log_message
	from sa_conversion_utils.database.db_utils import backup_db
	from sa_conversion_utils.utilities.create_engine import main as create_engine
	from sa_conversion_utils.utilities.collect_files import collect_files
	from sa_conversion_utils.utilities.detect_delimiter import detect_delimiter

console = Console()
encodings = ['ISO-8859-1', 'latin1', 'cp1252', 'utf-8']

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def clean_file(file_path, encoding):
	"""
    Attempts to read and clean the file by handling encoding issues.
    If cleaning succeeds, the cleaned file content is returned.
    If an error occurs, logs the error and returns None.
    """
	try:
		with open(file_path, 'r', encoding=encoding) as file:
		# with open(file_path, 'r', encoding='ISO-8859-1') as file:
			data = file.read()
	
		cleaned_data = data.replace('\x00', '')
		cleaned_data = cleaned_data.replace('\0', '')  # Remove any null characters
	
		logging.info(f"Successfully cleaned {file_path} with encoding {encoding}")
		return cleaned_data
	
	except UnicodeDecodeError as e:
		# logging.error(f"UnicodeDecodeError: Unable to decode {file_path} with encoding {encoding}. Error: {str(e)}")
		return None
	except Exception as e:
		# logging.error(f"An unexpected error occurred while cleaning the file {file_path}. Error: {str(e)}")
		return None

def read_csv_with_fallback(file_path):
	"""
    Attempts to read the file using multiple encodings and cleans it.
    Returns the cleaned data, encoding used, and delimiter if successful.
    """

	if os.path.getsize(file_path) == 0:
		console.print(f"[yellow]Skipping empty file: {file_path}")
		return
	
	detected_encoding = detect_encoding(file_path)

	all_encodings = [detected_encoding] + encodings
	# all_encodings = encodings

	data = clean_file(file_path, detected_encoding)
	for encoding in all_encodings:
		if data:
			try:
				delimiter = detect_delimiter(file_path, encoding)

				# Write cleaned data to a temporary file
				with NamedTemporaryFile(delete=False, mode='w', encoding=encoding) as temp_file:
					temp_file.write(data)
					temp_file_path = temp_file.name
				# with open(cleaned_file, 'r', encoding=encoding) as file:
				# 	sample = file.readline()
				# 	sniffer = csv.Sniffer()
				# 	try:
				# 		dialect = sniffer.sniff(sample)
				# 		delimiter = dialect.delimiter
				# 	except csv.Error:
				# 		delimiter = ','  # Default to comma if detection fails
					# console.print(f"[blue]Detected delimiter '{delimiter}' for {os.path.basename(file_path)}")

				# Read the file into DataFrame with detected settings
				df = pd.read_csv(
					temp_file_path,
					# data,
					# cleaned_file,
					# file_path,
					encoding=encoding,
					delimiter=delimiter,
					low_memory=False,
					dtype=str
					# keep_default_na=False
				)
				return df, encoding, delimiter

			except (UnicodeDecodeError, pd.errors.ParserError) as e:
				console.print(f"[yellow]Error reading {os.path.basename(file_path)} with encoding {encoding}: {e}")
				break
	# raise ValueError(f"Unable to read the file {os.path.basename(file_path)} with detected or fallback encodings.")
	# logging.error(f"Failed to read file {file_path} with all fallback encodings.")
	return None, None, None  # Return None if all attempts fail

def convert(engine, file_path, table_name, progress, overall_task, file_task, chunk_size, log_file, if_exists='append'):
	# print(log_file)
	file_name = os.path.basename(file_path)
	df, encoding, delimiter = read_csv_with_fallback(file_path)
	# df = replace_newlines_with_pipe(df)
	line_count = count_lines_mmap(file_path)

	if log_file:
		start_time = datetime.now().strftime('%Y-%m-%d %H:%M')
		log_message(log_file, f"Begin import: {start_time}")

	if df is not None and not df.empty:
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
		# progress.console.print(f"[yellow]SKIP: {file_name} is empty.")
		if log_file:
			log_message(log_file, f"SKIP: {file_name} | {encoding} | empty file")

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
	if_exists = options.get('if_exists', 'replace')
	conn_str = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
	# conn_str = r'mssql+pyodbc://sa:SAsuper11050@72.52.250.51/testTanya?driver=ODBC+Driver+17+for+SQL+Server'
	# engine = create_engine(conn_str)

	engine = create_engine(server=server,database=database)

	data_files = []
	file_summary = {}

	data_files, message = collect_files(input_path, console)
	# # Collect data files for import
	# if os.path.isdir(input_path):
	# 	data_files = [
	# 		os.path.join(input_path, f) for f in os.listdir(input_path)
	# 		if f.lower().endswith(('.csv', '.txt', '.exp')) and f != 'import_log.txt' and os.path.getsize(os.path.join(input_path, f)) > 0
	# 	]
	# 	if not data_files:
	# 		console.print(f"[yellow]No CSV or TXT files found in the directory: {input_path}")
	# 		return
	# elif os.path.isfile(input_path):
	# 	if input_path.lower().endswith(('.csv', '.txt', '.exp')) and os.path.getsize(input_path) > 0:
	# 		data_files = [input_path]
	# 	else:
	# 		console.print(f"[yellow]The specified file is not a CSV or TXT: {input_path}")
	# 		return
	# else:
	# 	console.print(f"[red]Invalid input path: {input_path}")
	# 	return

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
				convert(engine, data_file, table_name, progress, overall_task, file_task, chunk_size, log_file, if_exists)

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
        'input_path': r"C:\LocalConv\Litify-Shiner\trans\12.4.2024LitifyBackup\litify_pm__Damage__c.csv",
        # 'input_path': r"D:\Needles-JoelBieber\trans\Grow Path\PostgreSQL data - joelbieber_backup",
		'chunk_size': 10000
    }
    main(options)