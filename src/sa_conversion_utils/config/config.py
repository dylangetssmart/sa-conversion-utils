import argparse
from pathlib import Path
from dotenv import dotenv_values, set_key
from sa_conversion_utils.utils.logging.setup_logger import setup_logger
from rich.table import Table
from rich.console import Console

logger = setup_logger(__name__, log_file="config.log")
ENV_PATH = Path(".env")
console = Console()

def add_config_parser(subparsers):
    """Add the config command and its subcommands to the parser."""
    config_parser = subparsers.add_parser("config", help="Manage .env configuration file.")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Subcommands")

    # Show command
    show_parser = config_subparsers.add_parser("show", help="Display current .env keys and values")
    show_parser.set_defaults(func=handle_config_show)

    # Edit command
    edit_parser = config_subparsers.add_parser("edit", help="Edit the value of an existing .env key")
    edit_parser.add_argument("key", help="Key to edit")
    edit_parser.add_argument("value", help="New value for the key")
    edit_parser.set_defaults(func=handle_config_edit)

    # Add command
    add_parser = config_subparsers.add_parser("add", help="Add a new key-value pair to .env")
    add_parser.add_argument("key", help="Key to add")
    add_parser.add_argument("value", help="Value to set")
    add_parser.set_defaults(func=handle_config_add)

def handle_config_show(args):
    if not ENV_PATH.exists():
        logger.warning(".env file not found.")
        return
    
    env = dotenv_values(ENV_PATH)
    if not env:
        logger.info(".env file is empty.")
        return

    console.print(f"\n.env Configuration ({ENV_PATH.resolve()}):\n")

    table = Table(
        title=f"{ENV_PATH.resolve()}",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for key, value in env.items():
        table.add_row(key, value or "")
    console.print(table)

    # max_key_len = max(len(key) for key in env.keys())
    # dot_spacing = 6  # Minimum number of dots between key and value

    # print("\n.env Configuration:\n")
    # for key, value in env.items():
    #     dot_count = max(dot_spacing, 20 - len(key))  # Adjust for readability
    #     dots = '.' * dot_count
    #     print(f"{key} {dots} {value}")

def handle_config_edit(args):
    if not ENV_PATH.exists():
        logger.error(".env file not found.")
        return
    env = dotenv_values(ENV_PATH)
    if args.key not in env:
        logger.error(f"Key '{args.key}' not found in .env.")
        return
    set_key(str(ENV_PATH), args.key, args.value)
    logger.info(f"Updated '{args.key}' to '{args.value}' in .env.")

def handle_config_add(args):
    """Add a new key-value pair to the .env file, if it doesn't already exist."""
    env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}

    if args.key in env:
        logger.debug(f"Key '{args.key}' already exists. Use 'edit' to modify it.")
        console.print(f"[bright_yellow]Key '{args.key}' already exists. Use 'edit' to modify it.[/bright_yellow]")
        return

    with open(ENV_PATH, "a") as f:
        f.write(f"\n{args.key}={args.value}")
        logger.debug(f"Added {args.key} to .env file.")
        console.print(f"[bright-green]Added {args.key} to .env file.[/bright-green]")