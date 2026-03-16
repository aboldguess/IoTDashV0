"""
Mini README:
Unit tests for door-sensor parsing and OPEN/CLOSED state mapping.
These tests validate the new on/off door widget data contract in a fast, auditable way.
"""

import unittest

from fastapi import HTTPException

from app.routers.dashboard import ALLOWED_WIDGET_TYPES
from app.sensor_utils import parse_sensor_value, sensor_value_to_door_state


class DoorSensorParsingTests(unittest.TestCase):
    """Focused tests for accepted door sensor payload formats."""

    def test_widget_type_includes_door(self):
        self.assertIn("door", ALLOWED_WIDGET_TYPES)

    def test_on_off_and_open_closed_values_parse(self):
        self.assertEqual(parse_sensor_value("on"), 1.0)
        self.assertEqual(parse_sensor_value("open"), 1.0)
        self.assertEqual(parse_sensor_value("true"), 1.0)
        self.assertEqual(parse_sensor_value("off"), 0.0)
        self.assertEqual(parse_sensor_value("closed"), 0.0)
        self.assertEqual(parse_sensor_value("false"), 0.0)

    def test_numeric_string_value_parses(self):
        self.assertEqual(parse_sensor_value("1"), 1.0)
        self.assertEqual(parse_sensor_value("0"), 0.0)
        self.assertEqual(parse_sensor_value("0.6"), 0.6)

    def test_invalid_sensor_value_raises_http_422(self):
        with self.assertRaises(HTTPException) as context:
            parse_sensor_value("totally-invalid")
        self.assertEqual(context.exception.status_code, 422)

    def test_sensor_value_to_door_state_threshold(self):
        self.assertEqual(sensor_value_to_door_state(1.0), "OPEN")
        self.assertEqual(sensor_value_to_door_state(0.5), "OPEN")
        self.assertEqual(sensor_value_to_door_state(0.49), "CLOSED")


if __name__ == "__main__":
    unittest.main()
