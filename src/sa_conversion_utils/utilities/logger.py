import os

def log_message(log_file, message: str):
    with open(log_file, 'a') as log_file_obj:
        log_file_obj.write(message + '\n')

def log_error(log_file, error_message: str, file_path: str):
    # Convert file path to a file URI
    file_uri = f'file:///{file_path.replace(os.sep, "/")}'
    # Format the log message with the clickable link
    full_message = f"{error_message}: {file_uri}"
    # Log the message using the log_message function
    log_message(log_file, full_message)

# Example usage
# error_file = "C:/Users/JohnDoe/Documents/error_file.sql"
# log_file = "C:/Users/JohnDoe/Documents/error_log.txt"
# log_error(log_file, "Error processing file", error_file)
