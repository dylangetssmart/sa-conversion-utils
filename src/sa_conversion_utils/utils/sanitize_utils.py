import pandas as pd
import re

def clean_string(value):
    """Remove non-printable or control characters from a string."""
    if isinstance(value, str):
        return re.sub(r'[\x00-\x1F\x7F-\x9F]', '', value)
    return value

def sanitize_dataframe(df):
    """Sanitize a DataFrame by cleaning its string values."""
    return df.map(clean_string)

__all__ = ['clean_string', 'sanitize_dataframe']