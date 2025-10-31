import argparse
import shutil
import sys
from pathlib import Path
from rich.prompt import Confirm
from rich.tree import Tree
from rich.console import Console
from rich.panel import Panel

from .get_legacy_systems import get_legacy_systems

# ROOT = Path(__file__).parent.parent
# SCRIPTS_DIR = Path("scripts")
# SHARED_DIR = SCRIPTS_DIR / "shared"
console = Console()


# def setup_parser(subparsers):
#     copy_shared_scripts_parser = subparsers.add_parser(
#         "copy-shared-scripts", help="Copy shared scripts into legacy system"
#     )
#     copy_shared_scripts_parser.set_defaults(func=main)
#     copy_shared_scripts_parser.add_argument(
#         "--system",
#         help="Legacy system to initialize (e.g., needles, trialworks)",
#         choices=get_legacy_systems(SCRIPTS_DIR),
#     )


def copy_shared_scripts(scripts_dir, legacy_system: str):
    """Copy shared scripts into the selected legacy system."""
    shared_dir = scripts_dir / "shared"
    target_dir = scripts_dir / legacy_system
    
    if not target_dir.exists():
        console.print(f"❌ Legacy system folder not found: {target_dir}")
        sys.exit(1)

    console.print(f"🚀 Copying shared scripts into '{legacy_system}'...\n")

    for shared_subdir in shared_dir.iterdir():
        dest_subdir = target_dir / shared_subdir.name
        sql_files = list(shared_subdir.glob("*.sql"))

        if not shared_subdir.is_dir():
            continue

        if not sql_files:
            continue

        # Build the Rich Tree display
        tree = Tree(
            f"📂 [bold yellow]{shared_subdir}[/bold yellow]",
            guide_style="dim white",
        )

        for sql_file in sql_files:
            dest_file = dest_subdir / sql_file.name
            status = (
                "[yellow]skip existing[/yellow]"
                if dest_file.exists()
                else "[green]new file[/green]"
            )

            padded_name = (
                f"[cyan]{sql_file.name:<50}[/cyan]"  # Format with consistent padding
            )
            tree.add(f"{padded_name} {status}")

        console.print(
            Panel(
                tree, title=shared_subdir.name, border_style="blue", title_align="left"
            )
        )

        if Confirm.ask(f"Copy to [bold magenta]{dest_subdir}[/bold magenta]"):
            for sql_file in sql_files:
                dest_file = dest_subdir / sql_file.name

                if dest_file.exists():
                    console.print(
                        f"[yellow]  ⚠️   Skipping existing file: {dest_file}[/yellow]"
                        # f"[yellow]  ⚠️  Skipping existing file: {dest_file.relative_to(ROOT)}[/yellow]"
                    )
                    continue

                dest_file = target_dir / shared_subdir.name / sql_file.name
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sql_file, dest_file)
                console.print(
                    f"[green]  ✅  Copied: {dest_file}[/green]"
                    # f"[green]  ✅  Copied: {dest_file.relative_to(ROOT)}[/green]"
                )


# def main():
#     parser = argparse.ArgumentParser(
#         description="Copy shared migration scripts into legacy system folder."
#     )
#     parser.add_argument(
#         "--system",
#         help="Legacy system to initialize (e.g., needles, trialworks)",
#         choices=get_legacy_systems(SCRIPTS_DIR),
#     )
#     args = parser.parse_args()

#     systems = get_legacy_systems(SCRIPTS_DIR)

#     if args.system:
#         chosen = args.system
#     else:
#         console.print("Available legacy systems:")
#         for i, sys_name in enumerate(systems, start=1):
#             console.print(f"  {i}. {sys_name}")
#         choice = input("\nSelect a system number: ").strip()
#         if not choice.isdigit() or not (1 <= int(choice) <= len(systems)):
#             console.print("❌ Invalid selection.")
#             sys.exit(1)
#         chosen = systems[int(choice) - 1]

#     copy_shared_scripts(chosen)


# if __name__ == "__main__":
#     main()
