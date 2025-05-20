import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import openpyxl
import os

def select_file():
    filepath = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if filepath:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, filepath)

def convert_excel_to_csv():
    excel_path = entry_file_path.get()
    if not os.path.isfile(excel_path):
        messagebox.showerror("Error", "Please select a valid Excel file.")
        return

    try:
        output_folder = os.path.dirname(excel_path)
        excel_data = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')

        for sheet_name, data in excel_data.items():
            sanitized_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name)
            csv_file_path = os.path.join(output_folder, f"{sanitized_name}.csv")
            data.to_csv(csv_file_path, index=False)

        messagebox.showinfo("Success", "All sheets have been exported as CSV files.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to convert Excel file.\n{str(e)}")

# GUI Setup
root = tk.Tk()
root.title("Excel to CSV Converter")
root.geometry("500x150")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(expand=True, fill="both")

label_file = tk.Label(frame, text="Select Excel File:")
label_file.pack(anchor="w")

entry_file_path = tk.Entry(frame, width=60)
entry_file_path.pack(side="left", fill="x", expand=True)

btn_browse = tk.Button(frame, text="Browse", command=select_file)
btn_browse.pack(side="left", padx=5)

btn_convert = tk.Button(root, text="Convert to CSVs", command=convert_excel_to_csv)
btn_convert.pack(pady=10)

root.mainloop()