import os

def generate_runlist(folder_path, output_file="_runlist2.txt"):
    """
    Generates a runlist file based on the .sql files in the specified folder.

    Args:
        folder_path (str): The path to the folder containing .sql files.
        output_file (str): The name of the output runlist file. Defaults to '_runlist.txt'.

    Returns:
        None
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")

    # Get all .sql files in the folder
    sql_files = [file for file in os.listdir(folder_path) if file.lower().endswith('.sql')]

    if not sql_files:
        print(f"No .sql files found in the folder '{folder_path}'.")
        return

    # Sort files alphabetically
    sql_files.sort()

    # Write the runlist file
    runlist_path = os.path.join(folder_path, output_file)
    with open(runlist_path, "w") as runlist_file:
        runlist_file.write("# Auto-generated runlist\n")
        for sql_file in sql_files:
            runlist_file.write(f"{sql_file}\n")

    print(f"Runlist generated at: {runlist_path}")

if __name__ == "__main__":
    # Example usage
    folder_path = r"D:\skolrood\needles\conv\2_case"
    generate_runlist(folder_path)