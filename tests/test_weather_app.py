"""單元與功能整合測試。

驗證項目：
1. SQLite 資料庫初始化與資料表建立
2. 參數化 SQL 查詢
3. 重複匯入更新 (UPSERT) 機制驗證 (避免重複資料)
4. CWA JSON 結構解析邏輯 (MinT, MaxT, 日期整合)
5. 溫度顏色區間判定邏輯
6. 地理座標對應與 Folium 標記生成
"""

import os
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import folium

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
from src.fetch_data import parse_weather_json


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
        """測試重複匯入時更新原紀錄，避免重複資料 (約束測試)。"""
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

        # 測試依日期查詢
        dates = get_distinct_dates(self.test_db_path)
        self.assertIn("2026-04-14", dates)

        df_date = get_forecasts_by_date("2026-04-14", self.test_db_path)
        self.assertEqual(len(df_date), 6)  # 6 個預設地區

    def test_temp_color_mapping(self):
        """測試溫度分級顏色規則 (圖二 Step 17)。"""
        self.assertEqual(get_temp_color(18.0), "blue")    # < 20
        self.assertEqual(get_temp_color(20.0), "green")   # 20 - 25
        self.assertEqual(get_temp_color(25.0), "green")   # 20 - 25
        self.assertEqual(get_temp_color(27.5), "orange")  # 25 - 30
        self.assertEqual(get_temp_color(30.0), "orange")  # 25 - 30
        self.assertEqual(get_temp_color(31.5), "red")     # > 30

    def test_cwa_json_parser(self):
        """測試 JSON 解析模組對 CWA 階層結構之提取與彙整。"""
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
                                ],
                            },
                        ],
                    }
                ]
            }
        }

        df = parse_weather_json(sample_cwa_json)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["regionName"], "北部地區")
        self.assertEqual(df.iloc[0]["dataDate"], "2026-04-14")
        self.assertEqual(df.iloc[0]["mint"], 18.0)  # min(19, 18)
        self.assertEqual(df.iloc[0]["maxt"], 26.0)  # max(26, 24)

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

        # 確保能成功輸出 HTML 字串
        html_output = m.get_root().render()
        self.assertIn("北部地區", html_output)
        self.assertIn("中部地區", html_output)


if __name__ == "__main__":
    unittest.main()
