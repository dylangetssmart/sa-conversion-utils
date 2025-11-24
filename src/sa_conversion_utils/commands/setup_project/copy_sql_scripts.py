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


def setup_parser(subparsers):
    copy_sql_scripts_parser = subparsers.add_parser("copy-sql-scripts", help="Copy SQL scripts from source to target directory.")   
    copy_sql_scripts_parser.add_argument(
        "script_dir", 
        type=Path, 
        help="The source directory containing the SQL scripts."
    )
    copy_sql_scripts_parser.add_argument(
        "target_dir", 
        type=Path, 
        help="The destination directory for the copied SQL scripts."
    )
    copy_sql_scripts_parser.set_defaults(func=copy_sql_scripts)


def handle_copy(source_file: Path, dest_file: Path):
    """
    Checks if the destination file exists (skips if it does) 
    and copies the source file otherwise, including error handling.
    """
    if dest_file.exists():
        print(f"  ⚠️  Skipping existing file: {dest_file}")
        return
    
    # Ensure the destination directory exists before copying
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(source_file, dest_file)
        print(f"  ✅ Copied: {dest_file}")
    except Exception as e:
        print(f"  ❌ Error copying {source_file.name}: {e}")


def copy_sql_scripts(script_dir: Path, target_dir: Path):
    """
    Copies all .sql files from the source directory and its immediate 
    subdirectories into corresponding subdirectories in the target directory.
    If the file already exists in the target, it is skipped.
    """

    # shared_dir = scripts_dir / "shared"
    # target_dir = scripts_dir / legacy_system
    
    print(f"🚀 Copying SQL scripts from '{script_dir}' to '{target_dir}'...")

    if not script_dir.exists() or not script_dir.is_dir():
        print(f"❌ Source directory not found: {script_dir}")
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)

    for item in script_dir.iterdir():
        if item.is_file() and item.suffix.lower() == ".sql":
            dest_file = target_dir / item.name
            handle_copy(item, dest_file)
            
        elif item.is_dir():
            source_subdir = item
            dest_subdir = target_dir / source_subdir.name
            dest_subdir.mkdir(parents=True, exist_ok=True)

            sql_files = list(source_subdir.glob("*.sql"))
            
            if not sql_files:
                continue

            print(f"\n📂 Processing subdirectory: {source_subdir.name}")
            for sql_file in sql_files:
                dest_file = dest_subdir / sql_file.name
                handle_copy(sql_file, dest_file)
            
    print("\n✅ Copy operation complete.")

def main():
    parser = argparse.ArgumentParser(
        description="Copy .sql scripts from a source directory to a target directory."
    )
    parser.add_argument(
        "script_dir", 
        type=Path, 
        help="The source directory containing the SQL scripts."
    )
    parser.add_argument(
        "target_dir", 
        type=Path, 
        help="The destination directory for the copied SQL scripts."
    )
    args = parser.parse_args()
    
    # Call the core function with paths from command-line arguments
    copy_sql_scripts(args.script_dir, args.target_dir)


if __name__ == "__main__":
    # Example usage when running from the command line:
    # python your_script_name.py /path/to/source /path/to/destination
    main()











    # for shared_subdir in shared_dir.iterdir():
    #     dest_subdir = target_dir / shared_subdir.name
    #     sql_files = list(shared_subdir.glob("*.sql"))

    #     if not shared_subdir.is_dir():
    #         continue

    #     if not sql_files:
    #         continue

    #     # Build the Rich Tree display
    #     tree = Tree(
    #         f"📂 [bold yellow]{shared_subdir}[/bold yellow]",
    #         guide_style="dim white",
    #     )

    #     for sql_file in sql_files:
    #         dest_file = dest_subdir / sql_file.name
    #         status = (
    #             "[yellow]skip existing[/yellow]"
    #             if dest_file.exists()
    #             else "[green]new file[/green]"
    #         )

    #         padded_name = (
    #             f"[cyan]{sql_file.name:<50}[/cyan]"  # Format with consistent padding
    #         )
    #         tree.add(f"{padded_name} {status}")

    #     console.print(
    #         Panel(
    #             tree, title=shared_subdir.name, border_style="blue", title_align="left"
    #         )
    #     )

    #     if Confirm.ask(f"Copy to [bold magenta]{dest_subdir}[/bold magenta]"):
    #         for sql_file in sql_files:
    #             dest_file = dest_subdir / sql_file.name

    #             if dest_file.exists():
    #                 console.print(
    #                     f"[yellow]  ⚠️   Skipping existing file: {dest_file}[/yellow]"
    #                     # f"[yellow]  ⚠️  Skipping existing file: {dest_file.relative_to(ROOT)}[/yellow]"
    #                 )
    #                 continue

    #             dest_file = target_dir / shared_subdir.name / sql_file.name
    #             dest_file.parent.mkdir(parents=True, exist_ok=True)
    #             shutil.copy2(sql_file, dest_file)
    #             console.print(
    #                 f"[green]  ✅  Copied: {dest_file}[/green]"
    #                 # f"[green]  ✅  Copied: {dest_file.relative_to(ROOT)}[/green]"
    #             )


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
