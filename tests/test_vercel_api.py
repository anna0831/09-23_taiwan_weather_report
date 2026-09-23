"""Integration tests for Vercel API and Static endpoints."""

import unittest
import json
import urllib.request


class TestVercelEndpoints(unittest.TestCase):
    BASE_URL = "http://127.0.0.1:3000"

    def test_01_static_index(self):
        url = f"{self.BASE_URL}/"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        content = res.read().decode("utf-8")
        self.assertIn("Taiwan Weather Forecast", content)
        self.assertIn("header-icon", content)

    def test_02_static_css(self):
        url = f"{self.BASE_URL}/style.css"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        content = res.read().decode("utf-8")
        self.assertIn("weather-icon-normal", content)

    def test_03_static_js(self):
        url = f"{self.BASE_URL}/app.js"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        content = res.read().decode("utf-8")
        self.assertIn("fetchWeatherData", content)

    def test_04_api_weather(self):
        import urllib.parse
        quoted_region = urllib.parse.quote("臺北市")
        url = f"{self.BASE_URL}/api/weather?region={quoted_region}"
        res = urllib.request.urlopen(url, timeout=5)

        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertEqual(data.get("status"), "success")
        self.assertIn("selected_forecasts", data)
        self.assertIn("map_points", data)
        self.assertGreater(len(data["selected_forecasts"]), 0)


if __name__ == "__main__":
    unittest.main()
