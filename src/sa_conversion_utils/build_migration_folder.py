import os
import shutil
import json

# Paths (adjust as needed)
GENERIC_SCRIPTS_DIR = "generic_scripts"
SOURCE_SYSTEMS_DIR = "source_systems"
DIST_DIR = "dist/scripts"

def load_manifest(folder):
    """Load the order of scripts from a manifest file or default to all .sql files sorted."""
    manifest_file = os.path.join(folder, "order.txt")  # Use .txt for simplicity
    if os.path.exists(manifest_file):
        with open(manifest_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    # Default to all SQL files in alphabetical order
    return sorted(f for f in os.listdir(folder) if f.endswith(".sql"))

def consolidate_scripts(source_system):
    """Consolidate generic and source-specific scripts into the dist folder."""
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)  # Clear the existing dist folder
    os.makedirs(DIST_DIR)

    script_sources = [
        (GENERIC_SCRIPTS_DIR, "generic"),
        (os.path.join(SOURCE_SYSTEMS_DIR, source_system), source_system),
    ]

    script_order = []
    for folder, label in script_sources:
        if os.path.exists(folder):
            scripts = load_manifest(folder)
            for script in scripts:
                src = os.path.join(folder, script)
                if os.path.exists(src):
                    script_order.append((src, script))

    # Copy scripts to dist folder in order
    for i, (src, script_name) in enumerate(script_order, start=1):
        dest = os.path.join(DIST_DIR, f"{i:03}_{script_name}")
        shutil.copyfile(src, dest)
        print(f"Added: {dest}")

if __name__ == "__main__":
    source_system = input("Enter the source system (e.g., SystemB): ").strip()
    consolidate_scripts(source_system)
    print(f"Scripts for {source_system} consolidated in '{DIST_DIR}'.")
