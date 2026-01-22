# Standard Library Imports
import os
import subprocess
import tkinter as tk
import argparse
import logging
import glob
from pathlib import Path
from dotenv import load_dotenv

# Third Party Imports
from tkinter import filedialog
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.text import Text

# Global Constants
logger = logging.getLogger(__name__)
console = Console()

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
DEFUALT_SERVER = os.getenv("SERVER")
DEFAULT_DB = os.getenv("TARGET_DB")
SQL_REMOTE_PATH_PREFIX = os.getenv("SQL_REMOTE_PATH_PREFIX")

# Setup default backup directory
backup_dir_in_cwd = os.path.join(os.getcwd(), "backups")
DEFAULT_BACKUP_DIR = backup_dir_in_cwd if os.path.isdir(backup_dir_in_cwd) else os.path.join(os.getcwd(), "backups")


def find_most_recent_backup(directory, search_term):
    """
    Searches for the most recent .bak file in the directory that contains the search_term.
    """
    if not os.path.isdir(directory):
        return None
    
    # Get all .bak files
    files = glob.glob(os.path.join(directory, "*.bak"))
    
    # Filter by search term (case-insensitive)
    matches = [f for f in files if search_term.lower() in os.path.basename(f).lower()]
    
    if not matches:
        return None
    
    # Return the file with the latest modification time
    return max(matches, key=os.path.getmtime)


def restore(args: argparse.Namespace):
    server = args.server
    database = args.database
    backup_dir = args.backup_dir
    search_pattern = args.pattern

    if not server or not database:
        logger.error("Missing Server or Database arguments")
        console.print("[red]Error: Server and Database must be specified.[/red]")
        return

    backup_file = None

    # 1. Try to find file by pattern if provided (e.g., 'sami restore imp')
    if search_pattern:
        backup_file = find_most_recent_backup(backup_dir, search_pattern)
        if not backup_file:
            console.print(f"[yellow]No match for '{search_pattern}' in {backup_dir}. Opening file selector...[/yellow]")

    # 2. Fallback to File Dialog if no pattern or no match found
    if not backup_file:
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        backup_file = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("SQL Backup files", "*.bak")],
            initialdir=backup_dir,
        )

    if not backup_file:
        console.print("[red]Restore cancelled: No file selected.[/red]")
        return

    # CRITICAL: Convert to absolute path to prevent SQL Server from 
    # prefixing its own default backup path (e.g., E:\SADB\...)
    backup_file = os.path.abspath(backup_file)

    # Handle path translation if SQL Server sees the drive/folder differently
    sql_path = backup_file
    if SQL_REMOTE_PATH_PREFIX:
        filename = os.path.basename(backup_file)
        sql_path = os.path.join(SQL_REMOTE_PATH_PREFIX, filename)

    # Prettier, Succinct Confirmation UI
    confirmation_text = Text.assemble(
        ("Target: ", "bold"), (f"{server}.{database}\n", "magenta"),
        ("Source: ", "bold"), (f"{os.path.basename(backup_file)}", "cyan")
    )
    
    if SQL_REMOTE_PATH_PREFIX:
        confirmation_text.append("\nSQL-Engine Path: ", style="bold")
        confirmation_text.append(f"{sql_path}", style="dim")

    console.print(Panel(confirmation_text, title="[bold yellow]Confirm Restore[/bold yellow]", expand=False))

    if not Confirm.ask("[bold red]Proceed with overwrite?[/bold red]"):
        console.print("[yellow]Operation aborted by user.[/yellow]")
        return

    # Execution phase
    try:
        # 1. Single User Mode
        console.print(f"\n[bold blue]→[/bold blue] Setting [magenta]{database}[/magenta] to SINGLE_USER...")
        subprocess.run([
            "sqlcmd", "-S", server, "-Q", 
            f"ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;",
            "-b", "-d", "master"
        ], check=True, capture_output=True)

        # 2. Restore
        console.print(f"[bold blue]→[/bold blue] Restoring from [cyan]{os.path.basename(backup_file)}[/cyan]...")
        subprocess.run([
            "sqlcmd", "-S", server, "-Q", 
            f"RESTORE DATABASE [{database}] FROM DISK='{sql_path}' WITH REPLACE, RECOVERY;",
            "-b", "-d", "master"
        ], check=True, capture_output=True)

        # 3. Multi User Mode
        console.print(f"[bold blue]→[/bold blue] Setting [magenta]{database}[/magenta] to MULTI_USER...")
        subprocess.run([
            "sqlcmd", "-S", server, "-Q", 
            f"ALTER DATABASE [{database}] SET MULTI_USER;",
            "-b", "-d", "master"
        ], check=True, capture_output=True)

        console.print(f"\n[bold green]SUCCESS:[/bold green] {database} has been restored.")

    except subprocess.CalledProcessError as e:
        # Limit error output to be reasonable
        raw_output = (e.stdout or b'').decode() + (e.stderr or b'').decode()
        lines = [line.strip() for line in raw_output.split('\n') if line.strip()]
        
        if len(lines) > 10:
            truncated = lines[:4] + ["... [output truncated] ..."] + lines[-4:]
            output = "\n".join(truncated)
        else:
            output = "\n".join(lines)

        console.print(f"\n[bold red]RESTORE FAILED[/bold red]\n{output}")
        
        # Cleanup: Attempt to set back to multi-user so DB isn't stuck
        subprocess.run(["sqlcmd", "-S", server, "-Q", f"ALTER DATABASE [{database}] SET MULTI_USER;"], capture_output=True)
    finally:
        logger.info(f"Restore operation finished for {database}")


def setup_parser(subparsers):
    """
    Configures the parser for the 'restore' subcommand.
    """
    restore_parser = subparsers.add_parser("restore", help="Restore a database from a backup file.")
    
    # Positional argument for pattern matching: 'sami restore imp'
    restore_parser.add_argument(
        "pattern",
        nargs="?",
        help="Search pattern to find a backup file (e.g., 'imp')"
    )
    
    restore_parser.add_argument(
        "-s",
        "--server",
        default=DEFUALT_SERVER,
        help="SQL Server")
    restore_parser.add_argument(
        "-d",
        "--database",
        default=DEFAULT_DB,
        help="Database to restore"
    )
    restore_parser.add_argument(
        "--backup-dir",
        default=DEFAULT_BACKUP_DIR,
        help="Directory where backup files are stored",
    )
    restore_parser.set_defaults(func=restore)