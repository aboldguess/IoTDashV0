"""
Mini README:
Shared sensor payload parsing helpers used by HTTP ingestion and MQTT ingestion code paths.
"""

from fastapi import HTTPException


def parse_sensor_value(raw_value: str) -> float:
    """Convert sensor payloads into a numeric value for storage and charting."""
    normalized_value = raw_value.strip().lower()
    if normalized_value in {"on", "open", "true"}:
        return 1.0
    if normalized_value in {"off", "closed", "false"}:
        return 0.0

    try:
        return float(raw_value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Sensor value must be numeric or on/off style text") from exc


def sensor_value_to_door_state(value: float) -> str:
    """Interpret a numeric value as an OPEN/CLOSED door state."""
    return "OPEN" if value >= 0.5 else "CLOSED"
