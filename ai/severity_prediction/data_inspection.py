import pandas as pd
import os

def inspect_dataset(year, folder_path):
    print(f"=== Inspecting CRSS {year} Dataset ===")
    
    files_to_check = ['ACCIDENT.csv', 'VEHICLE.csv', 'PERSON.csv']
    
    for file in files_to_check:
        file_path = os.path.join(folder_path, file)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        print(f"\n--- {file} ---")
        try:
            # Read only first few rows to get columns and sample
            df = pd.read_csv(file_path, nrows=5)
            print(f"Columns ({len(df.columns)}):")
            print(list(df.columns))
            
            # Check for severity related columns
            sev_cols = [c for c in df.columns if 'SEV' in c.upper() or 'INJ' in c.upper() or 'FATAL' in c.upper()]
            if sev_cols:
                print(f"Potential Severity Columns: {sev_cols}")
                
        except Exception as e:
            print(f"Error reading {file}: {e}")
            
    print("\n")

if __name__ == "__main__":
    base_dir = r"c:\Users\HP\JeevanSetuN"
    inspect_dataset(2022, os.path.join(base_dir, "CRSS2022CSV"))
    inspect_dataset(2023, os.path.join(base_dir, "CRSS2023CSV"))
