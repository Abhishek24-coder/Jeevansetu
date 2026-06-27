from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from ai.feature_engineering.feature_extractor import FeatureExtractor
from ai.models.schemas import MotionVector, SensorPayload


ACCIDENT_REQUIRED_COLUMNS = {
    "accel_x",
    "accel_y",
    "accel_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
    "speed_kmph",
    "previous_speed_kmph",
    "orientation_prev_roll",
    "orientation_prev_pitch",
    "orientation_prev_yaw",
    "orientation_curr_roll",
    "orientation_curr_pitch",
    "orientation_curr_yaw",
    "label",
}


class AccidentDatasetPreprocessor:
    """Validates, cleans, and featurizes accident detection datasets."""

    def load(self, csv_path: str) -> pd.DataFrame:
        data = pd.read_csv(csv_path)
        missing = ACCIDENT_REQUIRED_COLUMNS.difference(data.columns)
        if missing:
            raise ValueError(f"dataset is missing required columns: {sorted(missing)}")
        return data

    def clean(self, data: pd.DataFrame) -> pd.DataFrame:
        cleaned = data.copy()
        numeric_columns = list(ACCIDENT_REQUIRED_COLUMNS - {"label"})
        cleaned[numeric_columns] = cleaned[numeric_columns].apply(pd.to_numeric, errors="coerce")
        cleaned["label"] = pd.to_numeric(cleaned["label"], errors="coerce")
        cleaned = cleaned.dropna(subset=numeric_columns + ["label"])
        cleaned = cleaned[(cleaned["speed_kmph"] >= 0) & (cleaned["previous_speed_kmph"] >= 0)]
        cleaned["label"] = cleaned["label"].astype(int)
        return cleaned.reset_index(drop=True)

    def featurize(self, data: pd.DataFrame) -> pd.DataFrame:
        rows: list[dict[str, float | int]] = []
        for _, row in data.iterrows():
            payload = SensorPayload(
                accelerometer=MotionVector(x=row.accel_x, y=row.accel_y, z=row.accel_z),
                gyroscope=MotionVector(x=row.gyro_x, y=row.gyro_y, z=row.gyro_z),
                speed_kmph=row.speed_kmph,
                previous_speed_kmph=row.previous_speed_kmph,
                previous_orientation=MotionVector(
                    x=row.orientation_prev_roll,
                    y=row.orientation_prev_pitch,
                    z=row.orientation_prev_yaw,
                ),
                current_orientation=MotionVector(
                    x=row.orientation_curr_roll,
                    y=row.orientation_curr_pitch,
                    z=row.orientation_curr_yaw,
                ),
            )
            features = FeatureExtractor.extract(payload)
            feature_row = features.model_dump()
            feature_row["label"] = int(row.label)
            rows.append(feature_row)
        return pd.DataFrame(rows)

    def split(
        self,
        features: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        x = features.drop(columns=["label"])
        y = features["label"]
        stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None
        if stratify is not None:
            minimum_test_fraction = y.nunique() / len(y)
            test_size = max(test_size, minimum_test_fraction)
        return train_test_split(x, y, test_size=test_size, random_state=random_state, stratify=stratify)

    def prepare(self, csv_path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        data = self.clean(self.load(csv_path))
        features = self.featurize(data)
        return self.split(features)
