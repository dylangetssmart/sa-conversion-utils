import logging
import pandas as pd

logger = logging.getLogger(__name__)

def insert_to_sql_server(file_path, engine, table_name, data, console=None):
    try:
        df = pd.DataFrame([data])
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        logger.debug(f"Data inserted into {table_name}: {data}")
    except Exception as e:
        logger.error(f"{file_path} - Error inserting data into {table_name}: {e}")
        if console:
            console.print(f"[red]Error inserting data into {table_name} -- {file_path}[/red]")
        return None