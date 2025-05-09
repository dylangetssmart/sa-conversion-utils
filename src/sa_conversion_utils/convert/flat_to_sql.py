# External
import os
import logging
from datetime import datetime
import pandas as pd
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn
from rich.table import Table

# Internal imports
# try:
# 	from ..utils.count_lines import count_lines_mmap
# 	from ..utils.detect_encoding import detect_encoding
# 	from ..database.backup import backup_db
# 	from ..utilities.create_engine import main as create_engine
# 	from ..utilities.collect_files import collect_files
# 	from ..utilities.detect_delimiter import detect_delimiter
# except ImportError:

# Absolute import for standalone context
from sa_conversion_utils.utils.count_lines import count_lines_mmap
from sa_conversion_utils.utils.detect_encoding import detect_encoding
from sa_conversion_utils.database.backup import backup_db
from sa_conversion_utils.utils.create_engine import main as create_engine
from sa_conversion_utils.utils.collect_files import collect_files
from sa_conversion_utils.utils.detect_delimiter import detect_delimiter

console = Console()
encodings = ['ISO-8859-1', 'latin1', 'cp1252', 'utf-8']

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def clean_file(file_path, encoding):
	"""
    Attempts to read and clean the file by handling encoding issues.
    If cleaning succeeds, the cleaned file content is returned.
    If an error occurs, logs the error and returns None.
    """
	file_name = os.path.basename(file_path)
	try:
		with open(file_path, 'r', encoding=encoding) as file:
			data = file.read()
	
		cleaned_data = data.replace('\x00', '')
		cleaned_data = cleaned_data.replace('\0', '')  # Remove any null characters
	
		logging.debug(f"Successfully cleaned {file_name} with encoding {encoding}")
		return cleaned_data
	
	except UnicodeDecodeError as e:
		logging.error(f"Unable to decode {file_name} with encoding {encoding}. Error: {str(e)}")
		return None
	except Exception as e:
		logging.error(f"An unexpected error occurred while cleaning the {file_name}. Error: {str(e)}")
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
	data = clean_file(file_path, detected_encoding)
	
	if data is None:
		return None, None, None  # Return None if cleaning fails

	for encoding in all_encodings:
		if data:
			try:
				delimiter = detect_delimiter(file_path, encoding)

				# Write cleaned data to a temporary file
				with NamedTemporaryFile(delete=False, mode='w', encoding=encoding) as temp_file:
					temp_file.write(data)
					temp_file_path = temp_file.name

				# Read the file into DataFrame with detected settings
				df = pd.read_csv(
					temp_file_path,
					encoding=encoding,
					delimiter=delimiter,
					low_memory=False,
					dtype=str
					# keep_default_na=False
				)
				logging.debug(f"Successfully read {file_path} with encoding {encoding}")
				return df, encoding, delimiter
			
			except (UnicodeDecodeError, pd.errors.ParserError) as e:
				console.print(f"[yellow]Error reading {os.path.basename(file_path)} with encoding {encoding}: {e}")
				break
	# raise ValueError(f"Unable to read the file {os.path.basename(file_path)} with detected or fallback encodings.")
	logging.error(f"Failed to read file {file_path} with all fallback encodings.")
	return None, None, None  # Return None if all attempts fail

def convert(engine, file_path, table_name, chunk_size, log_file, if_exists='append'):
	file_name = os.path.basename(file_path)
	logging.info(f"Processing {file_name}...")
	df, encoding, delimiter = read_csv_with_fallback(file_path)
	line_count = count_lines_mmap(file_path)

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
			except TypeError as e:
				logging.error(f"Error during import of chunk {i}: {e}")
				# if log_file:
				# 	log_message(log_file, f"FAIL: {file_name} | {encoding} | Error during import of chunk {i}: {e}")
			except ValueError as e:
				logging.error(f"Value Error during import of chunk {i}: {e}")
				# if log_file:
				# 	log_message(log_file, f"FAIL: {file_name} | {encoding} | Value Error during import of chunk {i}. Error: {e}")
				raise
			except Exception as e:
				logging.error(f"General Exception during import of chunk {i}: {e}")
				# if log_file:
				# 	log_message(log_file, f"FAIL: {file_name} | {encoding} | General Exception during import of chunk {i}. Error: {e}")
				raise
		
		logging.info(f"PASS: {file_name} | encoding {encoding}")
		# if log_file:
		# 	log_message(log_file, f"PASS: {file_name} | {encoding}")

	else:
		# progress.console.print(f"[yellow]SKIP: {file_name} is empty.")
		logging.info(f"SKIP: {file_name} | {encoding} | empty file")
		# if log_file:
		# 	log_message(log_file, f"SKIP: {file_name} | {encoding} | empty file")

def main(options):
	server = options.get('server')
	database = options.get('database')
	table_name_options = options.get('table')
	input_path = options.get('input_path')
	chunk_size = options.get('chunk_size')
	if_exists = options.get('if_exists', 'replace')
	# conn_str = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'

	engine = create_engine(server=server,database=database)

	data_files, message = collect_files(input_path, console)
	logging.debug(f"Collected {len(data_files)} files from {input_path}, {message}")

	if Confirm.ask(f"Import all files to [bold cyan]{server}.{database}[/bold cyan]"):
		for data_file in data_files:
			# line_count = count_lines_mmap(data_file)
			table_name = table_name_options or os.path.splitext(os.path.basename(data_file))[0]
			convert(engine, data_file, table_name, chunk_size, if_exists)

	if len(data_files) > 0:
		if Confirm.ask("Import completed. Backup database?"):
			backup_options = {
				'server': server,
				'database': database,
				'output': input_path,
			}
			backup_db(backup_options)

if __name__ == "__main__":
    options = {
        'server': 'DylanS\\MSSQLSERVER2022',
        'database': 'ShinerLitify_01-30-2025',
        'input_path': r"C:\LocalConv\Litify-Shiner\litify\data\2025-01-31",
		'chunk_size': 10000
    }
    main(options)