from __future__ import annotations

from datetime import datetime, timezone


def generate_incident_id(prefix: str = "INC") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}{timestamp}"

