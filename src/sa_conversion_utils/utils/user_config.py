from dotenv import load_dotenv, set_key
import os
from pathlib import Path
from sa_conversion_utils.utils.logging.setup_logger import setup_logger

logger = setup_logger(__name__, log_file="sami.log")

# ENV_PATH = Path(".env")
ENV_PATH = os.path.join(os.getcwd(), '.env')
logger.debug(f"ENV_PATH: {ENV_PATH}")

def get_or_prompt_env(key: str, prompt: str) -> str:
    """Get an env var from .env or prompt the user and store it."""
    load_dotenv(dotenv_path=ENV_PATH)

    # retrieve the environment variable for the key
    value = os.getenv(key)
    logger.debug(f"{key} : {value}")

    # if they key isn't found in .env, then ask the user for it
    if not value:
        value = input(f"{prompt}: ").strip()
        set_key(dotenv_path=str(ENV_PATH), key_to_set=key, value_to_set=value)
        logger.debug(f"set {key} to {value} in .env")
    return value


def load_user_config(keys_and_prompts: dict) -> dict:
    """
    Bulk load user config values.
    Accepts a dict of {ENV_VAR: prompt_text}.
    Returns a dict of {ENV_VAR: value}.
    """

    # [('SERVER', 'Enter the SQL Server name'), ('SOURCE_DB', Enter the source database name)]
    
    # loops through the items in the dictionary
    # searches for the keys in the .env file
    # if not found, prompts the user for the value and sets it in the .env file
    logger.debug(f"keys_and_prompts={keys_and_prompts}")
    
    config = {}
    for key, prompt in keys_and_prompts.items():
        config[key] = get_or_prompt_env(key, prompt)
    return config