import yaml
import re
import argparse

def read_yaml_metadata(file_path):
    """
    Reads YAML metadata from a /*--- ... ---*/ block at the top of a SQL file.

    Args:
        file_path (str): Path to the SQL file.

    Returns:
        dict: Parsed metadata as a dictionary, or an empty dict if not found.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find block like /*--- ... ---*/
    match = re.search(r'/\*---(.*?)---\*/', content, re.DOTALL)
    if not match:
        return {}

    yaml_block = match.group(1).strip()
    try:
        return yaml.safe_load(yaml_block)
    except yaml.YAMLError as e:
        print(f"YAML parsing error in {file_path}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description="Extract YAML metadata from a SQL file.")
    parser.add_argument("file", help="Path to the SQL file")
    args = parser.parse_args()

    metadata = read_sql_metadata(args.file)
    print(metadata)

if __name__ == "__main__":
    main()
