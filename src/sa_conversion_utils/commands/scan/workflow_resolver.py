import os
import argparse
import json
from pathlib import Path
from typing import List, Optional
from . import scan

# External dependencies used by this function
from rich.prompt import Confirm
from rich.console import Console

# Default location for the discovery file
WORKFLOWS_FILE = "workflows.json"


def resolve_workflow_path(workflow_segments: List[str], console: Console) -> Optional[Path]:
    """
    Loads workflows.json and resolves the workflow path segments into a full input directory path.
    
    Includes a user experience (UX) check to prompt the user to run the 'scan' command if 
    the workflows.json file is missing, and correctly loops to load the file afterward 
    if the scan is successful.
    
    Args:
        workflow_segments: A list of string segments representing the hierarchical path 
                           within the workflow structure (e.g., ['needles', 'convert']).
        console: The rich.console.Console object for printing messages and prompts.

    Returns:
        A Path object to the resolved input directory, or None if resolution fails 
        (e.g., file not found, JSON error, or path segment not found).
    """
    workflows_file_path = Path(WORKFLOWS_FILE)

    while True:
        if not workflows_file_path.exists():
            if Confirm.ask(f"[bold red]Error:[/bold red] Workflow file '{WORKFLOWS_FILE}' not found. Run 'sami scan' now?"):
                # Dynamically import and run scan (assuming relative import path is correct)
                try:
                    # Create a minimal args object required by the scan function
                    scan_args = argparse.Namespace()
                    
                    # Execute the scan function from the scan module
                    scan.scan(scan_args)
                    
                    # After successful scan, the file should now exist. Loop back to try and read it.
                    continue 
                except ImportError:
                    console.print("[bold red]Fatal Error:[/bold red] Cannot find or import the 'scan' module.")
                    return None
            else:
                # User declined to run scan
                return None
        
        # If the file exists (either initially or after a successful scan)
        try:
            with open(workflows_file_path, 'r') as f:
                workflow_data = json.load(f)
            break # Exit the loop, file loaded successfully

        except json.JSONDecodeError:
            console.print(f"[bold red]Error:[/bold red] Could not decode '{WORKFLOWS_FILE}'. Check file integrity.")
            return None
    
    # --- Logic for processing workflow_data (outside the loop) ---
    
    # 1. Determine the base path from where the scan was run
    # Assuming 'workflows.discovered.path' holds the root directory used during the scan
    try:
        base_scan_path = Path(workflow_data['workflows']['discovered']['path'])
    except KeyError:
        console.print("[bold red]Error:[/bold red] Could not find scan path in workflows.json structure.")
        return None
    
    # 2. Reconstruct the full path using the workflow segments
    resolved_path = base_scan_path
    
    # Construct the path by joining the base path and the segments
    for segment in workflow_segments:
        resolved_path = resolved_path / segment
        
    # Check if the resolved path actually exists
    if not resolved_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Resolved path does not exist: [yellow]{resolved_path}[/yellow]")
        console.print(f"[dim]Segments used: {workflow_segments}[/dim]")
        return None

    return resolved_path
