""" confirm.py
Prompts the user for confirmation to execute SQL sequence against the specified server and database.

Args:
    server (str): The server name.
    database (str): The database name.
    sequence (str): The SQL sequence to execute.

Returns:
    bool: True if the user confirms, False otherwise.
"""

from rich.console import Console

console = Console()

def confirm_execution(server: str, database: str, custom_msg: str) -> bool:
    # Rich styling for server and database
    server_str = f"[bold cyan]{server}[/bold cyan]"
    database_str = f"[bold magenta]{database}[/bold magenta]"
    
    message = (
        f"Are you sure you want to {custom_msg} "
        f"against {server_str}.{database_str}?"
    )

    # Confirmation prompt with rich styling
    confirmation = console.input(f"{message} (y/n): ").strip().lower()
        
    if confirmation == 'y':
        return True
    else:
        console.print("Operation canceled by the user.", style="bold red")
        return False