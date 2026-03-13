"""
Mini README:
User-facing dashboard routes for widgets, sensor ingestion, charts, and actuator commands.
Provides Adafruit IO-like primitives: feeds/topics, controls, and mixed widgets.
"""

import json

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ActuatorCommand, DashboardWidget, SensorDataPoint, User

router = APIRouter(prefix="/api", tags=["dashboard-api"])


@router.post("/widgets")
def create_widget(
    name: str = Form(...),
    widget_type: str = Form(...),
    topic: str = Form(""),
    config_json: str = Form("{}"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    widget = DashboardWidget(owner_id=user.id, name=name, widget_type=widget_type, topic=topic, config_json=config_json)
    db.add(widget)
    db.commit()
    return {"ok": True, "widget_id": widget.id}


@router.post("/sensor/publish")
def publish_sensor(topic: str = Form(...), value: float = Form(...), api_key: str = Form(...), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.api_key == api_key)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    point = SensorDataPoint(owner_id=user.id, topic=topic, value=value)
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


@router.post("/actuator/send")
def send_command(
    target: str = Form(...),
    command: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cmd = ActuatorCommand(owner_id=user.id, target=target, command=command)
    db.add(cmd)
    db.commit()
    return {"ok": True}


@router.get("/widgets")
def list_widgets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widgets = db.execute(select(DashboardWidget).where(DashboardWidget.owner_id == user.id)).scalars().all()
    return [
        {"name": w.name, "widget_type": w.widget_type, "topic": w.topic, "config": json.loads(w.config_json), "id": w.id}
        for w in widgets
    ]
