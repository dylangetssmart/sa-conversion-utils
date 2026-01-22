import os
import shutil
import argparse
from pathlib import Path
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.tree import Tree
import questionary

# Setup custom theme for consistent branding
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "step": "bold magenta",
    "banner": "bold blue"

})

console = Console(theme=custom_theme)

# ASCII Art Banner
BANNER_ART = r"""
 ________  ________  ________   ___      ___ _______   ________  ________  ___  ________  ________           
|\   ____\|\   __  \|\   ___  \|\  \    /  /|\  ___ \ |\   __  \|\   ____\|\  \|\   __  \|\   ___  \         
\ \  \___|\ \  \|\  \ \  \\ \  \ \  \  /  / | \   __/|\ \  \|\  \ \  \___|\ \  \ \  \|\  \ \  \\ \  \        
 \ \  \    \ \  \\\  \ \  \\ \  \ \  \/  / / \ \  \_|/_\ \   _  _\ \_____  \ \  \ \  \\\  \ \  \\ \  \       
  \ \  \____\ \  \\\  \ \  \\ \  \ \    / /   \ \  \_|\ \ \  \\  \\|____|\  \ \  \ \  \\\  \ \  \\ \  \      
   \ \_______\ \_______\ \__\\ \__\ \__/ /     \ \_______\ \__\\ _\ ____\_\  \ \__\ \_______\ \__\\ \__\     
    \|_______|\|_______|\|__| \|__|\|__|/       \|_______|\|__|\|__|\_________\|__|\|_______|\|__| \|__|     
                                                                   \|_________|                              
                                                                                                             
 ________  _________  ________  ________  _________  _______   ________          ___  __    ___  _________   
|\   ____\|\___   ___\\   __  \|\   __  \|\___   ___\\  ___ \ |\   __  \        |\  \|\  \ |\  \|\___   ___\ 
\ \  \___|\|___ \  \_\ \  \|\  \ \  \|\  \|___ \  \_\ \   __/|\ \  \|\  \       \ \  \/  /|\ \  \|___ \  \_| 
 \ \_____  \   \ \  \ \ \   __  \ \   _  _\   \ \  \ \ \  \_|/_\ \   _  _\       \ \   ___  \ \  \   \ \  \  
  \|____|\  \   \ \  \ \ \  \ \  \ \  \\  \|   \ \  \ \ \  \_|\ \ \  \\  \|       \ \  \\ \  \ \  \   \ \  \ 
    ____\_\  \   \ \__\ \ \__\ \__\ \__\\ _\    \ \__\ \ \_______\ \__\\ _\        \ \__\\ \__\ \__\   \ \__\
   |\_________\   \|__|  \|__|\|__|\|__|\|__|    \|__|  \|_______|\|__|\|__|        \|__| \|__|\|__|    \|__|
   \|_________|                                                                                              
"""

def setup_init_command(subparsers):
    """Adds the 'init' command to the main argparse parser."""
    parser = subparsers.add_parser('init', help='Initialize a new migration project from template.')
    parser.set_defaults(func=run_init)

def select_shared_items(shared_dir):
    """Allows user to select specific files/folders from the shared directory using checkboxes."""
    items = sorted([item for item in shared_dir.iterdir() if not item.name.startswith('.')])
    
    if not items:
        return []

    # Prepare choices for questionary
    choices = [
        questionary.Choice(
            title=f"{item.name} ({'Folder' if item.is_dir() else 'File'})",
            value=item
        ) for item in items
    ]

    console.print("\n[info]Use arrow keys to move, Space to select, and Enter to confirm.[/info]")
    
    selected_items = questionary.checkbox(
        "Select Shared Items to Copy:",
        choices=choices,
        style=questionary.Style([
            ('checkbox-selected', 'fg:green bold'),
            ('selected', 'fg:cyan'),
            ('highlighted', 'fg:cyan bold'),
            ('answer', 'fg:green bold'),
        ])
    ).ask()

    # If user cancels or selects none, selected_items will be None or empty list
    return selected_items if selected_items else []

