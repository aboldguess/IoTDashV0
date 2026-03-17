"""
Mini README:
Regression tests for dashboard MQTT router bindings.
Ensures route-layer MQTT manager lookups follow live module state set at startup.
"""

import unittest

from app import mqtt_service
from app.routers import dashboard


class DashboardMQTTBindingTests(unittest.TestCase):
    def test_get_mqtt_manager_reads_live_module_state(self):
        original = mqtt_service.mqtt_manager
        try:
            sentinel = object()
            mqtt_service.mqtt_manager = sentinel
            self.assertIs(dashboard._get_mqtt_manager(), sentinel)
        finally:
            mqtt_service.mqtt_manager = original


if __name__ == "__main__":
    unittest.main()
