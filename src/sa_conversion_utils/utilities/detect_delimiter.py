import csv
import logging

def detect_delimiter(file_path, encoding):
    """
    Detects the delimiter of the file by reading the first line.
    Returns the detected delimiter or a default delimiter (comma) if detection fails.
    """
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            sample = file.readline()
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ','  # Default to comma if detection fails
        return delimiter
    except Exception as e:
        logging.error(f"An error occurred while detecting the delimiter for {file_path}. Error: {str(e)}")
        return ','  # Default to comma if an error occurs