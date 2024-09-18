import pandas as pd
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML
import re
from io import StringIO

csv_path = r"C:\LocalConv\Litify-Shiner\data\litify_pm__lit_Note__c.csv"

# Function to strip NUL characters from a string
def strip_nul(text):
    return text.replace("\x00", "")

# Read the CSV, applying the stripping function to the target column
# df = pd.read_csv(
#     csv_path,
#     encoding="ISO-8859-1",
#     low_memory=False,
#     dtype=str,
#     usecols=["litify_pm__lit_Note__c"],
#     converters={"litify_pm__lit_Note__c": strip_nul}
# )

def clean_html(raw_html):
    """
    Utility function to remove HTML tags from a string.
    """
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def extract_data(data_string):
    """
    Extract data from a CSV-like string, clean HTML content from specified fields, and return a pandas DataFrame.
    """
    # Simulate file object with StringIO for pandas to read
    data = StringIO(data_string)
    
    # Read the CSV data
    df = pd.read_csv(data)
    
    # Fields that are expected to contain HTML and need cleaning
    html_fields = ['litify_pm__lit_Note__c']
    
    # Apply HTML cleaning to the specified columns
    for field in html_fields:
        if field in df.columns:
            df[field] = df[field].astype(str).apply(clean_html)
    
    return df


data_string = """ "Id","OwnerId","IsDeleted","Name","CreatedDate","CreatedById","LastModifiedDate","LastModifiedById","SystemModstamp","litify_pm__lit_Account__c","litify_pm__lit_Damage__c","litify_pm__lit_Expense__c","litify_pm__lit_Insurance__c","litify_pm__lit_Intake__c","litify_pm__lit_Matter__c","litify_pm__lit_Negotiation__c","litify_pm__lit_Note__c","litify_pm__lit_Referral__c","litify_pm__lit_Request__c","litify_pm__lit_Resolution__c","litify_pm__lit_Role__c","litify_pm__lit_Time_Entry__c","litify_pm__lit_Topic__c","litify_ext__Private__c","External_Id__c","Case_Type__c","CaseId__c"
"a0x8Z00000ETV10QAH","0058Z000007t9CrQAI","0","2023-01-05 - Norfus, Victor vs. Heydel, Shannon","2023-01-05 17:07:21","0058Z000007t9CrQAI","2023-01-05 17:07:21","0058Z000007t9CrQAI","2023-01-05 17:07:21","","","","","","a0L8Z00000eDQkfUAG",""," <p>everythinhd</p>","","","","","","Status","0","","","" """
df = extract_data(data_string)
print(df)


"a0x8Z00000ETV10QAH","0058Z000007t9CrQAI","0","2023-01-05 - Norfus, Victor vs. Heydel, Shannon","2023-01-05 17:07:21","0058Z000007t9CrQAI","2023-01-05 17:07:21","0058Z000007t9CrQAI","2023-01-05 17:07:21","","","","","","a0L8Z00000eDQkfUAG",""," <p>everythinhd</p>","","","","","","Status","0","","",""