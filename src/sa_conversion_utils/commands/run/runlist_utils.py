import logging
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

# --- CONFIGURATION CONSTANT ---
# This is the directory that holds all project folders containing runlists (e.g., 'scripts/needles')
RUNLIST_BASE_DIR = Path("scripts")
# ------------------------------

logger = logging.getLogger('run') # Assuming 'run' logger is configured in run_command.py

def load_scripts_from_runlist(runlist_path: Path, group_name: Optional[str]) -> List[Path]:
    """ 
    Reads the runlist file, resolves paths, validates scripts, and optionally filters by group.
    The runlist file can contain INI-style group headers (e.g., [reset]).
    """
    scripts: List[Path] = []
    logger.debug(f"Parsing runlist file: {runlist_path}, Group: {group_name}")
    
    try:
        with open(runlist_path, 'r') as f:
            # Read all non-commented, non-empty lines
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logger.error(f"Runlist file not found: {runlist_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading runlist file {runlist_path}: {e}")
        return []
        
    runlist_dir = runlist_path.parent
    
    # --- Group-based Parsing ---
    if group_name:
        target_header = f"[{group_name}]"
        in_target_group = False
        
        for i, line in enumerate(lines, 1):
            if line.startswith('[') and line.endswith(']'):
                # Found a new header
                if line == target_header:
                    in_target_group = True
                    logger.debug(f"Found target group: {target_header}. Starting collection.")
                elif in_target_group:
                    # Found the end of the target group (next header)
                    logger.debug(f"Reached end of target group: {line}. Stopping collection.")
                    break
                continue
            
            # Collect script paths only when inside the target group and line is not empty
            if in_target_group and line:
                script_path = runlist_dir / line
                
                if not script_path.is_file() or not script_path.name.lower().endswith(".sql"):
                    logger.error(f"Runlist line {i}: '{line}' in group '{group_name}' is not a valid SQL script path. Skipping.")
                    continue
                    
                scripts.append(script_path.resolve()) # Store the absolute path
                
        if not scripts:
             logger.error(f"Group '{group_name}' not found or contains no valid scripts in the runlist.")
             
    # --- Full File Parsing (No Group Specified) ---
    else:
        # Load all valid lines, ignoring headers, maintaining sequential order
        for i, line in enumerate(lines, 1):
            if line.startswith('[') and line.endswith(']'):
                continue # Skip section headers when no group is specified
                
            script_path = runlist_dir / line
            
            if not script_path.is_file() or not script_path.name.lower().endswith(".sql"):
                logger.error(f"Runlist line {i}: '{line}' is not a valid SQL script path. Skipping.")
                continue
                
            scripts.append(script_path.resolve())
            
    return scripts

def collect_scripts_from_dir(input_dir: Path) -> List[Path]:
    """ Scans the input directory for SQL files, sorts them, and returns absolute paths. """
    # logger.debug(f"Scanning input directory for SQL files: {input_dir}")
    
    if not input_dir.is_dir():
        logger.error(f"Input directory '{input_dir}' does not exist or is not a directory.")
        return []
        
    # Collect, filter, and sort files by name
    scripts = [f for f in input_dir.iterdir() if f.is_file() and f.name.lower().endswith(".sql")]
    scripts.sort(key=lambda p: p.name)
    
    # Return a list of absolute paths
    return [s.resolve() for s in scripts]

def resolve_runlist_path(runlist_input: str) -> Optional[Path]:
    """
    Resolves the runlist input string (either a direct path or a project name)
    to a fully qualified Path object, respecting the naming conventions.
    """
    input_path = Path(runlist_input)

    # 1. Check if input is a direct, valid path
    if input_path.is_file():
        return input_path.resolve()

    # 2. Check for conventional naming inside the project directory
    project_name = runlist_input.lower()
    project_dir = RUNLIST_BASE_DIR / project_name
    
    if not project_dir.is_dir():
        logger.error(f"Project directory '{project_dir}' does not exist for runlist input '{runlist_input}'.")
        return None

    # Define prioritized search patterns
    search_patterns = [
        f"{project_name}_run_list.txt",
        f"{project_name}_runlist.txt",
        "*.run_list.txt",
        "*.runlist.txt",
        "runlist.txt",
    ]

    for pattern in search_patterns:
        # Use glob to find files matching the pattern within the project directory
        matches = list(project_dir.glob(pattern))
        
        # We only want to match a single, unique file per pattern check
        if len(matches) == 1:
            return matches[0].resolve()

    # If no file was found using any of the conventions
    return None

def display_runlist_groups(runlist_path: Path, console: Console):
    """ Reads the runlist and displays its groups and scripts using a rich Tree. """
    try:
        with open(runlist_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        console.print(f"[bold red]Error reading runlist:[/bold red] {e}")
        return

    tree = Tree(
        f"[bold blue]Runlist: {runlist_path.name}[/bold blue] [dim]({runlist_path.parent.name})[/dim]",
        guide_style="cyan"
    )
    
    runlist_dir = runlist_path.parent
    current_group_node = None
    group_count = 0
    script_count = 0
    
    # Add a default 'No Group' node for scripts at the file's root
    default_node = tree.add("[bold white]• No Group / Root Scripts[/bold white]")
    in_default_group = True

    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            # Found a header, this ends the 'No Group' section
            in_default_group = False 
            
            group_name = line[1:-1]
            current_group_node = tree.add(f"[bold yellow]Group: {group_name}[/bold yellow]")
            group_count += 1
            continue
        
        # If we have a line that isn't a header or a comment/empty:
        if line:
            script_path = runlist_dir / line
            
            # Determine which node to attach the script to
            target_node = current_group_node if current_group_node and not in_default_group else default_node

            # Check if file exists and set style
            if script_path.is_file():
                status_color = "green"
                status_icon = "✓"
                script_count += 1
            else:
                status_color = "red"
                status_icon = "✗"
                
            target_node.add(f"[{status_color}]{status_icon} [/][dim white]{line}[/dim white]")
            
    # Remove the default node if no scripts were found there and no groups were present
    if not group_count and not default_node.children:
         tree.remove(default_node)
         tree.add("[dim]No scripts or group definitions found.[/dim]")
    
    console.print(tree)