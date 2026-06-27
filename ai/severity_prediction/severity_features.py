import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Explanation of Features:
#
# 1. TIME/LIGHTING
# - HOUR: Time of crash. Nighttime crashes often have higher severity due to poor visibility and speeding.
# - LGT_COND (Lighting Condition): Dark/Unlit roads drastically increase critical injuries.
#
# 2. WEATHER/ROAD
# - WEATHER: Rain, snow, or fog impacts braking distance and control.
# - VSURCOND (Vehicle Surface Condition): Wet or icy roads lead to loss of control, increasing severity.
#
# 3. COLLISION INFO
# - MAN_COLL (Manner of Collision): Head-on collisions (usually coded differently) transfer much more kinetic energy.
# - VE_TOTAL (Number of Vehicles): Multi-vehicle pileups can be more severe.
# - HARM_EV (First Harmful Event): Rollovers or hitting fixed objects (trees) vs hitting another car.
#
# 4. VEHICLE INFO
# - BODY_TYP (Body Type): Motorcycles and small cars offer less protection than large SUVs.
# - IMPACT1 (Initial Point of Impact): Frontal and side impacts have different severity profiles.
# - ROLLOVER: A vehicle rolling over is highly correlated with critical/fatal injuries.
#
# 5. INJURY/PERSON INFO (Used as features IF known at dispatch time, else avoided)
# - AGE: Older individuals or very young children have a higher risk of severe outcomes from the same impact.
# - SEAT_POS: Driver vs passenger, front vs rear.
# - REST_USE (Restraint/Seatbelt Use): Unbelted occupants have drastically higher critical injury rates.

def get_feature_pipeline():
    """
    Creates a scikit-learn preprocessing pipeline for feature engineering.
    """
    
    # Define columns based on CRSS structure
    numeric_features = [
        'AGE',       # Age of the person
        'VE_TOTAL',  # Total vehicles involved
    ]
    
    categorical_features = [
        'HOUR',      # Hour of day
        'LGT_COND',  # Lighting conditions
        'WEATHER',   # Weather
        'VSURCOND',  # Road surface condition
        'MAN_COLL',  # Manner of collision
        'HARM_EV',   # First harmful event
        'BODY_TYP',  # Vehicle body type
        'IMPACT1',   # Point of impact
        'ROLLOVER',  # Rollover indicator
        'SEAT_POS',  # Seat position
        'REST_USE'   # Restraint use (seatbelt)
    ]
    
    # Impute missing numerics with median and scale
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Impute missing categoricals with a constant 'Missing' and OneHotEncode
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value=-1)),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    # Combine into a ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    return preprocessor, numeric_features + categorical_features

def engineer_features(X_df):
    """
    Helper to extract just the needed columns before feeding to the pipeline.
    This avoids passing massive 100+ column dataframes to transformers.
    """
    _, selected_cols = get_feature_pipeline()
    
    # Ensure all selected columns exist (fill with -1 if missing from some years)
    for col in selected_cols:
        if col not in X_df.columns:
            X_df[col] = -1
            
    return X_df[selected_cols]
