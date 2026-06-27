import pandas as pd
import os

def load_and_merge_data(base_dir):
    """
    Loads ACCIDENT, VEHICLE, and PERSON datasets from 2022 and 2023,
    and merges them into a single comprehensive dataframe at the PERSON level.
    """
    years = ['CRSS2022CSV', 'CRSS2023CSV']
    merged_dfs = []

    for year_folder in years:
        folder_path = os.path.join(base_dir, year_folder)
        
        try:
            # Load tables
            accident = pd.read_csv(os.path.join(folder_path, 'ACCIDENT.csv'), low_memory=False)
            vehicle = pd.read_csv(os.path.join(folder_path, 'VEHICLE.csv'), low_memory=False)
            person = pd.read_csv(os.path.join(folder_path, 'PERSON.csv'), low_memory=False)

            # Some columns might exist in both vehicle and accident (like YEAR), so we merge carefully
            # Merge VEHICLE and ACCIDENT on CASENUM
            acc_veh = pd.merge(vehicle, accident, on='CASENUM', how='inner', suffixes=('_veh', '_acc'))

            # Merge with PERSON on CASENUM and VEH_NO
            # Note: non-motorists might have VEH_NO=0, we'll keep them with a left join or just inner
            # Inner join to focus on vehicle occupants for severity prediction
            acc_veh_per = pd.merge(person, acc_veh, on=['CASENUM', 'VEH_NO'], how='inner', suffixes=('_per', '_vehacc'))
            
            merged_dfs.append(acc_veh_per)
            print(f"Successfully loaded and merged {year_folder}")
        except Exception as e:
            print(f"Error processing {year_folder}: {e}")

    # Combine all years
    if merged_dfs:
        final_df = pd.concat(merged_dfs, ignore_index=True)
        return final_df
    return pd.DataFrame()

if __name__ == "__main__":
    df = load_and_merge_data(r"c:\Users\HP\JeevanSetuN")
    print(f"Loaded {len(df)} total person-level records.")
