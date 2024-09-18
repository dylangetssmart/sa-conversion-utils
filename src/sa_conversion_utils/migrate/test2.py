import pandas as pd

def clean_and_read_csv(file_path):
    # Step 1: Remove NUL characters from the CSV file
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        text = file.read().replace("\x00", "")
    
    # Write the cleaned text back to the file
    with open(file_path, 'w', encoding='ISO-8859-1') as file:
        file.write(text)
    
    # Step 2: Read the cleaned CSV file with pandas
    df = pd.read_csv(file_path, encoding='ISO-8859-1', low_memory=False, usecols=["litify_pm__lit_Note__c"])
    
    # Step 3: Print the dataframe
    print(df)

# Example usage:
csv = r"C:\LocalConv\Litify-Shiner\data\litify_pm__lit_Note__c.csv"
clean_and_read_csv(csv)