import yaml
import re
import argparse

from sa_conversion_utils.utilities.setup_logger import setup_logger
logger = setup_logger(__name__, log_file="run.log")

def read_yaml_metadata(file_path):
    """
    Reads YAML metadata from a /*--- ... ---*/ block at the top of a SQL file.

    Args:
        file_path (str): Path to the SQL file.

    Returns:
        dict: A dictionary containing the YAML metadata, or an empty dictionary if none is found.
    """

    metadata = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find block like /*--- ... ---*/
        match = re.search(r'/\*---(.*?)---\*/', content, re.DOTALL)
        if match:
            yaml_block = match.group(1).strip()
            try:
                metadata = yaml.safe_load(yaml_block)
            except yaml.YAMLError as e:
                logger.error(f"YAML parsing error in {file_path}: {e}")
                return {}
        else:
            logger.debug(f"No YAML metadata block found in {file_path}")

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}

    logger.debug(f"YAML metadata extracted from {file_path}: {metadata}")
    return metadata

def main():
    parser = argparse.ArgumentParser(description="Extract YAML metadata from a SQL file.")
    parser.add_argument("file", help="Path to the SQL file")
    args = parser.parse_args()

    metadata = read_yaml_metadata(args.file)
    print(metadata)

if __name__ == "__main__":
    main()
