import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

from severity_features import engineer_features

def evaluate_model():
    base_dir = r"c:\Users\HP\JeevanSetuN"
    data_dir = os.path.join(base_dir, "ai", "severity_prediction", "data")
    
    print("Loading test data and model...")
    try:
        X_test = pd.read_csv(os.path.join(data_dir, "X_test.csv"))
        y_test = np.load(os.path.join(data_dir, "y_test.npy"))
        label_encoder = joblib.load(os.path.join(data_dir, "label_encoder.joblib"))
        model = joblib.load(os.path.join(base_dir, "ai", "severity_prediction", "best_severity_model.joblib"))
    except FileNotFoundError:
        print("Data or model not found. Please run train_severity_model.py first.")
        return

    print("Evaluating...")
    X_test_sub = engineer_features(X_test)
    y_pred = model.predict(X_test_sub)
    y_pred_proba = model.predict_proba(X_test_sub)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted')
    rec = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"\n--- Evaluation Metrics ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    
    print("\n--- Classification Report ---")
    target_names = label_encoder.classes_
    print(classification_report(y_test, y_pred, target_names=target_names))
    
    print("\n--- Confusion Matrix ---")
    cm = confusion_matrix(y_test, y_pred)
    cm_df = pd.DataFrame(cm, index=[f"True {n}" for n in target_names], columns=[f"Pred {n}" for n in target_names])
    print(cm_df)
    
    print("\n--- Metric Importance for Emergency Response ---")
    print("In the context of JeevanSetu (Emergency Response), RECALL for the 'Critical' class is the most important metric.")
    print("A False Negative (predicting a Critical accident as Minor) could delay life-saving medical dispatch.")
    print("A False Positive (predicting Minor as Critical) wastes resources but does not cost lives.")
    print("We should ideally optimize the classification threshold to maximize Critical Recall.")

if __name__ == "__main__":
    evaluate_model()
