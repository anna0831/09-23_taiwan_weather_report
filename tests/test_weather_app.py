"""單元與功能整合測試 (離線驗證，不依賴外部網路與真實 API Key)。

驗證項目：
1. SQLite 資料庫初始化與資料表結構
2. 參數化 SQL 查詢與防 SQL Injection
3. 重複匯入更新 (UPSERT) 機制 (避免重複資料)
4. CWA JSON 結構解析邏輯 (MinT, MaxT, 跨日時段與多日彙整)
5. JSON 異常與邊界值容錯處理 (缺少元素、非數值字串等)
6. 無 API Key 呼叫 sync_cwa_to_db 之優雅防呆回應
7. 溫度顏色區間判定邏輯 (<20, 20-25, 25-30, >30)
8. 地理座標對應與 Folium 標記產製
"""

import tempfile
import unittest
from pathlib import Path

from src.config import get_temp_color, REGION_COORDINATES
from src.db import (
    init_db,
    save_forecasts,
    get_distinct_regions,
    get_forecasts_by_region,
    get_distinct_dates,
    get_forecasts_by_date,
    seed_mock_data,
    get_connection,
)
from src.fetch_data import parse_weather_json, sync_cwa_to_db
import folium


class TestWeatherApp(unittest.TestCase):
    def setUp(self):
        # 建立獨立的測試用暫存資料庫
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_data.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_init_and_table(self):
        """測試資料庫建立與 TemperatureForecasts 資料表結構。"""
        init_db(self.test_db_path)
        self.assertTrue(self.test_db_path.exists())

        conn = get_connection(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TemperatureForecasts';")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "TemperatureForecasts")
        conn.close()

    def test_save_and_upsert_logic(self):
        """測試重複匯入時更新原紀錄，避免重複資料 (UPSERT 驗證)。"""
        init_db(self.test_db_path)

        data_initial = [
            {"regionName": "北部地區", "dataDate": "2026-04-14", "mint": 18.0, "maxt": 25.0},
            {"regionName": "中部地區", "dataDate": "2026-04-14", "mint": 20.0, "maxt": 29.0},
        ]
        count1 = save_forecasts(data_initial, self.test_db_path)
        self.assertEqual(count1, 2)

        # 查詢目前總筆數
        conn = get_connection(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM TemperatureForecasts;")
        self.assertEqual(cursor.fetchone()["total"], 2)

        # 重複插入相同地區與日期，但更新溫度數值
        data_updated = [
            {"regionName": "北部地區", "dataDate": "2026-04-14", "mint": 17.5, "maxt": 26.5},
        ]
        count2 = save_forecasts(data_updated, self.test_db_path)
        self.assertEqual(count2, 1)

        # 驗證總筆數仍為 2，並無重複產生
        cursor.execute("SELECT COUNT(*) AS total FROM TemperatureForecasts;")
        self.assertEqual(cursor.fetchone()["total"], 2)

        # 驗證數值已成功更新
        cursor.execute(
            "SELECT mint, maxt FROM TemperatureForecasts WHERE regionName = ? AND dataDate = ?;",
            ("北部地區", "2026-04-14"),
        )
        row = cursor.fetchone()
        self.assertEqual(row["mint"], 17.5)
        self.assertEqual(row["maxt"], 26.5)
        conn.close()

    def test_parameterized_queries(self):
        """測試參數化 SQL 查詢 (依地區與依日期)。"""
        seed_mock_data(self.test_db_path)

        # 測試地區清單
        regions = get_distinct_regions(self.test_db_path)
        self.assertIn("北部地區", regions)
        self.assertIn("中部地區", regions)
        self.assertIn("南部地區", regions)

        # 測試依地區查詢
        df_central = get_forecasts_by_region("中部地區", self.test_db_path)
        self.assertFalse(df_central.empty)
        self.assertEqual(len(df_central), 7)
        self.assertTrue(all(df_central["regionName"] == "中部地區"))

        # 測試防 SQL Injection
        df_malicious = get_forecasts_by_region("中部地區' OR '1'='1", self.test_db_path)
        self.assertTrue(df_malicious.empty)

        # 測試依日期查詢
        dates = get_distinct_dates(self.test_db_path)
        self.assertIn("2026-09-21", dates)

        df_date = get_forecasts_by_date("2026-09-21", self.test_db_path)
        self.assertEqual(len(df_date), 6)  # 6 個預設地區

    def test_temp_color_mapping(self):
        """測試溫度分級顏色規則。"""
        self.assertEqual(get_temp_color(18.0), "blue")    # < 20
        self.assertEqual(get_temp_color(19.9), "blue")    # < 20
        self.assertEqual(get_temp_color(20.0), "green")   # 20 - 25
        self.assertEqual(get_temp_color(25.0), "green")   # 20 - 25
        self.assertEqual(get_temp_color(25.1), "orange")  # 25 - 30
        self.assertEqual(get_temp_color(30.0), "orange")  # 25 - 30
        self.assertEqual(get_temp_color(30.1), "red")     # > 30
        self.assertEqual(get_temp_color(35.0), "red")     # > 30

    def test_cwa_json_parser_standard(self):
        """測試 JSON 解析模組對標準 CWA 結構之提取與跨日時段彙整。"""
        sample_cwa_json = {
            "records": {
                "location": [
                    {
                        "locationName": "北部地區",
                        "weatherElement": [
                            {
                                "elementName": "MinT",
                                "time": [
                                    {
                                        "startTime": "2026-04-14 06:00:00",
                                        "endTime": "2026-04-14 18:00:00",
                                        "parameter": {"parameterName": "19", "parameterUnit": "C"},
                                    },
                                    {
                                        "startTime": "2026-04-14 18:00:00",
                                        "endTime": "2026-04-15 06:00:00",
                                        "parameter": {"parameterName": "18", "parameterUnit": "C"},
                                    },
                                    {
                                        "startTime": "2026-04-15 06:00:00",
                                        "endTime": "2026-04-15 18:00:00",
                                        "parameter": {"parameterName": "20", "parameterUnit": "C"},
                                    },
                                ],
                            },
                            {
                                "elementName": "MaxT",
                                "time": [
                                    {
                                        "startTime": "2026-04-14 06:00:00",
                                        "endTime": "2026-04-14 18:00:00",
                                        "parameter": {"parameterName": "26", "parameterUnit": "C"},
                                    },
                                    {
                                        "startTime": "2026-04-14 18:00:00",
                                        "endTime": "2026-04-15 06:00:00",
                                        "parameter": {"parameterName": "24", "parameterUnit": "C"},
                                    },
                                    {
                                        "startTime": "2026-04-15 06:00:00",
                                        "endTime": "2026-04-15 18:00:00",
                                        "parameter": {"parameterName": "28", "parameterUnit": "C"},
                                    },
                                ],
                            },
                        ],
                    }
                ]
            }
        }

        df = parse_weather_json(sample_cwa_json)
        self.assertEqual(len(df), 2)  # 2026-04-14, 2026-04-15
        
        day1 = df[df["dataDate"] == "2026-04-14"].iloc[0]
        self.assertEqual(day1["regionName"], "北部地區")
        self.assertEqual(day1["mint"], 18.0)  # min(19, 18)
        self.assertEqual(day1["maxt"], 26.0)  # max(26, 24)

        day2 = df[df["dataDate"] == "2026-04-15"].iloc[0]
        self.assertEqual(day2["mint"], 20.0)
        self.assertEqual(day2["maxt"], 28.0)

    def test_cwa_json_parser_edge_cases(self):
        """測試 JSON 解析容錯性：空資料、缺少元素、無效數值字串。"""
        # 空記錄
        df_empty = parse_weather_json({})
        self.assertTrue(df_empty.empty)

        # 包含缺少 MinT/MaxT 或格式異常
        corrupted_json = {
            "records": {
                "location": [
                    {
                        "locationName": "測試地區",
                        "weatherElement": [
                            {
                                "elementName": "Wx",  # 非溫度要素
                                "time": [{"startTime": "2026-04-14 06:00:00", "parameter": {"parameterName": "晴天"}}],
                            },
                            {
                                "elementName": "MinT",
                                "time": [{"startTime": "2026-04-14 06:00:00", "parameter": {"parameterName": "N/A"}}],  # 無效數值
                            },
                        ],
                    }
                ]
            }
        }
        df_corrupted = parse_weather_json(corrupted_json)
        self.assertTrue(df_corrupted.empty)

    def test_sync_cwa_to_db_without_api_key(self):
        """測試未設定 API Key 時，sync_cwa_to_db 會回傳錯誤訊息而非崩潰。"""
        success, msg, count = sync_cwa_to_db(api_key="", db_path=self.test_db_path)
        self.assertFalse(success)
        self.assertEqual(count, 0)
        self.assertIn("未設定 CWA API Key", msg)

    def test_folium_map_generation(self):
        """測試 Folium 地圖標記產製與屬性。"""
        m = folium.Map(location=[23.7, 120.9], zoom_start=7)
        for r_name, coord in REGION_COORDINATES.items():
            color = get_temp_color(24.0)
            folium.CircleMarker(
                location=[coord["lat"], coord["lon"]],
                radius=15,
                color=color,
                fill=True,
                fill_color=color,
                popup=f"{r_name} Min: 20 Max: 28",
            ).add_to(m)

        html_output = m.get_root().render()
        self.assertIn("北部地區", html_output)
        self.assertIn("中部地區", html_output)


if __name__ == "__main__":
    unittest.main()
