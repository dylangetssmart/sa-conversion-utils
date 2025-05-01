import os
from sa_conversion_utils.run.read_yaml_metadata import read_yaml_metadata
from sa_conversion_utils.utilities.setup_logger import setup_logger

logger = setup_logger(__name__, log_file="run.log")

GROUP_ORDER = [
    "setup",
    "load",
    "postload",
    "cleanup"
]

def sort_scripts_using_metadata(input_dir):
    """Reads metadata from each SQL file and builds a list of scripts with their sequence and group."""
    scripts_with_metadata = []

    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.sql'):
            file_path = os.path.join(input_dir, filename)
            logger.debug(f"Processing file: {file_path}")

            # Read metadata from the file
            metadata = read_yaml_metadata(file_path)

            if metadata:
                # Fetch group and order, default to 'miscellaneous' and infinity if not present
                group = metadata.get("group", "misc") or 'misc'
                order = metadata.get("order", float('inf')) if metadata.get("order") is not None else float('inf')                
                logger.debug(f"Metadata found for {filename}: {metadata}")
            else:
                logger.debug(f"No metadata found for file: {filename}")
                group = "misc"
                order = float('inf')  # Default order if no metadata is found

            scripts_with_metadata.append({
                "filename": filename,
                "group": group,
                "order": order
            })
            logger.debug(f"Appended {filename} with group {group} and order {order}")

    # Sort first by group order and then by script order
    scripts_with_metadata.sort(key=lambda x: (GROUP_ORDER.index(x["group"]), x["order"]))
    
    # Return sorted list of filenames
    return [script["filename"] for script in scripts_with_metadata]