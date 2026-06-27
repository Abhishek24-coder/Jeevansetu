import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Tuple

def map_severity(inj_sev_code):
    """
    Maps the KABCO injury severity code to standard classes.
    0: No Apparent Injury (O), 1: Possible Injury (C) -> Minor
    2: Suspected Minor Injury (B) -> Moderate
    3: Suspected Serious (A), 4: Fatal (K) -> Critical
    """
    if inj_sev_code in [0, 1, 5]:
        return 'Minor'
    elif inj_sev_code == 2:
        return 'Moderate'
    elif inj_sev_code in [3, 4]:
        return 'Critical'
    else:
        return 'Unknown' # 6, 8, 9

def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, LabelEncoder]:
    """
    Preprocesses the raw merged dataframe:
    - Filters valid rows based on target.
    - Handles missing values.
    - Splits into Train, Val, Test.
    """
    # 1. Map Target Variable
    df['SEVERITY_CLASS'] = df['INJ_SEV'].apply(map_severity)
    
    # Drop rows where target is unknown
    df = df[df['SEVERITY_CLASS'] != 'Unknown'].copy()
    
    # 2. Encode Target
    le = LabelEncoder()
    df['TARGET'] = le.fit_transform(df['SEVERITY_CLASS'])
    
    # Separate features and target
    X = df.drop(columns=['SEVERITY_CLASS', 'TARGET'])
    y = df['TARGET']
    
    # 3. Train/Val/Test Split (70/15/15)
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.1765, stratify=y_temp, random_state=42) # 0.15 / 0.85 approx 0.1765
    
    return X_train, y_train, X_val, y_val, X_test, y_test, le

if __name__ == "__main__":
    print("Preprocessing module ready.")
