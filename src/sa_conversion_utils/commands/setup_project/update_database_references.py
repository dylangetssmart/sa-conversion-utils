import argparse
import sys
import os
import re

from pathlib import Path
from rich.prompt import Confirm
from rich.tree import Tree
from rich.console import Console
from rich.panel import Panel

ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = ROOT / "scripts"
SHARED_DIR = SCRIPTS_DIR / "shared"
console = Console()

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
DEFAULT_SERVER = os.getenv("SERVER", "DEFAULT_SQL_SERVER")
DEFAULT_DB = os.getenv("TARGET_DB", "DEFAULT_DATABASE")


def get_legacy_systems():
    """Return a list of legacy systems (all subfolders in scripts/, excluding 'shared')."""
    return sorted(
        [p.name for p in SCRIPTS_DIR.iterdir() if p.is_dir() and p.name != "shared"]
    )


def update_database_references(target_system: str):
    """
    walk through all sql files in system directory
    and replace boilerplate database references with actual database names

    """
    target_dir = SCRIPTS_DIR / target_system
    if not target_dir.exists():
        console.print(f"❌ Legacy system folder not found: {target_dir}")
        sys.exit(1)

    console.print(f"🚀 Copying shared scripts into '{target_system}'...\n")

    # Define the search pattern (case-insensitive) and the replacement string
    # We use a raw string for the pattern for clarity.
    # The 'r' prefix in the pattern denotes a raw string.
    search_pattern = r"USE\s+\[SA\]"
    replacement_target = f"USE [{DEFAULT_DB}]"  # Use the desired final case

    # Iterate through all .sql files in the target system directory
    for sql_file in target_dir.rglob("*.sql"):
        try:
            with open(sql_file, "r", encoding="utf-8") as file:
                content = file.read()
        except IOError as e:
            console.print(f"⚠️ Could not read file {sql_file}: {e}")
            continue

        # Use re.sub() for case-insensitive replacement (re.IGNORECASE)
        # re.sub() handles ALL case variations of USE [SA] (e.g., Use [Sa], use [sa], etc.)
        updated_content = re.sub(
            search_pattern, replacement_target, content, flags=re.IGNORECASE
        )

        # Write back the updated content only if changes were made
        if updated_content != content:
            # This writes the content with the replacement applied,
            # but all other text retains its original case.
            with open(sql_file, "w", encoding="utf-8") as file:
                file.write(updated_content)
            console.print(f"✅ Updated database references in: {sql_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize migration scripts for a legacy system."
    )
    parser.add_argument(
        "--system",
        help="Legacy system to initialize (e.g., needles, trialworks)",
        choices=get_legacy_systems(),
    )
    args = parser.parse_args()

    systems = get_legacy_systems()

    if args.system:
        chosen = args.system
    else:
        # Interactive prompt
        console.print("Available legacy systems:")
        for i, sys_name in enumerate(systems, start=1):
            console.print(f"  {i}. {sys_name}")
        choice = input("\nSelect a system number: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(systems)):
            console.print("❌ Invalid selection.")
            sys.exit(1)
        chosen = systems[int(choice) - 1]

    update_database_references(chosen)


if __name__ == "__main__":
    main()
