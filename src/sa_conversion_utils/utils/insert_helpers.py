import logging
from .insert_sql import insert_to_sql_server

logger = logging.getLogger(__name__)

def insert_entities(file_path, engine, entities, table_name, entity_label, parent_id, progress=None):
    """
    Insert a list of entities (notes, tasks, emails) into the database.

    Args:
        file_path (str): Path to the YAML file being processed.
        engine (sqlalchemy.Engine): Database engine.
        entities (list): List of dicts to insert.
        table_name (str): Target SQL table (e.g., 'notes').
        entity_label (str): Label for logging (e.g., 'note').
        parent_id (str|int): Contact or company ID to associate.
        progress: Optional rich Progress object for console reporting.
    """
    for entity in entities:
        try:
            insert_to_sql_server(file_path, engine, table_name, entity, console=progress.console if progress else None)
            logger.debug(f"Inserted {entity_label} ID {entity['id']} for parent ID {parent_id}")
        except Exception as e:
            logger.error(f"FAIL: insert {entity_label} ID {entity.get('id')} from {file_path}: {e}")

            if progress:
                progress.console.print(
                    f"[red]{entity_label.capitalize()} insert failed: {file_path}: {e}[/red]"
                )
