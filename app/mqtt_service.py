"""
Mini README:
MQTT integration service for Mosquitto-compatible brokers.
- Manages a single resilient MQTT client connection.
- Supports connect/test/publish/subscribe workflows.
- Persists incoming enrolled sensor data into the database for charting.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.models import SensorDataPoint, SensorEnrollment
from app.sensor_utils import parse_sensor_value

logger = logging.getLogger(__name__)


@dataclass
class MQTTConnectionState:
    host: str = ""
    port: int = 1883
    username: str = ""
    tls_enabled: bool = False
    connected: bool = False
    last_error: str = ""
    subscribed_topics: dict[str, int] = field(default_factory=dict)


class MQTTManager:
    """Thread-safe MQTT manager with DB persistence callback for enrolled topics."""

    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._lock = threading.RLock()
        self._client: mqtt.Client | None = None
        self._state = MQTTConnectionState()

    def _build_client(self, client_id: str) -> mqtt.Client:
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        client.enable_logger(logger)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        return client

    @staticmethod
    def _normalize_broker_endpoint(host: str, port: int) -> tuple[str, int]:
        """Normalize user-provided MQTT broker values into host+port safe for paho connect."""
        cleaned_host = (host or "").strip()
        cleaned_port = int(port)

        if not cleaned_host:
            raise ValueError("MQTT host is required")

        # Accept values like "mqtt://172.19.0.29:1883" or "172.19.0.29:1883" from the UI.
        # paho-mqtt expects host only, so we parse and strip protocol/path fragments.
        candidate = cleaned_host
        parsed = urlparse(cleaned_host)
        if parsed.scheme and parsed.netloc:
            candidate = parsed.netloc

        if "/" in candidate:
            candidate = candidate.split("/", 1)[0]

        parsed_candidate = urlparse(f"//{candidate}")
        normalized_host = parsed_candidate.hostname or candidate
        if parsed_candidate.port:
            cleaned_port = parsed_candidate.port

        return normalized_host.strip("[]"), cleaned_port

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc):
        with self._lock:
            self._state.connected = rc == 0
            if rc != 0:
                self._state.last_error = f"MQTT connect failed with rc={rc}"
                logger.error(self._state.last_error)
                return
            for topic, qos in self._state.subscribed_topics.items():
                client.subscribe(topic, qos=qos)
            logger.info("MQTT connected to %s:%s", self._state.host, self._state.port)

    def _on_disconnect(self, client: mqtt.Client, userdata, rc):
        with self._lock:
            self._state.connected = False
            if rc != 0:
                self._state.last_error = f"Unexpected MQTT disconnect rc={rc}"
                logger.warning(self._state.last_error)

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        payload_text = msg.payload.decode("utf-8", errors="ignore")
        logger.debug("MQTT message on %s payload=%s", msg.topic, payload_text)
        db = self._session_factory()
        try:
            enrollments = db.execute(
                select(SensorEnrollment).where(SensorEnrollment.topic == msg.topic, SensorEnrollment.is_active.is_(True))
            ).scalars().all()
            if not enrollments:
                return

            try:
                parsed_value = parse_sensor_value(payload_text)
            except Exception:
                try:
                    body = json.loads(payload_text)
                    parsed_value = parse_sensor_value(str(body.get("value", body.get("reading", ""))))
                except Exception:
                    logger.warning("Unable to parse MQTT payload for topic %s: %s", msg.topic, payload_text)
                    return

            for enrollment in enrollments:
                db.add(SensorDataPoint(owner_id=enrollment.owner_id, topic=msg.topic, value=parsed_value))
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception("Failed storing MQTT message: %s", exc)
        finally:
            db.close()

    def connect(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        tls_enabled: bool = False,
        keepalive: int = 60,
    ) -> MQTTConnectionState:
        with self._lock:
            if self._client:
                self.disconnect()

            try:
                normalized_host, normalized_port = self._normalize_broker_endpoint(host=host, port=port)
            except ValueError as exc:
                self._state = MQTTConnectionState(host=host, port=port, username=username, tls_enabled=tls_enabled)
                self._state.connected = False
                self._state.last_error = str(exc)
                return self.status()

            client = self._build_client(client_id=f"iotdash-{uuid.uuid4().hex[:12]}")
            if username:
                client.username_pw_set(username=username, password=password)
            if tls_enabled:
                client.tls_set()

            self._state = MQTTConnectionState(
                host=normalized_host,
                port=normalized_port,
                username=username,
                tls_enabled=tls_enabled,
            )
            self._client = client

            try:
                client.connect(normalized_host, normalized_port, keepalive=keepalive)
                client.loop_start()
            except Exception as exc:
                self._state.last_error = str(exc)
                self._state.connected = False
                logger.exception("MQTT connect failed")
            return self.status()

    def disconnect(self):
        with self._lock:
            if self._client:
                try:
                    self._client.loop_stop()
                    self._client.disconnect()
                except Exception:
                    logger.exception("MQTT disconnect failed")
            self._client = None
            self._state.connected = False

    def status(self) -> MQTTConnectionState:
        with self._lock:
            return MQTTConnectionState(
                host=self._state.host,
                port=self._state.port,
                username=self._state.username,
                tls_enabled=self._state.tls_enabled,
                connected=self._state.connected,
                last_error=self._state.last_error,
                subscribed_topics=dict(self._state.subscribed_topics),
            )

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> dict:
        with self._lock:
            if not self._client or not self._state.connected:
                return {"ok": False, "error": "MQTT client is not connected"}
            result = self._client.publish(topic, payload=payload, qos=qos, retain=retain)
            return {"ok": result.rc == mqtt.MQTT_ERR_SUCCESS, "rc": result.rc}

    def subscribe(self, topic: str, qos: int = 0) -> dict:
        with self._lock:
            self._state.subscribed_topics[topic] = qos
            if not self._client or not self._state.connected:
                return {"ok": False, "error": "MQTT client is not connected"}
            result, mid = self._client.subscribe(topic, qos=qos)
            return {"ok": result == mqtt.MQTT_ERR_SUCCESS, "mid": mid, "rc": result}


mqtt_manager: MQTTManager | None = None


def init_mqtt_manager(session_factory: sessionmaker) -> MQTTManager:
    global mqtt_manager
    mqtt_manager = MQTTManager(session_factory=session_factory)
    return mqtt_manager
