import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_sample_weight

from severity_loader import load_and_merge_data
from severity_preprocessing import preprocess_data
from severity_features import engineer_features, get_feature_pipeline

def train_models():
    base_dir = r"c:\Users\HP\JeevanSetuN"
    print("Loading data...")
    df = load_and_merge_data(base_dir)
    
    if df.empty:
        print("No data loaded. Check paths.")
        return
        
    print(f"Loaded {len(df)} records. Preprocessing...")
    X_train, y_train, X_val, y_val, X_test, y_test, label_encoder = preprocess_data(df)
    
    # Save test data for evaluation phase
    os.makedirs(os.path.join(base_dir, "ai", "severity_prediction", "data"), exist_ok=True)
    X_test.to_csv(os.path.join(base_dir, "ai", "severity_prediction", "data", "X_test.csv"), index=False)
    import numpy as np
    np.save(os.path.join(base_dir, "ai", "severity_prediction", "data", "y_test.npy"), y_test)
    joblib.dump(label_encoder, os.path.join(base_dir, "ai", "severity_prediction", "data", "label_encoder.joblib"))
    
    print("Engineering features...")
    # Filter columns to only what we need for training
    X_train_sub = engineer_features(X_train)
    X_val_sub = engineer_features(X_val)
    
    preprocessor, _ = get_feature_pipeline()
    
    print("Training Random Forest...")
    # Compute balanced sample weights to tell the model to treat all classes equally
    sample_weights = compute_sample_weight('balanced', y_train)
    
    rf_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1))
    ])
    rf_pipeline.fit(X_train_sub, y_train, classifier__sample_weight=sample_weights)
    rf_preds = rf_pipeline.predict(X_val_sub)
    rf_acc = accuracy_score(y_val, rf_preds)
    rf_f1 = f1_score(y_val, rf_preds, average='weighted')
    print(f"Random Forest Validation - Acc: {rf_acc:.4f}, F1: {rf_f1:.4f}")
    
    print("Training XGBoost...")
    xgb_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', XGBClassifier(n_estimators=50, max_depth=6, learning_rate=0.1, random_state=42, use_label_encoder=False, eval_metric='mlogloss'))
    ])
    xgb_pipeline.fit(X_train_sub, y_train, classifier__sample_weight=sample_weights)
    xgb_preds = xgb_pipeline.predict(X_val_sub)
    xgb_acc = accuracy_score(y_val, xgb_preds)
    xgb_f1 = f1_score(y_val, xgb_preds, average='weighted')
    print(f"XGBoost Validation - Acc: {xgb_acc:.4f}, F1: {xgb_f1:.4f}")
    
    # Select best
    best_pipeline = rf_pipeline if rf_f1 > xgb_f1 else xgb_pipeline
    best_name = "RandomForest" if rf_f1 > xgb_f1 else "XGBoost"
    print(f"Best model selected: {best_name}")
    
    # Export best model
    model_path = os.path.join(base_dir, "ai", "severity_prediction", "best_severity_model.joblib")
    joblib.dump(best_pipeline, model_path)
    print(f"Model saved to {model_path}")
    print("Save and load instructions: Use joblib.load('best_severity_model.joblib') to load the full pipeline for inference.")

if __name__ == "__main__":
    train_models()
