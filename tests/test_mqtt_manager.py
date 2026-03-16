"""
Mini README:
Unit tests for MQTT manager behavior that does not require a running broker.
These checks protect connection-state and publish/subscribe guardrails.
"""

import unittest

from app.database import SessionLocal
from app.mqtt_service import MQTTManager


class MQTTManagerOfflineTests(unittest.TestCase):
    def setUp(self):
        self.manager = MQTTManager(session_factory=SessionLocal)

    def tearDown(self):
        self.manager.disconnect()

    def test_publish_fails_cleanly_when_not_connected(self):
        result = self.manager.publish(topic="sensors/test", payload="1")
        self.assertFalse(result["ok"])
        self.assertIn("not connected", result["error"])

    def test_subscribe_fails_cleanly_when_not_connected(self):
        result = self.manager.subscribe(topic="sensors/test", qos=0)
        self.assertFalse(result["ok"])
        self.assertIn("not connected", result["error"])

    def test_normalize_broker_endpoint_accepts_scheme_and_port(self):
        host, port = self.manager._normalize_broker_endpoint("mqtt://172.19.0.29:1883", 1884)
        self.assertEqual(host, "172.19.0.29")
        self.assertEqual(port, 1883)

    def test_normalize_broker_endpoint_accepts_host_with_inline_port(self):
        host, port = self.manager._normalize_broker_endpoint("172.19.0.29:1883", 1884)
        self.assertEqual(host, "172.19.0.29")
        self.assertEqual(port, 1883)


if __name__ == "__main__":
    unittest.main()
