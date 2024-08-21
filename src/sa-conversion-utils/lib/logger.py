import os

def log_message(log_file, message: str):
    with open(log_file, 'a') as log_file_obj:
        log_file_obj.write(message + '\n')
