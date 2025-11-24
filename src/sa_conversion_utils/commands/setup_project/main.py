from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
import argparse
import sys

from .get_legacy_systems import get_legacy_systems
from .copy_sql_scripts import copy_shared_scripts
from .update_database_references import update_database_references
from .update_env_vars import update_env_vars

ROOT = Path(__file__).parent.parent
# SCRIPTS_DIR = ROOT / "scripts"
SCRIPTS_DIR = Path("scripts")
SHARED_DIR = SCRIPTS_DIR / "shared"
console = Console()


def setup_parser(subparsers):
    seutp_project_parser = subparsers.add_parser("setup-project", help="Setup project")
    seutp_project_parser.set_defaults(func=setup_project)
    seutp_project_parser.add_argument(
        "--system",
        help="Legacy system to initialize (e.g., needles, trialworks)",
        choices=get_legacy_systems(SCRIPTS_DIR),
    )


def setup_project(args): # Function now accepts 'args' from argparse

    # --- 1. Determine Target System ---
    if args.system:
        legacy_system = args.system
    else:
        # Interactive prompt for system selection
        system_choices = get_legacy_systems(SCRIPTS_DIR)
        if not system_choices:
            console.print("❌ No legacy system folders found in 'scripts/' besides 'shared'.")
            sys.exit(1)
        try:
            legacy_system = Prompt.ask(
                "Select legacy system", 
                choices=system_choices, 
                default=system_choices[0]
            )
        except KeyboardInterrupt:
            console.print("\nSetup cancelled.")
            sys.exit(0)

    console.print(
        Panel(
            f"Starting setup process for legacy system: [bold yellow]{legacy_system}[/bold yellow]",
            title="✨ Project Setup",
            border_style="green",
        )
    )

    # --- Step 1: Update .env variables ---
    if Confirm.ask(f"\n[bold]1. Set .env variables[/bold]?"):
        update_env_vars()

    # --- Step 2: Copy shared scripts ---
    if Confirm.ask(f"\n[bold]2. Copy shared scripts[/bold] into '{legacy_system}'?"):
        copy_shared_scripts(SCRIPTS_DIR, legacy_system)

    # --- Step 3: Update database references ---
    if Confirm.ask(f"\n[bold]3. Update database references[/bold] in '{legacy_system}' scripts?"):
        update_database_references(legacy_system)

    console.print(f"\n[bold green]🎉 Setup Complete for {legacy_system}![/bold green]")