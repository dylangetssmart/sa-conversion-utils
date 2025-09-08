import yaml
import logging

logger = logging.getLogger(__name__)

def load_yaml(file_path, console=None):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file {file_path}: {exc}")
        if console:
            console.print(f"[red]Error parsing YAML file {file_path}[/red]")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading YAML file {file_path}: {e}")
        if console:
            console.print(f"[red]Unexpected error loading YAML file {file_path}[/red]")
        return None
