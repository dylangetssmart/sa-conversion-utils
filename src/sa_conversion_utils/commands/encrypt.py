import logging
import argparse
import os

logger = logging.getLogger(__name__)

def setup_parser(subparsers):
    encrypt_parser = subparsers.add_parser("encrypt", help="Run SSNEncryption.exe to encrypt SSNs in the database.")
    encrypt_parser.set_defaults(func=encrypt)

def encrypt(args):
    cwd = os.getcwd()
    lib_dir = os.path.join(cwd, "lib")
    exe_path = os.path.join(lib_dir, "SSNEncryption.exe")

    if not os.path.isfile(exe_path):
        logger.error(f"SSNEncryption.exe not found in {lib_dir}")
        print(f"SSNEncryption.exe not found in {lib_dir}")
        return

    try:
        result = os.system(exe_path)
        if result == 0:
            logger.info("SSN encryption completed successfully.")
            print("SSN encryption completed successfully.")
        else:
            logger.error(f"SSN encryption failed with exit code {result}.")
            print(f"SSN encryption failed with exit code {result}.")
    except Exception as e:
        logger.error(f"An error occurred while running SSN encryption: {str(e)}")
        print(f"An error occurred while running SSN encryption: {str(e)}")