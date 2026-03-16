"""
Mini README:
This file contains database models for users, plans, widgets, sensor datapoints,
site settings, MQTT sensor enrollment, and actuator commands powering the IoT dashboard.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubscriptionTier(Base):
    __tablename__ = "subscription_tiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0)
    usage_limit_daily: Mapped[int] = mapped_column(Integer, default=1000)
    usage_limit_monthly: Mapped[int] = mapped_column(Integer, default=30000)
    included_features: Mapped[str] = mapped_column(Text, default="basic_widgets")
    special_offer: Mapped[str] = mapped_column(String(255), default="")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    profile_picture_url: Mapped[str] = mapped_column(String(512), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    api_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    subscription_tier_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_tiers.id"), nullable=True)

    subscription_tier: Mapped[SubscriptionTier | None] = relationship()
    widgets: Mapped[list["DashboardWidget"]] = relationship(back_populates="owner")
    enrolled_sensors: Mapped[list["SensorEnrollment"]] = relationship(back_populates="owner")


class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    widget_type: Mapped[str] = mapped_column(String(40), nullable=False)  # chart/switch/map/gauge/text/door
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    topic: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped[User] = relationship(back_populates="widgets")


class SensorEnrollment(Base):
    __tablename__ = "sensor_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sensor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    qos: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped[User] = relationship(back_populates="enrolled_sensors")


class SensorDataPoint(Base):
    __tablename__ = "sensor_data_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    value: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ActuatorCommand(Base):
    __tablename__ = "actuator_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target: Mapped[str] = mapped_column(String(255), index=True)
    command: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SiteConfig(Base):
    __tablename__ = "site_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    splash_tagline: Mapped[str] = mapped_column(String(255), default="Build, monitor, and monetize your IoT")
    help_markdown: Mapped[str] = mapped_column(
        Text,
        default="Use Dashboard to add widgets, API Keys to publish sensor data, and Subscriptions to manage billing.",
    )
