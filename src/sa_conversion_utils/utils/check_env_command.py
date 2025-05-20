import os
from dotenv import load_dotenv, set_key, dotenv_values
from pathlib import Path
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from sa_conversion_utils.config.user_config import REQUIRED_ENV_VARS

logger = setup_logger(__name__, log_file="config.log")
ENV_PATH = Path(".env")


def add_config_parser(subparsers):
    """Add the config command to the parser."""
    parser = subparsers.add_parser("config", help="View or edit .env configuration")
    parser.add_argument(
        "--edit", action="store_true", help="Prompt for missing or new config values"
    )
    parser.add_argument(
        "--show-all", action="store_true", help="Show all config keys, even if unset"
    )
    parser.set_defaults(func=handle_config_command)


def handle_config_command(args):
    """Handle the 'config' command."""
    load_dotenv()
    current_config = dotenv_values(ENV_PATH)

    print("🔧 Current configuration:\n")

    for key in REQUIRED_ENV_VARS:
        value = current_config.get(key)
        if value or args.show_all:
            display = value if value else "(missing)"
            print(f"  {key}: {display}")

    if args.edit:
        print("\n✏️ Enter new values (leave blank to keep current):\n")
        for key in REQUIRED_ENV_VARS:
            current = current_config.get(key, "")
            new_value = input(f"{key} [{current}]: ").strip()
            if new_value:
                set_key(str(ENV_PATH), key, new_value)
                print(f"✅ Updated {key}")
            elif not current:
                print(f"⚠️ {key} is still missing")

    print("\n✅ Done.")
