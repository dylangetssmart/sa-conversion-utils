import os
import pandas as pd
# import time
# import chardet
# import mmap
from sqlalchemy import create_engine
# https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, SpinnerColumn

# Relative import for package context
try:
	from ..utils.count_lines import count_lines_mmap
	from ..utils.detect_encoding import detect_encoding
# Absolute import for standalone context
except ImportError:
	from sa_conversion_utils.utils.count_lines import count_lines_mmap
	from sa_conversion_utils.utils.detect_encoding import detect_encoding


# step 1 = process
# step 2 - convert
# step 3 - convert calls read_csv_with_fallback()
# read_csv_with_fallback calls pandas.read_csv()
# step 4 convert invokes .to_sql() on the dataframe received from read_csv_with_fallback



console = Console()
encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']

# def count_lines_mmap(file_path):
#     with open(file_path, 'r') as f:
#         # Memory-map the file, size 0 means whole file
#         with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
#             # Count the number of newlines
#             return mm.read().count(b'\n')

# def detect_encoding(file_path):
#     with open(file_path, 'rb') as f:
#         result = chardet.detect(f.read())
#         return result['encoding']

def read_csv_with_fallback(file_path):
	# print(file_path)
	# for encoding in encodings:
	# 	try:
	# 		df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
	# 		return df, encoding
	# 	except (UnicodeDecodeError, pd.errors.ParserError) as e:
	# 		console.print(f"[yellow]Encoding error {file_path} with {encoding}. Error: {e}")
	# 		continue
	# raise ValueError(f"Unable to read the file {file_path} with known encodings.")

	detected_encoding = detect_encoding(file_path)
	all_encodings = [detected_encoding] + encodings

	for encoding in all_encodings:
		try:
			df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
			console.print(f"[green]Successfully read {os.path.basename(file_path)} with encoding: {encoding}")
			return df, encoding
		except (UnicodeDecodeError, pd.errors.ParserError) as e:
			console.print(f"[yellow]Error reading {os.path.basename(file_path)} with encoding {encoding}: {e}")
    
	raise ValueError(f"Unable to read the file {os.path.basename(file_path)} with detected or fallback encodings.")

	# for encoding in encodings:
	# 	try:
	# 		df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
	# 		return df, encoding
	# 	except (UnicodeDecodeError, pd.errors.ParserError) as e:
	# 		console.print(f"[yellow]Encoding error:\nFile: {os.path.basename(file_path)}\nEncoding: {encoding}\nError: {e}")
	# 		continue
    
	# # console.print(f"[blue]Using detected encoding: {detected_encoding} for file {file_path}")
    
	# try:
	# 	df = pd.read_csv(file_path, encoding=detected_encoding, low_memory=False)
	# 	return df, detected_encoding
	# except Exception as e:
	# 	raise ValueError(f"Unable to read the file {file_path} even with detected encoding: {detected_encoding}. Error: {e}")

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
	# print(csv_files, 'process')
	with Progress(
		SpinnerColumn(),
		TextColumn("[progress.description]{task.description}"),
		BarColumn(),
		TaskProgressColumn(),
		"•",
		TimeElapsedColumn(),
		"•",
		TextColumn("{task.completed:,}/{task.total:,}"),
		TextColumn(f"Chunk size: {chunk_size} rows"),
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
			if Confirm.ask(f'Import {os.path.basename(input_path)}?'):
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
        'database': 'JoelBieber_GrowPath',
        'input_path': r"D:\Needles-JoelBieber\trans\Grow Path\PostgreSQL data - joelbieber_backup\user_profile.csv",
        # 'input_path': r"D:\Needles-JoelBieber\trans\Grow Path\PostgreSQL data - joelbieber_backup",
		'chunk_size': 2000
    }
    main(options)