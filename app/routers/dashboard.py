"""
Mini README:
User-facing dashboard routes for widgets, sensor ingestion, charts, and actuator commands.
Provides Adafruit IO-like primitives: feeds/topics, controls, and mixed widgets.
"""

import json

from typing import Optional

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ActuatorCommand, DashboardWidget, SensorDataPoint, User

router = APIRouter(prefix="/api", tags=["dashboard-api"])
ALLOWED_WIDGET_TYPES = {"chart", "switch", "map", "gauge", "text", "door"}


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


@router.post("/widgets")
def create_widget(
    request: Request,
    name: str = Form(...),
    widget_type: str = Form(...),
    topic: str = Form(""),
    config_json: str = Form("{}"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cleaned_widget_type = widget_type.strip().lower()
    if cleaned_widget_type not in ALLOWED_WIDGET_TYPES:
        raise HTTPException(status_code=400, detail="Invalid widget type")

    try:
        parsed_config = json.loads(config_json or "{}")
    except json.JSONDecodeError as exc:
        if "text/html" in request.headers.get("accept", ""):
            request.session["flash"] = f"Widget was not added: config must be valid JSON ({exc.msg})."
            return RedirectResponse(url="/dashboard", status_code=303)
        raise HTTPException(status_code=400, detail="Config JSON is invalid") from exc

    widget = DashboardWidget(
        owner_id=user.id,
        name=name.strip(),
        widget_type=cleaned_widget_type,
        topic=topic.strip(),
        config_json=json.dumps(parsed_config),
    )
    db.add(widget)
    db.commit()

    if "text/html" in request.headers.get("accept", ""):
        request.session["flash"] = f"Widget '{widget.name}' added successfully."
        return RedirectResponse(url="/dashboard", status_code=303)

    return {"ok": True, "widget_id": widget.id}


@router.post("/sensor/publish")
def publish_sensor(
    topic: str = Form(...),
    value: str = Form(...),
    api_key: str = Form(""),
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Accepts API keys in three forms for device compatibility:
    1) Form field `api_key` (legacy behavior)
    2) `Authorization: Bearer <api_key>` header
    3) `X-API-Key: <api_key>` header
    """
    resolved_api_key = (api_key or "").strip()
    if not resolved_api_key and authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            resolved_api_key = token.strip()
    if not resolved_api_key and x_api_key:
        resolved_api_key = x_api_key.strip()

    user = db.execute(select(User).where(User.api_key == resolved_api_key)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    parsed_value = parse_sensor_value(value)

    point = SensorDataPoint(owner_id=user.id, topic=topic, value=parsed_value)
    db.add(point)
    db.commit()
    return {"ok": True}


@router.get("/sensor/latest")
def latest_sensor_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    points = (
        db.execute(select(SensorDataPoint).where(SensorDataPoint.owner_id == user.id).order_by(desc(SensorDataPoint.created_at)).limit(30))
        .scalars()
        .all()
    )
    return [
        {"topic": p.topic, "value": p.value, "created_at": p.created_at.isoformat()} for p in reversed(points)
    ]


@router.get("/sensor/door-status")
def latest_door_status(
    topic: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest_point = (
        db.execute(
            select(SensorDataPoint)
            .where(SensorDataPoint.owner_id == user.id, SensorDataPoint.topic == topic)
            .order_by(desc(SensorDataPoint.created_at))
            .limit(1)
        )
        .scalars()
        .first()
    )
    if not latest_point:
        return {"topic": topic, "state": "UNKNOWN", "value": None, "created_at": None}

    return {
        "topic": topic,
        "state": sensor_value_to_door_state(latest_point.value),
        "value": latest_point.value,
        "created_at": latest_point.created_at.isoformat(),
    }


@router.post("/actuator/send")
def send_command(
    request: Request,
    target: str = Form(...),
    command: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cmd = ActuatorCommand(owner_id=user.id, target=target, command=command)
    db.add(cmd)
    db.commit()

    if "text/html" in request.headers.get("accept", ""):
        request.session["flash"] = f"Command '{command}' sent to {target}."
        return RedirectResponse(url="/dashboard", status_code=303)

    return {"ok": True}


@router.get("/widgets")
def list_widgets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widgets = db.execute(select(DashboardWidget).where(DashboardWidget.owner_id == user.id)).scalars().all()
    return [
        {"name": w.name, "widget_type": w.widget_type, "topic": w.topic, "config": json.loads(w.config_json), "id": w.id}
        for w in widgets
    ]
