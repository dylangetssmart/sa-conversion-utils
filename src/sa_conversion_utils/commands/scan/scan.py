import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from rich.console import Console
from rich.prompt import Confirm
from rich.tree import Tree
from ...logging.logger_config import logger_config

console = Console()
logger = logger_config(name='scan', log_file="scan.log", level=logging.INFO, rich_console=console)

def discover_sql_scripts(root_dir: str) -> Dict:
    """
    Recursively scan directory for SQL scripts and build workflow structure.
    Groups scripts by directory structure and stores the script count at the 
    most specific directory level.
    """
    workflows: Dict[str, Any] = {}
    root_path = Path(root_dir)

    # Find all SQL files and count them per directory path
    dir_counts: Dict[Path, int] = {}
    folders_with_sql = set()
    
    for sql_file in root_path.rglob('*.sql'):
        dir_path = sql_file.parent
        dir_counts[dir_path] = dir_counts.get(dir_path, 0) + 1
        folders_with_sql.add(dir_path)
    
    if not dir_counts:
        return workflows

    # Build workflow structure
    for dir_path in folders_with_sql:
        try:
            # Get the path relative to the root scan directory
            relative_path = dir_path.relative_to(root_path)
            parts = relative_path.parts
        except ValueError:
            continue
            
        if not parts:
            # Handle scripts found directly in the root directory
            workflow_name = 'ROOT_WORKFLOW' 
            current_parts = []
        else:
            # Use first level as workflow name
            workflow_name = parts[0]
            current_parts = parts[1:]
        
        if workflow_name not in workflows:
            workflows[workflow_name] = {}
            
        current = workflows[workflow_name]
        
        # Traverse or create nested structure
        for part in current_parts:
            if part not in current:
                current[part] = {} 
            current = current[part]

        # Place the script count at the deepest level where the scripts were found
        current['scripts'] = dir_counts.get(dir_path, 0)

    return workflows


def save_workflows(workflows: Dict, output_file: str):
    """
    Save discovered workflows to JSON file.
    """
    workflow_data = {
        "workflows": {
            "discovered": {
                "timestamp": datetime.now().isoformat(),
                "path": os.getcwd()
            },
            "structure": workflows
        }
    }

    if os.path.dirname(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(workflow_data, f, indent=2)
    
    logger.info(f"Workflows saved to [bold green]{output_file}[/bold green]")


# --- NEW HELPER FOR RICH TREE ---
def build_rich_tree(parent_tree: Tree, structure: Dict):
    """
    Recursively build a rich.tree.Tree structure from the workflow dictionary.
    """
    
    # Only iterate over sub-dictionaries (folders), ignoring the 'scripts' count
    folder_items = {k: v for k, v in structure.items() if isinstance(v, dict)}
    
    for name, info in sorted(folder_items.items()):
        
        # Get the script count for the current directory
        script_count = info.get("scripts", 0)

        # Determine the label for the node
        label = f"[cyan]{name}[/cyan]"
        
        # Add script count if scripts are present in this folder
        if script_count > 0:
            label += f" ([bold magenta]{script_count} SQL[/bold magenta])"
            
        # Create a new node in the tree
        node = parent_tree.add(label)
        
        # Recursively process child folders
        build_rich_tree(node, info)


def scan(args):
    """
    Scan directory structure and create workflows.json, using rich.tree for 
    readable output.
    """
    logger.info("Starting directory scan...")
    
    # Discover SQL scripts and their organization
    workflows = discover_sql_scripts(os.getcwd())
    
    if not workflows:
        logger.warning("No SQL scripts found in the current directory structure")
        return

    console.print("\n" + "="*50)
    console.print("[bold yellow]🚀 Discovered SQL Workflows[/bold yellow]")
    console.print("="*50 + "\n")

    # Create a main Tree object to hold all workflows
    main_tree = Tree(
        f"[bold green]Scanning '{os.getcwd()}'[/bold green]",
        guide_style="dim white",
    )

    # Add each top-level workflow as a separate branch
    for workflow_name, workflow_content in workflows.items():
        
        # Get script count for the top level folder itself
        top_level_script_count = workflow_content.get("scripts", 0)
        
        label = f"📂 [bold yellow]{workflow_name}[/bold yellow]"
        if top_level_script_count > 0:
            label += f" ([bold magenta]{top_level_script_count} SQL[/bold magenta])"

        # Add the top-level node with a newline before it for separation
        workflow_root_node = main_tree.add(label, highlight=True)
        
        # Build the rest of the tree structure from the content
        build_rich_tree(workflow_root_node, workflow_content)
        
    # Print the final, consolidated tree
    console.print(main_tree)
    console.print("\n" + "="*50 + "\n")

    if Confirm.ask("[bold]✅ Structure Discovery Complete. Save discovered structure?[/bold]"):
        save_workflows(workflows, "workflows.json")
        logger.info("Directory scan complete")
        
    else:
        logger.info("Save cancelled by user.")


def setup_parser(subparsers):
    """Configure the parser for the 'scan' subcommand."""
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan directory structure and create workflows.json"
    )
    scan_parser.set_defaults(func=scan)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A CLI tool for managing SQL workflows.")
    subparsers = parser.add_subparsers(title="Available commands", dest="command")
    
    setup_parser(subparsers)
    
    # Note: To run this, you would typically use: 
    # args = parser.parse_args()
    # if hasattr(args, 'func'):
    #     args.func(args)
    
    # Since we can't run the full command line interface, 
    # the script is left here for structural reference.
    # To test, call scan() directly if you have a filesystem accessible.