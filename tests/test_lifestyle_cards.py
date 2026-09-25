"""生活建議卡片與門檻規則離線單元測試 (tests/test_lifestyle_cards.py)。

測試項目涵蓋：
1. 雨量／降雨預報（帶傘建議）判斷門檻 (≥60% 建議帶傘、30~59% 可斟酌、<30% 無需帶傘、None 資料不足)
2. 術語合規性：資料僅有降雨機率時，嚴禁稱為「預測雨量」
3. 空氣品質（口罩建議）分級門檻 (良好、普通、對敏感族群不健康、對所有族群不健康、危害、None 無資料)
4. 觀測與預報標示：嚴格區分「目前觀測值」與「未來預報」
5. 颱風警報狀態判定：
   - 陸上颱風警報防颱提醒
   - 海上颱風警報海面戒備
   - 無警報常態巡邏 (「目前無相關警報」)
   - API 失敗/連線異常嚴格區分為「資料暫時無法取得」，絕不可誤判為「無颱風」
6. 日期超出範圍與過期資料防呆處理
7. SQLite 資料庫儲存與讀取 (pop 降雨機率、AirQualityObservations、TyphoonWarnings)
"""

import tempfile
import unittest
from pathlib import Path

from src.db import (
    init_db,
    save_forecasts,
    get_forecasts_by_region,
    save_air_quality,
    get_air_quality,
    save_typhoon_warning,
    get_latest_typhoon_warning,
    seed_mock_data,
)
from src.lifestyle import (
    evaluate_umbrella_advice,
    evaluate_air_quality_advice,
    evaluate_typhoon_advice,
)
from src.fetch_data import parse_weather_json, fetch_cwa_typhoon


