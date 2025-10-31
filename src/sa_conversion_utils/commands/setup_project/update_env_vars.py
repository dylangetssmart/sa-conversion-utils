import os
from dotenv import load_dotenv, set_key
from rich.prompt import Prompt
from rich.console import Console
from rich.panel import Panel

console = Console()

def update_env_vars():
    """
    Update environment variables in the .env file based on the target system.
    """

    sql_server = Prompt.ask(f"Enter SQL Server name")
    source_db = Prompt.ask(f"Enter source database name")
    target_db = Prompt.ask(f"Enter SA database name")

    env_path = os.path.join(os.getcwd(), ".env")
    load_dotenv(dotenv_path=env_path)

    set_key(env_path, "SERVER", sql_server)
    set_key(env_path, "SOURCE_DB", source_db)
    set_key(env_path, "TARGET_DB", target_db)

    summary = f"""
        [green]SERVER[/green] = [cyan]{sql_server}[/cyan]
        [green]SOURCE_DB[/green] = [cyan]{source_db}[/cyan]
        [green]TARGET_DB[/green] = [cyan]{target_db}[/cyan]
        """
    
    console.print(
        Panel(
            summary.strip(),
            title="✅ .env Variables Updated",
            border_style="green",
            title_align="left"
        )
    )