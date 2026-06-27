# JeevanSetu AI Layer

This package contains the standalone AI system for accident detection, severity prediction, hospital recommendation, response building, and model training.

## Folder Structure

```text
ai/
  accident_detection/       Rule-based and model-ready accident detection engines.
  severity_prediction/      Risk scoring and severity classification logic.
  hospital_recommendation/  Geo, ETA, capability, and availability based ranking.
  feature_engineering/      Reusable sensor-derived feature calculations.
  preprocessing/           Dataset validation, cleaning, and train/test preparation.
  datasets/                CSV schemas and seed data for local development.
  models/                  Saved trained model artifacts and metadata.
  notebooks/               Exploratory analysis notebooks.
  tests/                   Unit and integration tests for AI behavior.
  configs/                 Runtime thresholds, paths, and model settings.
  utils/                   Shared geo, IDs, and serialization helpers.
  api/                     FastAPI service exposing AI-only endpoints.
  training/                Training pipeline for Random Forest and XGBoost.
```

## Dataset Strategy

### Accident Detection Dataset

Location: `ai/datasets/accident_detection_events.csv`

Required columns:

```text
event_id,timestamp,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,speed_kmph,previous_speed_kmph,orientation_prev_roll,orientation_prev_pitch,orientation_prev_yaw,orientation_curr_roll,orientation_curr_pitch,orientation_curr_yaw,label
```

`label` is `1` for crash events and `0` for non-crash events.

### Severity Prediction Dataset

Location: `ai/datasets/severity_events.csv`

Required columns:

```text
incident_id,vehicle_speed_kmph,impact_force_g,speed_drop_kmph,orientation_change_deg,response_delay_sec,injury_severity,severity_label
```

`severity_label` is one of `minor`, `moderate`, or `critical`.

### Hospital Recommendation Dataset

Location: `ai/datasets/hospitals.csv`

Required columns:

```text
hospital_id,hospital_name,latitude,longitude,trauma_capability,icu_available,beds_available,emergency_capacity,active
```

Scores are normalized in code. Higher trauma capability, ICU availability, beds, and emergency capacity improve ranking; lower ETA and distance improve ranking.

## Feature Formulas

- Acceleration magnitude: `sqrt(ax^2 + ay^2 + az^2)`
- Gyroscope magnitude: `sqrt(gx^2 + gy^2 + gz^2)`
- Speed drop: `max(previous_speed - current_speed, 0)`
- Orientation change: Euclidean angular delta across roll, pitch, yaw.
- Impact force: acceleration magnitude expressed in g-force proxy.
- Response delay: seconds between alert and user confirmation/escalation.

## Development Roadmap

1. Phase 1 - Dataset Collection: collect labeled crash/non-crash mobile sensor traces and hospital metadata.
2. Phase 2 - Feature Engineering: stabilize derived features and outlier handling.
3. Phase 3 - Accident Detection: ship rule-based v1, then train binary classifiers.
4. Phase 4 - Severity Prediction: calibrate score bands with emergency outcome data.
5. Phase 5 - Hospital Recommendation: integrate live ETA, beds, ICU, and trauma capability feeds.
6. Phase 6 - FastAPI Integration: expose AI-only endpoints and backend handoff contracts.
7. Phase 7 - Testing: unit, contract, load, drift, and field simulation tests.

## How to prepare and train your crash dataset

### 1) Prepare a crash sensor dataset for accident detection training

Use `ai/training/prepare_dataset.py` to standardize your raw dataset into `ai/datasets/accident_detection_events.csv`.
It supports the JeevanSetu crash dataset zip/parquet format with `gsensor`, `gyro`, `gps_speed`, and `label` columns.

```bash
cd c:\Users\prade\OneDrive\Desktop\jeevansetu\Jeevansetu\ai
python training/prepare_dataset.py --input path/to/crash_dataset.zip --output datasets/accident_detection_events.csv --overwrite
```

The script converts sensor time-series traces into event-level training features and normalizes labels to `0`/`1`.

### 2) Train the accident detection model

```bash
cd c:\Users\prade\OneDrive\Desktop\jeevansetu\Jeevansetu\ai
python training/train.py --dataset datasets/accident_detection_events.csv --output-dir models
```

### 3) Training outputs

- `ai/models/best_accident_detector.joblib`
- `ai/models/random_forest_accident_detector.joblib`
- `ai/models/xgboost_accident_detector.joblib`
- `ai/models/training_metrics.json`