def generate_tree_from_paths(paths, title="Selected Items", base_path=None):
    """Creates a Rich Tree object from a list of Path objects."""
    tree = Tree(f"[bold yellow]{title}[/bold yellow]")
    for path in paths:
        # If base_path is provided, we show the relative destination path
        display_name = path.name
        if base_path:
            try:
                display_name = str(path.relative_to(base_path.parent.parent))
            except ValueError:
                display_name = path.name

        if path.is_dir():
            branch = tree.add(f"[bold cyan]📂 {display_name}[/bold cyan]")
            # Add a few children if it's a directory to show structure
            try:
                # Use a small sample to avoid huge trees
                children = sorted(list(path.iterdir()))
                for child in children:
                    branch.add(f"[dim]{child.name}[/dim]")
                # if len(children) > 5:
                #     branch.add("[dim]...[/dim]")
            except (PermissionError, FileNotFoundError):
                branch.add("[red]Not accessible[/red]")
        else:
            tree.add(f"[white]📄 {display_name}[/white]")
    return tree

def run_init(args):
    """Executes the initialization workflow with a Rich UI and summary reporting."""
    console.print(Panel.fit(f"[banner]{BANNER_ART}[/banner]", subtitle="https://github.com/SmartAdvocate/conversion-starter-kit"))
    # console.print(Panel.fit("[bold blue]Project Initialization[/bold blue]", subtitle="Starter Kit v1.1"))
    
    root_dir = Path.cwd()
    summary_data = {
        "removed_folders": [],
        "env_vars": {},
        "shared_copied": [],
        "replacements": {},
        "files_updated_count": 0
    }
    
    # 1. Select Source System
    excluded_folders = {'.git', '.github', 'shared', '__pycache__', 'venv', '.venv', 'backups', '.vs', 'logs'}
    systems = sorted([d.name for d in root_dir.iterdir() if d.is_dir() and d.name not in excluded_folders])
    
    if not systems:
        console.print("[error]Error:[/error] No system folders found in the current directory.")
        return

    console.print("\n[step]Step 1: Select Source System[/step]")
    
    # Replaced IntPrompt with questionary.select for a better UX
    selection = questionary.select(
        "Which source system are you migrating from?",
        choices=systems,
        style=questionary.Style([
            ('selected', 'fg:cyan bold'),
            ('highlighted', 'fg:cyan bold'),
            ('answer', 'fg:green bold'),
        ])
    ).ask()

    if not selection:
        console.print("[error]Initialization cancelled.[/error]")
        return

    console.print(f"Selected: [success]{selection}[/success]\n")

    # Cleanup: Remove other system folders with persistent progress
    folders_to_remove = [s for s in systems if s != selection]
    if folders_to_remove:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Cleaning up template directories...", total=len(folders_to_remove))
            
            for system in folders_to_remove:
                system_path = root_dir / system
                try:
                    shutil.rmtree(system_path)
                    progress.console.print(f"[success]✔[/success] Removed {system}")
                    summary_data["removed_folders"].append(system)
                except Exception as e:
                    progress.console.print(f"[warning]⚠[/warning] Could not delete {system}: {e}")
                
                progress.advance(task)

    # 2. Configure .env
    console.print("\n[step]Step 2: Database Configuration[/step]")
    sql_server = Prompt.ask("Enter [bold]SQL Server Name[/bold]")
    source_db = Prompt.ask("Enter [bold]Source Database Name[/bold]")
    target_db = Prompt.ask("Enter [bold]Target (SA) Database Name[/bold]")

    summary_data["env_vars"] = {
        "SOURCE_SYSTEM": selection,
        "SQL_SERVER": sql_server,
        "SOURCE_DB": source_db,
        "TARGET_DB": target_db
    }

    env_content = [f"{k}={v}" for k, v in summary_data["env_vars"].items()]
    env_path = root_dir / ".env"
    with open(env_path, "w") as f:
        f.write("\n".join(env_content))
    
    console.print(f"[success]✔[/success] Created .env file\n")

    # 3. Copy Shared Scripts
    console.print("[step]Step 3: Selective Copy of Shared Scripts[/step]")
    shared_dir = root_dir / "shared"
    target_conversion_dir = root_dir / selection / "conversion"
    
    if not target_conversion_dir.exists():
        target_conversion_dir.mkdir(parents=True, exist_ok=True)

    if shared_dir.exists():
        selected_items = select_shared_items(shared_dir)
        
        if selected_items:
            copied_paths = []
            with Progress(console=console) as progress:
                task = progress.add_task("Copying selected items...", total=len(selected_items))
                for item in selected_items:
                    dest = target_conversion_dir / item.name
                    try:
                        if item.is_dir():
                            if dest.exists():
                                shutil.rmtree(dest)
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)
                        
                        summary_data["shared_copied"].append(item.name)
                        copied_paths.append(dest)
                        progress.advance(task)
                    except Exception as e:
                        console.print(f"[error]Error copying {item.name}:[/error] {e}")

            # Show the tree of copied items with their new paths
            console.print("")
            copy_tree = generate_tree_from_paths(copied_paths, title=f"Successfully copied to {selection}/conversion/", base_path=target_conversion_dir)
            console.print(copy_tree)
            console.print("")
        else:
            console.print("[info]No shared items selected for copying.[/info]")
    else:
        console.print("[warning]Warning:[/warning] 'shared' directory not found. Skipping.")

    # 4. Update Database References
    console.print("\n[step]Step 4: Updating Database References[/step]")
    
    summary_data["replacements"] = {
        "{SOURCE_DB}": f"[{source_db}]",
        "{TARGET_DB}": f"[{target_db}]"
    }
    
    console.print("[info]Replacing placeholders in SQL scripts:[/info]")
    for placeholder, val in summary_data["replacements"].items():
        console.print(f"  • {placeholder} [bold cyan]→[/bold cyan] {val}")
    console.print("")

    sql_files_to_update = list((root_dir / selection).rglob("*.sql"))
    
    if sql_files_to_update:
        with Progress(console=console, transient=True) as progress:
            task = progress.add_task("Updating SQL placeholders...", total=len(sql_files_to_update))
            for file_path in sql_files_to_update:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    original_content = content
                    for placeholder, value in summary_data["replacements"].items():
                        content = content.replace(placeholder, value)
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        summary_data["files_updated_count"] += 1
                        console.print(f"[success]✔[/success] Updated references in: [dim]{file_path.relative_to(root_dir)}[/dim]")
                    
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[error]Error processing {file_path.name}:[/error] {e}")
    
    # Final Summary Construction
    summary_table = Table(show_header=False, box=None, padding=(0, 1))
    summary_table.add_column("Key", style="bold magenta")
    summary_table.add_column("Value")

    summary_table.add_row("Source System:", selection)
    summary_table.add_row("Cleanup:", f"Removed {len(summary_data['removed_folders'])} folders")
    
    env_summary = ", ".join([f"{k}={v}" for k, v in summary_data["env_vars"].items()])
    summary_table.add_row("Config:", env_summary)
    
    shared_summary = f"Copied {len(summary_data['shared_copied'])} items"
    summary_table.add_row("Shared Scripts:", shared_summary)
    
    replacements_summary = f"{summary_data['files_updated_count']} files modified"
    summary_table.add_row("SQL Replacements:", replacements_summary)

    console.print("\n")
    console.print(Panel(
        summary_table,
        title="[bold green]Initialization Complete[/bold green]",
        border_style="green",
        expand=False
    ))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    setup_init_command(subparsers)
    import sys
    if len(sys.argv) == 1:
        args = parser.parse_args(['init'])
    else:
        args = parser.parse_args()
        
    if hasattr(args, 'func'):
        args.func(args)