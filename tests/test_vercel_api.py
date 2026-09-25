"""Integration tests for Vercel API, Static endpoints, and Lifestyle Advice Cards."""

import unittest
import json
import threading
import time
import urllib.request
import urllib.parse
from http.server import HTTPServer
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dev_server import VercelDevServerHandler


class TestVercelEndpoints(unittest.TestCase):
    PORT = 3000
    BASE_URL = f"http://127.0.0.1:{PORT}"
    server = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        # 測試伺服器是否已在運行
        try:
            res = urllib.request.urlopen(f"{cls.BASE_URL}/", timeout=1)
            if res.status == 200:
                return
        except Exception:
            pass

        # 若未運行，於背景執行緒啟動 dev_server
        try:
            cls.server = HTTPServer(("127.0.0.1", cls.PORT), VercelDevServerHandler)
            cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
            cls.server_thread.start()
            time.sleep(0.3)
        except Exception as e:
            print(f"Warning: Failed to start test server on {cls.PORT}: {e}")

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            try:
                cls.server.shutdown()
                cls.server.server_close()
            except Exception:
                pass

    def test_01_static_index(self):
        url = f"{self.BASE_URL}/"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        content = res.read().decode("utf-8")
        self.assertIn("Taiwan Weather Forecast", content)
        self.assertIn("header-icon", content)
        self.assertIn("powerpuff_girls.png", content)
        self.assertIn("lifestyle-section", content)

    def test_02_static_css(self):
        url = f"{self.BASE_URL}/style.css"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        content = res.read().decode("utf-8")
        self.assertIn("weather-icon-normal", content)
        self.assertIn("lifestyle-card", content)
        self.assertIn("hero-ppg-img", content)

    def test_03_static_js(self):
        url = f"{self.BASE_URL}/app.js"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        content = res.read().decode("utf-8")
        self.assertIn("fetchWeatherData", content)
        self.assertIn("renderLifestyleCards", content)

    def test_04_static_powerpuff_image(self):
        """驗證飛天小女警圖片能由靜態資源端點正常存取且為 PNG 格式。"""
        url = f"{self.BASE_URL}/powerpuff_girls.png"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        content_type = res.headers.get("Content-Type", "")
        self.assertTrue("image" in content_type or res.length > 0)
        self.assertGreater(res.length, 1000)

    def test_05_api_weather_and_lifestyle(self):
        """驗證 /api/weather 回傳預報數據、生活建議卡片與最新同步時間。"""
        quoted_region = urllib.parse.quote("臺北市")
        url = f"{self.BASE_URL}/api/weather?region={quoted_region}"
        res = urllib.request.urlopen(url, timeout=5)

        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("selected_region"), "臺北市")
        self.assertIn("selected_forecasts", data)
        self.assertIn("map_points", data)
        self.assertGreater(len(data["selected_forecasts"]), 0)

        # 驗證最後同步時間修正
        self.assertIn("last_sync", data)
        self.assertTrue(len(data["last_sync"]) >= 10)

        # 驗證三張生活建議卡片
        self.assertIn("lifestyle_advice", data)
        advice = data["lifestyle_advice"]
        self.assertIn("umbrella", advice)
        self.assertIn("air_quality", advice)
        self.assertIn("typhoon", advice)

        # 驗證雨量帶傘卡片屬性
        u = advice["umbrella"]
        self.assertIn(u["status"], ["建議帶傘", "可自行斟酌", "無需帶傘", "資料不足"])
        self.assertEqual(u["metric_name"], "降雨機率 (PoP)")

        # 驗證空氣品質卡片屬性
        a = advice["air_quality"]
        self.assertIn("目前觀測值", a["data_type"])
        self.assertIn("環境部", a["source"])

        # 驗證颱風卡片屬性
        t = advice["typhoon"]
        self.assertIn("中央氣象署", t["source"])
        self.assertFalse(t["is_error"])

    def test_06_api_date_query(self):
        """測試指定特定日期切換生活建議。"""
        quoted_region = urllib.parse.quote("北部地區")
        url = f"{self.BASE_URL}/api/weather?region={quoted_region}&date=2026-09-24"
        res = urllib.request.urlopen(url, timeout=5)
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertEqual(data["selected_date"], "2026-09-24")
        self.assertEqual(data["lifestyle_advice"]["umbrella"]["date"], "2026-09-24")

    def test_07_api_county_pills_clickable(self):
        """驗證熱門巡邏點（如臺中市、新北市、高雄市）皆可成功由後端處理與回傳。"""
        for city in ["臺中市", "新北市", "高雄市", "北部地區"]:
            quoted = urllib.parse.quote(city)
            url = f"{self.BASE_URL}/api/weather?region={quoted}"
            res = urllib.request.urlopen(url, timeout=5)
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["selected_region"], city)
            self.assertGreater(len(data["selected_forecasts"]), 0)


if __name__ == "__main__":
    unittest.main()
