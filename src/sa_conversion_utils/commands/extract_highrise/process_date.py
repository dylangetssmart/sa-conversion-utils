from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def process_date(date_string):
    """ Convert date string to SQL Server compatible format """
    try:
        # Parse the date string into a datetime object
        date_obj = datetime.strptime(date_string, "%B %d, %Y %H:%M")
        # Format the datetime object to the SQL-compatible format (DATETIME(3))
        return date_obj.strftime("%Y-%m-%d %H:%M:%S.000")
    except ValueError:
        logger.warning(f"Warning: Could not parse date: {date_string}")
        return None