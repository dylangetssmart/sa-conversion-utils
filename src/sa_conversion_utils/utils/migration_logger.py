import pandas as pd
from datetime import datetime
import os

# Define the path to the log file
LOG_FILE_PATH = os.path.join(os.getcwd(),'migration_log.xlsx')
# LOG_FILE_PATH = os.path.join('path', 'to', 'your', 'repo', 'migration_log.xlsx')

def log_migration_step(subcommand, function, database, status, start_time, end_time, output_errors):
    start_time_str = start_time.strftime('%Y-%m-%d %H:%M') if start_time else None
    end_time_str = end_time.strftime('%Y-%m-%d %H:%M') if end_time else None
    duration = str(end_time - start_time) if start_time and end_time else None

    log_entry = {
        "Subcommand": subcommand,
        "Function": function,
        "Database": database,
        "Status": status,
        "Start Time": start_time_str,
        "End Time": end_time_str,
        "Duration": duration,
        "Output/Errors": output_errors,
    }

    new_entry_df = pd.DataFrame([log_entry])

    if os.path.exists(LOG_FILE_PATH):
        # If the file exists, append the new log entry
        with pd.ExcelWriter(LOG_FILE_PATH, mode='a', if_sheet_exists='overlay') as writer:
            existing_df = pd.read_excel(LOG_FILE_PATH)
            updated_df = pd.concat([existing_df, new_entry_df], ignore_index=True)
            updated_df.to_excel(writer, index=False)
    else:
        # If the file doesn't exist, create a new one
        new_entry_df.to_excel(LOG_FILE_PATH, index=False)

def wipe_migration_log():
    if os.path.exists(LOG_FILE_PATH):
        df = pd.DataFrame(columns=["Step Name", "Status", "Start Time", "End Time", "Duration", "Output/Errors", "Responsible"])
        df.to_excel(LOG_FILE_PATH, index=False)

# Example usage
# start_time = datetime.now()
# # ... perform some migration step ...
# end_time = datetime.now()
# log_migration_step("Data Extraction", "Completed", start_time, end_time, None, "YourName")
