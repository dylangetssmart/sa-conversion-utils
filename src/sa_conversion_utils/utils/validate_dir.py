import os

def validate_input_dir(input_dir, logger):
    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        return False
    return True