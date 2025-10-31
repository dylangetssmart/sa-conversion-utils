from pathlib import Path


def get_legacy_systems(SCRIPTS_DIR: Path):
    """Return a list of legacy systems (all subfolders in scripts/, excluding 'shared')."""
    return sorted(
        [p.name for p in SCRIPTS_DIR.iterdir() if p.is_dir() and p.name != "shared"]
    )
