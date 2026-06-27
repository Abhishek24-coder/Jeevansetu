from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from xgboost import XGBClassifier

from ai.configs.settings import DATASETS_DIR, MODELS_DIR
from ai.preprocessing import AccidentDatasetPreprocessor


def build_random_forest() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=250,
        max_depth=8,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )


def build_xgboost() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
    )


def evaluate_model(model: Any, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    predictions = model.predict(x_test)
    return {
        "accuracy": round(accuracy_score(y_test, predictions), 4),
        "precision": round(precision_score(y_test, predictions, zero_division=0), 4),
        "recall": round(recall_score(y_test, predictions, zero_division=0), 4),
        "f1": round(f1_score(y_test, predictions, zero_division=0), 4),
        "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
    }


def train(dataset_path: Path, output_dir: Path = MODELS_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    preprocessor = AccidentDatasetPreprocessor()
    x_train, x_test, y_train, y_test = preprocessor.prepare(str(dataset_path))

    candidates = {
        "random_forest": build_random_forest(),
        "xgboost": build_xgboost(),
    }

    metrics: dict[str, Any] = {}
    trained_models: dict[str, Any] = {}
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        metrics[name] = evaluate_model(model, x_test, y_test)
        trained_models[name] = model
        joblib.dump(model, output_dir / f"{name}_accident_detector.joblib")

    best_name = max(metrics, key=lambda key: metrics[key]["f1"])
    joblib.dump(trained_models[best_name], output_dir / "best_accident_detector.joblib")

    result = {
        "dataset": str(dataset_path),
        "feature_columns": list(x_train.columns),
        "best_model": best_name,
        "metrics": metrics,
    }
    with (output_dir / "training_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Train JeevanSetu accident detection models.")
    parser.add_argument("--dataset", default=str(DATASETS_DIR / "accident_detection_events.csv"))
    parser.add_argument("--output-dir", default=str(MODELS_DIR))
    args = parser.parse_args()

    result = train(Path(args.dataset), Path(args.output_dir))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