class TestLifestyleCards(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_lifestyle.db"
        init_db(self.test_db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. 雨量／降雨預報（帶傘建議）門檻測試
    # -------------------------------------------------------------------------
    def test_umbrella_advice_thresholds(self):
        """測試帶傘建議之各區間門檻判定。"""
        # ≥60%: 建議帶傘
        adv_high = evaluate_umbrella_advice(pop=60.0, date_str="2026-09-25")
        self.assertEqual(adv_high["status"], "建議帶傘")
        self.assertEqual(adv_high["level"], "high")
        self.assertIn("務必攜帶雨傘", adv_high["advice"])

        adv_high2 = evaluate_umbrella_advice(pop=90.0, date_str="2026-09-25")
        self.assertEqual(adv_high2["status"], "建議帶傘")

        # 30% ~ 59%: 可自行斟酌
        adv_med = evaluate_umbrella_advice(pop=30.0, date_str="2026-09-25")
        self.assertEqual(adv_med["status"], "可自行斟酌")
        self.assertEqual(adv_med["level"], "medium")
        self.assertIn("折疊傘", adv_med["advice"])

        adv_med2 = evaluate_umbrella_advice(pop=55.0, date_str="2026-09-25")
        self.assertEqual(adv_med2["status"], "可自行斟酌")

        # <30%: 無需帶傘
        adv_low = evaluate_umbrella_advice(pop=29.9, date_str="2026-09-25")
        self.assertEqual(adv_low["status"], "無需帶傘")
        self.assertEqual(adv_low["level"], "low")
        self.assertIn("安心", adv_low["advice"])

        adv_low2 = evaluate_umbrella_advice(pop=0.0, date_str="2026-09-25")
        self.assertEqual(adv_low2["status"], "無需帶傘")

    def test_umbrella_terminology_compliance(self):
        """驗證若資料只有降雨機率，不可稱為『預測雨量』。"""
        adv = evaluate_umbrella_advice(pop=50.0, date_str="2026-09-25")
        self.assertEqual(adv["metric_name"], "降雨機率 (PoP)")
        self.assertNotIn("預測雨量", adv["metric_name"])
        self.assertIn("PoP", adv["rule_explanation"])

    def test_umbrella_missing_data(self):
        """測試超出涵蓋範圍或無降雨機率時的防呆回應。"""
        adv_none = evaluate_umbrella_advice(pop=None, date_str="2026-10-15")
        self.assertEqual(adv_none["status"], "資料不足")
        self.assertEqual(adv_none["badge"], "無此期間資料")
        self.assertIsNone(adv_none["pop_value"])

        adv_neg = evaluate_umbrella_advice(pop=-1.0, date_str="2026-10-15")
        self.assertEqual(adv_neg["status"], "資料不足")

    # -------------------------------------------------------------------------
    # 2. 空氣品質（口罩建議）門檻測試
    # -------------------------------------------------------------------------
    def test_air_quality_thresholds(self):
        """測試空氣品質 AQI 生活分級建議。"""
        # AQI <= 50: 良好
        aqi_good = evaluate_air_quality_advice(aqi=35.0, site_name="大同站")
        self.assertEqual(aqi_good["status"], "良好")
        self.assertEqual(aqi_good["level"], "good")
        self.assertIn("無需特別佩戴口罩", aqi_good["advice"])

        # 51 ~ 100: 普通
        aqi_mod = evaluate_air_quality_advice(aqi=75.0, site_name="忠明站")
        self.assertEqual(aqi_mod["status"], "普通")
        self.assertEqual(aqi_mod["level"], "moderate")
        self.assertIn("敏感族群可視個人狀況評估", aqi_mod["advice"])

        # 101 ~ 150: 對敏感族群不健康
        aqi_org = evaluate_air_quality_advice(aqi=120.0, site_name="前金站")
        self.assertEqual(aqi_org["status"], "對敏感族群不健康")
        self.assertEqual(aqi_org["level"], "orange")
        self.assertIn("敏感族群外出建議佩戴口罩", aqi_org["advice"])

        # 151 ~ 200: 對所有族群不健康
        aqi_red = evaluate_air_quality_advice(aqi=160.0, site_name="小港站")
        self.assertEqual(aqi_red["status"], "對所有族群不健康")
        self.assertEqual(aqi_red["level"], "unhealthy")
        self.assertIn("外出建議佩戴口罩防護", aqi_red["advice"])

        # > 200: 非常不健康 / 危害
        aqi_haz = evaluate_air_quality_advice(aqi=230.0, site_name="大城站")
        self.assertEqual(aqi_haz["status"], "非常不健康 / 危害")
        self.assertEqual(aqi_haz["level"], "hazardous")

    def test_air_quality_observation_vs_forecast_distinction(self):
        """驗證嚴格區分目前觀測值與未來預報，避免將觀測值標示為未來預報。"""
        aq_obs = evaluate_air_quality_advice(aqi=40.0, is_forecast=False)
        self.assertEqual(aq_obs["data_type"], "目前觀測值")

        aq_fc = evaluate_air_quality_advice(aqi=40.0, is_forecast=True)
        self.assertEqual(aq_fc["data_type"], "未來預報")

        # 避免醫療診斷聲明
        self.assertIn("非個人專屬醫療處方建議", aq_obs["guideline"])

    def test_air_quality_unavailable(self):
        """測試缺少 AQI 資料時之容錯處理。"""
        aq_none = evaluate_air_quality_advice(aqi=None)
        self.assertEqual(aq_none["status"], "資料暫時無法取得")
        self.assertEqual(aq_none["badge"], "無此期間資料")
        self.assertIsNone(aq_none["aqi_value"])

    # -------------------------------------------------------------------------
    # 3. 颱風資訊（物資準備建議）與異常處理測試
    # -------------------------------------------------------------------------
    def test_typhoon_no_warning(self):
        """測試常態無警報時，顯示『目前無相關警報』而非錯誤或囤貨提醒。"""
        ty_data = {
            "hasWarning": 0,
            "typhoonName": "無",
            "warningType": "無警報發布",
            "issueTime": "2026-09-25 12:00:00",
            "affectedAreas": "無",
            "is_error": False,
        }
        res = evaluate_typhoon_advice(ty_data, region_name="臺北市")
        self.assertEqual(res["status"], "目前無相關警報")
        self.assertEqual(res["badge"], "常態巡邏")
        self.assertFalse(res["is_warning_active"])
        self.assertFalse(res["is_error"])
        self.assertIn("無須提前恐慌囤積物資", res["advice"])

    def test_typhoon_land_warning(self):
        """測試陸上颱風警報時，顯示警戒區域與官方防颱物資準備建議。"""
        ty_data = {
            "hasWarning": 1,
            "typhoonName": "山陀兒",
            "warningType": "海上陸上颱風警報",
            "issueTime": "2026-09-25 08:30:00",
            "affectedAreas": "高雄市、屏東縣、臺東縣",
            "is_error": False,
        }
        res = evaluate_typhoon_advice(ty_data, region_name="高雄市")
        self.assertIn("陸上颱風警報", res["status"])
        self.assertEqual(res["badge"], "警戒防颱")
        self.assertTrue(res["is_warning_active"])
        self.assertIn("加固門窗", res["advice"])
        self.assertIn("家庭常備物資", res["advice"])
        # 不商業推銷特定賣場
        self.assertNotIn("全聯", res["advice"])

    def test_typhoon_sea_warning(self):
        """測試僅有海上颱風警報時之海面警戒提醒。"""
        ty_data = {
            "hasWarning": 1,
            "typhoonName": "天兔",
            "warningType": "海上颱風警報",
            "issueTime": "2026-09-25 08:30:00",
            "affectedAreas": "巴士海峽、臺灣東南部海面",
            "is_error": False,
        }
        res = evaluate_typhoon_advice(ty_data, region_name="基隆市")
        self.assertIn("海上颱風警報", res["status"])
        self.assertEqual(res["badge"], "海上警戒")
        self.assertTrue(res["is_warning_active"])
        self.assertIn("切勿前往海邊觀浪", res["advice"])

    def test_typhoon_api_failure_strictly_distinguished(self):
        """關鍵測試：當 API 連線失敗或傳回錯誤時，必須顯示『資料暫時無法取得』，絕不能當作『無颱風』。"""
        # 情況 A: None
        res_none = evaluate_typhoon_advice(None)
        self.assertEqual(res_none["status"], "資料暫時無法取得")
        self.assertTrue(res_none["is_error"])
        self.assertFalse(res_none["is_warning_active"])
        self.assertNotEqual(res_none["status"], "目前無相關警報")

        # 情況 B: is_error=True
        error_data = {"is_error": True, "error_message": "Connection Timeout"}
        res_err = evaluate_typhoon_advice(error_data)
        self.assertEqual(res_err["status"], "資料暫時無法取得")
        self.assertTrue(res_err["is_error"])
        self.assertNotEqual(res_err["status"], "目前無相關警報")

    # -------------------------------------------------------------------------
    # 4. 資料庫儲存與讀取 (pop 降雨機率、空品、颱風) 整合測試
    # -------------------------------------------------------------------------
    def test_db_storage_pop_and_lifestyle(self):
        """測試 SQLite 資料庫能正確存取 pop 欄位、空氣品質與颱風警報。"""
        forecasts = [
            {"regionName": "臺北市", "dataDate": "2026-09-25", "mint": 24.0, "maxt": 31.0, "pop": 65.0},
        ]
        save_forecasts(forecasts, self.test_db_path)
        df = get_forecasts_by_region("臺北市", self.test_db_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["pop"], 65.0)

        # 測試空氣品質儲存與查詢
        aq_records = [
            {"regionName": "臺北市", "siteName": "大同站", "aqi": 45.0, "status": "良好", "obsTime": "2026-09-25 12:00:00"}
        ]
        save_air_quality(aq_records, self.test_db_path)
        aq_retrieved = get_air_quality("臺北市", self.test_db_path)
        self.assertIsNotNone(aq_retrieved)
        self.assertEqual(aq_retrieved["aqi"], 45.0)
        self.assertEqual(aq_retrieved["siteName"], "大同站")

        # 測試颱風警報儲存與查詢
        save_typhoon_warning({
            "hasWarning": 0,
            "typhoonName": "無",
            "warningType": "無警報發布",
            "issueTime": "2026-09-25 12:00:00",
            "affectedAreas": "無"
        }, self.test_db_path)
        ty_retrieved = get_latest_typhoon_warning(self.test_db_path)
        self.assertIsNotNone(ty_retrieved)
        self.assertEqual(ty_retrieved["hasWarning"], 0)

    # -------------------------------------------------------------------------
    # 5. CWA JSON 降雨機率 (PoP) 提取解析測試
    # -------------------------------------------------------------------------
    def test_parse_weather_json_pop_extraction(self):
        """測試 parse_weather_json 能從 F-D0047 或 F-C0032 提取降雨機率 (PoP)。"""
        sample_cwa_with_pop = {
            "records": {
                "Locations": [
                    {
                        "Location": [
                            {
                                "LocationName": "臺北市",
                                "WeatherElement": [
                                    {
                                        "ElementName": "最低溫度",
                                        "Time": [
                                            {"StartTime": "2026-09-25 06:00:00", "ElementValue": [{"MinTemperature": "23"}]}
                                        ]
                                    },
                                    {
                                        "ElementName": "最高溫度",
                                        "Time": [
                                            {"StartTime": "2026-09-25 06:00:00", "ElementValue": [{"MaxTemperature": "30"}]}
                                        ]
                                    },
                                    {
                                        "ElementName": "12小時降雨機率",
                                        "Time": [
                                            {"StartTime": "2026-09-25 06:00:00", "ElementValue": [{"ProbabilityOfPrecipitation": "70"}]}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        df = parse_weather_json(sample_cwa_with_pop)
        self.assertFalse(df.empty)
        row = df[df["regionName"] == "臺北市"].iloc[0]
        self.assertEqual(row["mint"], 23.0)
        self.assertEqual(row["maxt"], 30.0)
        self.assertEqual(row["pop"], 70.0)


if __name__ == "__main__":
    unittest.main()
