from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


CRASH_DATASET_COLUMNS = {"event_id", "label", "gsensor", "gyro", "gps_speed"}


def _as_array(value: Any, width: int | None = None) -> np.ndarray:
    if value is None:
        array = np.asarray([], dtype=float)
    else:
        try:
            array = np.asarray(value, dtype=float)
        except (TypeError, ValueError):
            flattened = [np.asarray(item, dtype=float).reshape(-1) for item in value]
            array = np.vstack(flattened) if flattened else np.asarray([], dtype=float)
    if width is not None:
        array = np.reshape(array, (-1, width)) if array.size else np.empty((0, width))
    return np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)


def _peak_vector(samples: Any) -> np.ndarray:
    array = _as_array(samples, width=3)
    if len(array) == 0:
        return np.zeros(3)
    magnitudes = np.linalg.norm(array, axis=1)
    return array[int(np.argmax(magnitudes))]


def _speed_pair(samples: Any) -> tuple[float, float]:
    speeds = _as_array(samples)
    speeds = speeds[(speeds >= 0) & np.isfinite(speeds)]
    if len(speeds) == 0:
        return 0.0, 0.0

    peak_index = int(np.argmax(speeds))
    previous_speed = float(speeds[peak_index])
    after_peak = speeds[peak_index:]
    current_speed = float(np.min(after_peak)) if len(after_peak) else float(np.min(speeds))
    return previous_speed, current_speed


def _orientation_vectors(gyro_samples: Any) -> tuple[np.ndarray, np.ndarray]:
    gyro = _as_array(gyro_samples, width=3)
    if len(gyro) == 0:
        return np.zeros(3), np.zeros(3)

    # The source dataset does not include device orientation directly. We use a
    # cumulative gyro delta as a stable proxy for event-level orientation change.
    midpoint = max(len(gyro) // 2, 1)
    previous = np.cumsum(gyro[:midpoint], axis=0)[-1]
    current = np.cumsum(gyro, axis=0)[-1]
    return previous, current


def _convert_crash_dataset_frame(frame: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        accel = _peak_vector(row["gsensor"])
        gyro = _peak_vector(row["gyro"])
        previous_speed, current_speed = _speed_pair(row["gps_speed"])
        previous_orientation, current_orientation = _orientation_vectors(row["gyro"])
        source_label = int(row["label"])

        records.append(
            {
                "event_id": row.get("event_id", len(records)),
                "timestamp": "",
                "accel_x": accel[0],
                "accel_y": accel[1],
                "accel_z": accel[2],
                "gyro_x": gyro[0],
                "gyro_y": gyro[1],
                "gyro_z": gyro[2],
                "speed_kmph": current_speed,
                "previous_speed_kmph": previous_speed,
                "orientation_prev_roll": previous_orientation[0],
                "orientation_prev_pitch": previous_orientation[1],
                "orientation_prev_yaw": previous_orientation[2],
                "orientation_curr_roll": current_orientation[0],
                "orientation_curr_pitch": current_orientation[1],
                "orientation_curr_yaw": current_orientation[2],
                "source_label": source_label,
                "label": 1 if source_label > 0 else 0,
            }
        )
    return pd.DataFrame.from_records(records)


def _parquet_entries_from_zip(zip_path: Path) -> Iterable[tuple[str, bytes]]:
    with zipfile.ZipFile(zip_path) as archive:
        for entry in archive.infolist():
            if entry.filename.lower().endswith(".parquet"):
                yield entry.filename, archive.read(entry)


def prepare_dataset(input_path: Path, output_path: Path, overwrite: bool = False) -> dict[str, Any]:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} already exists; pass --overwrite to replace it")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    source_counts: dict[str, int] = {}

    if input_path.suffix.lower() == ".zip":
        for name, payload in _parquet_entries_from_zip(input_path):
            table = pq.read_table(io.BytesIO(payload), columns=list(CRASH_DATASET_COLUMNS))
            frame = table.to_pandas()
            converted = _convert_crash_dataset_frame(frame)
            frames.append(converted)
            source_counts[name] = len(converted)
    elif input_path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(input_path, columns=list(CRASH_DATASET_COLUMNS))
        converted = _convert_crash_dataset_frame(frame)
        frames.append(converted)
        source_counts[str(input_path)] = len(converted)
    else:
        frame = pd.read_csv(input_path)
        missing = CRASH_DATASET_COLUMNS.difference(frame.columns)
        if missing:
            raise ValueError(f"unsupported CSV shape; missing {sorted(missing)}")
        converted = _convert_crash_dataset_frame(frame)
        frames.append(converted)
        source_counts[str(input_path)] = len(converted)

    if not frames:
        raise ValueError(f"no parquet files found in {input_path}")

    dataset = pd.concat(frames, ignore_index=True)
    dataset.to_csv(output_path, index=False)

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "rows": int(len(dataset)),
        "source_rows": source_counts,
        "source_label_counts": {str(k): int(v) for k, v in dataset["source_label"].value_counts().sort_index().items()},
        "binary_label_counts": {str(k): int(v) for k, v in dataset["label"].value_counts().sort_index().items()},
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a crash sensor dataset for JeevanSetu accident detection.")
    parser.add_argument("--input", required=True, help="Path to a source zip, parquet, or CSV dataset.")
    parser.add_argument("--output", required=True, help="Path to write accident_detection_events.csv.")
    parser.add_argument("--overwrite", action="store_true", help="Replace the output file if it already exists.")
    args = parser.parse_args()

    summary = prepare_dataset(Path(args.input), Path(args.output), overwrite=args.overwrite)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
