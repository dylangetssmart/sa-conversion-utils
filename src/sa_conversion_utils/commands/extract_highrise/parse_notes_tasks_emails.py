import re
import logging
from .process_date import process_date

logger = logging.getLogger(__name__)

def extract_id(entry_key: str) -> str | None:
    """
    Extract the numeric ID from a note or task key string.
    Examples:
        'Note 711840863' -> '711840863'
        'Task recording 711847247' -> '711847247'
        'Email 744140388' -> '744140388'
    """
    match = re.search(r'(\d+)$', entry_key.strip().rstrip(':'))
    return match.group(1) if match else None


def parse_notes_tasks_emails(data: list, contact_id: int = None, company_id: int = None):
    notes, tasks, emails = [], [], []

    for item in data:
        if not isinstance(item, dict):
            continue

        entry_key = next(iter(item.keys()))
        entry_id = extract_id(entry_key)
        entry_details = item.get(entry_key)

        if entry_id is None or not isinstance(entry_details, list):
            continue

        # Flatten list of small dicts into one dict
        merged = {}
        for detail in entry_details:
            if isinstance(detail, dict):
                merged.update(detail)

        written_date = process_date(merged.get("Written"))

        if entry_key.lower().startswith("note"):
            notes.append({
                "id": entry_id,
                "author": merged.get("Author"),
                "written_date": written_date,
                "about": merged.get("About"),
                "body": merged.get("Body"),
                "contact_id": contact_id,
                "company_id": company_id,
            })

        elif entry_key.lower().startswith("task"):
            tasks.append({
                "id": entry_id,
                "author": merged.get("Author"),
                "written_date": written_date,
                "about": merged.get("About"),
                "body": merged.get("Body"),
                "contact_id": contact_id,
                "company_id": company_id,
            })

        elif entry_key.lower().startswith("email"):
            emails.append({
                "id": entry_id,
                "author": merged.get("Author"),
                "written_date": written_date,
                "about": merged.get("About"),
                "subject": merged.get("Subject"),   # only emails
                "body": merged.get("Body"),
                "contact_id": contact_id,
                "company_id": company_id,
            })

    return notes, tasks, emails
