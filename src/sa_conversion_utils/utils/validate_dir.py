import os

def validate_dir(input_dir, logger, create_if_missing=False):
    """
    Validate the input directory.

    Args:
        input_dir (str): The directory to validate.
        logger (Logger): The logger instance to log messages.
        create_if_missing (bool): Whether to create the directory if it doesn't exist.
    
    Returns:
        bool: True if the directory exists or was created, False otherwise.
    """

    if not os.path.exists(input_dir):
        # Directory does not exist
        if create_if_missing:
            logger.info(f"Directory does not exist. Attempting to create: {input_dir}")
            try:
                os.makedirs(input_dir, exist_ok=True)
                logger.info(f"Creating missing directory: {input_dir}")
                return True
            except OSError as e:
                logger.error(f"Failed to create directory {input_dir}: {e}")
                return False
        else:
            logger.error(f"Input directory does not exist: {input_dir}")
            return False
    elif not os.path.isdir(input_dir):
        # Path exists but is not a directory
        logger.error(f"Input path is not a directory: {input_dir}")
        return False
    else:
        # Directory exists
        logger.debug(f"Input directory exists: {input_dir}")
        return True