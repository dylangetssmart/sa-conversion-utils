import os
import logging

# Highrise functions
from .parse_notes_tasks_emails import parse_notes_tasks_emails

# Logging and utility functions
from ...utils.insert_sql import insert_to_sql_server
from ...utils.insert_helpers import insert_entities
from ...utils.load_yaml import load_yaml

logger = logging.getLogger(__name__)

def extract_company(file_path, engine, progress=None):
    """Extract company details, notes, and tasks from YAML file."""

    data = load_yaml(file_path, console=progress.console if progress else None)
    if not data:
        return 

    if not isinstance(data, list) or len(data) < 1:
        logger.warning(f"No valid company data found in {file_path}")
        return

    # --- Company record ---
    company_header = data[0]
    company_data = {
        "id": company_header.get("ID"),
        "name": company_header.get("Name"),
        "filename": os.path.basename(file_path)
    }

    try:
        insert_to_sql_server(file_path, engine, "company", company_data, console=progress.console if progress else None)
        logger.debug(f"Inserted company: {company_data['name']}")
    except Exception as e:
        logger.error(f"FAIL: insert company from {file_path}: {e}")
        
        if progress:
            progress.console.print(f"[red]Company insert failed: {file_path}: {e}[/red]")

    # Notes, Tasks, Emails
    notes, tasks, emails = parse_notes_tasks_emails(data, company_id=company_data['id'])

    insert_entities(file_path, engine, notes, "notes", "note", company_data['id'], progress)
    insert_entities(file_path, engine, tasks, "tasks", "task", company_data['id'], progress)
    insert_entities(file_path, engine, emails, "emails", "email", company_data['id'], progress)