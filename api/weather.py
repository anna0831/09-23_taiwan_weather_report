"""Vercel Serverless Function: /api/weather

Provides weather data, coordinates, 7-day forecast, and optional CWA sync.
Compatible with Vercel Python Runtime and local Python servers.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import sqlite3

# 將專案根目錄加入 sys.path 以便匯入 src 模組
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from src.config import REGION_COORDINATES, DB_PATH, COUNTY_TO_REGION
    from src.db import (
        get_connection,
        init_db,
        get_distinct_regions,
        get_forecasts_by_region,
        get_all_forecasts,
        get_metadata,
        set_metadata,
        seed_mock_data,
        get_air_quality,
        get_latest_typhoon_warning,
    )
    from src.lifestyle import (
        evaluate_umbrella_advice,
        evaluate_air_quality_advice,
        evaluate_typhoon_advice,
    )
except ImportError:
    REGION_COORDINATES = {}
    COUNTY_TO_REGION = {}
    DB_PATH = BASE_DIR / "data" / "data.db"


def get_weather_payload(selected_region: str = None, selected_date: str = None) -> dict:
    """組織天氣預報資料、地圖定位點與三張生活建議卡片。"""
    from datetime import datetime

    # 確保資料庫存在與初始化
    init_db()

    # 讀取可用地區清單，若空則自動播種示範資料
    try:
        regions = get_distinct_regions()
        if not regions:
            seed_mock_data()
            regions = get_distinct_regions()
    except Exception:
        regions = []

    # 預設優先選擇
    default_priority = ["臺北市", "台北市", "北部地區", "新北市", "臺中市", "高雄市"]
    if not selected_region or selected_region not in regions:
        # 若傳入縣市但資料庫僅有分區 (或相反)，透過對應表查找
        fallback_mapped = COUNTY_TO_REGION.get(selected_region) if selected_region else None
        if fallback_mapped and fallback_mapped in regions:
            selected_region = fallback_mapped
        else:
            selected_region = None
            for pref in default_priority:
                if pref in regions:
                    selected_region = pref
                    break
            if not selected_region and regions:
                selected_region = regions[0]

    # 讀取所選地區的 7 天預報
    selected_forecasts = []
    if selected_region:
        try:
            df_sel = get_forecasts_by_region(selected_region)
            selected_forecasts = df_sel.to_dict(orient="records")
        except Exception:
            selected_forecasts = []

    # 讀取所有預報並彙整今日/最新地圖點
    all_forecasts = []
    try:
        df_all = get_all_forecasts()
        all_forecasts = df_all.to_dict(orient="records")
    except Exception:
        all_forecasts = []

    # 抓取每個地區最近一天的溫度作為地圖標註點
    map_points = []
    seen_regions = set()
    for row in all_forecasts:
        reg = row.get("regionName")
        if reg and reg not in seen_regions and reg in REGION_COORDINATES:
            seen_regions.add(reg)
            coord = REGION_COORDINATES[reg]
            mint = float(row.get("mint", 20.0))
            maxt = float(row.get("maxt", 28.0))
            avg = round((mint + maxt) / 2, 1)
            map_points.append({
                "regionName": reg,
                "label": coord.get("label", reg),
                "lat": coord["lat"],
                "lon": coord["lon"],
                "dataDate": row.get("dataDate", ""),
                "mint": mint,
                "maxt": maxt,
                "avg": avg,
            })

    # 若特定地區在地圖點中未包含，補齊其餘已知縣市
    for reg, coord in REGION_COORDINATES.items():
        if reg not in seen_regions and (not regions or reg in regions):
            seen_regions.add(reg)
            map_points.append({
                "regionName": reg,
                "label": coord.get("label", reg),
                "lat": coord["lat"],
                "lon": coord["lon"],
                "dataDate": "",
                "mint": 24.0,
                "maxt": 30.0,
                "avg": 27.0,
            })

    # 取得最後同步時間 (修正固定過期時間問題)
    try:
        last_sync = get_metadata("last_sync_time")
        if not last_sync:
            last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            set_metadata("last_sync_time", last_sync)
    except Exception:
        last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    # 生活建議卡片計算 (雨量/帶傘、空氣品質/口罩、颱風資訊/物資)
    # -------------------------------------------------------------------------
    # 1. 雨量／降雨預報（帶傘建議）
    target_row = None
    today_str = datetime.now().strftime("%Y-%m-%d")

    if selected_date:
        for r in selected_forecasts:
            if r.get("dataDate") == selected_date:
                target_row = r
                break
    else:
        # 優先尋找今日或第一筆
        for r in selected_forecasts:
            if r.get("dataDate") == today_str:
                target_row = r
                break
        if not target_row and selected_forecasts:
            target_row = selected_forecasts[0]

    if target_row:
        umbrella_advice = evaluate_umbrella_advice(
            pop=target_row.get("pop"),
            date_str=target_row.get("dataDate", ""),
            region_name=selected_region or ""
        )
    else:
        umbrella_advice = evaluate_umbrella_advice(
            pop=None,
            date_str=selected_date or today_str,
            region_name=selected_region or ""
        )

    # 2. 空氣品質（口罩建議）
    try:
        aq_record = get_air_quality(selected_region or "")
    except Exception:
        aq_record = None

    if aq_record:
        air_quality_advice = evaluate_air_quality_advice(
            aqi=aq_record.get("aqi"),
            site_name=aq_record.get("siteName", ""),
            obs_time=aq_record.get("obsTime", ""),
            is_forecast=False,
            region_name=selected_region or ""
        )
    else:
        air_quality_advice = evaluate_air_quality_advice(
            aqi=None,
            region_name=selected_region or ""
        )

    # 3. 颱風資訊（物資建議）
    try:
        ty_record = get_latest_typhoon_warning()
    except Exception:
        ty_record = None

    typhoon_advice = evaluate_typhoon_advice(
        ty_record,
        region_name=selected_region or ""
    )

    return {
        "status": "success",
        "last_sync": last_sync,
        "selected_region": selected_region,
        "selected_date": target_row.get("dataDate") if target_row else selected_date,
        "regions": regions,
        "selected_forecasts": selected_forecasts,
        "map_points": map_points,
        "lifestyle_advice": {
            "umbrella": umbrella_advice,
            "air_quality": air_quality_advice,
            "typhoon": typhoon_advice,
        },
        "total_records": len(all_forecasts)
    }


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function HTTP Request Handler"""

    def do_OPTIONS(self):
        """處理 CORS 預檢請求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """處理 GET 請求，返回氣象資料 JSON"""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        region = query_params.get("region", [None])[0]
        date = query_params.get("date", [None])[0]
        sync_requested = query_params.get("sync", ["0"])[0] in ["1", "true"]

        sync_result = None
        if sync_requested:
            try:
                from src.fetch_data import sync_cwa_to_db, fetch_moenv_aqi, fetch_cwa_typhoon
                from src.db import save_air_quality, save_typhoon_warning
                success, msg, saved = sync_cwa_to_db()
                # 同步空品
                try:
                    moenv_records = fetch_moenv_aqi()
                    if moenv_records:
                        save_air_quality(moenv_records)
                except Exception:
                    pass
                # 同步颱風
                try:
                    typhoon_data = fetch_cwa_typhoon()
                    if typhoon_data:
                        save_typhoon_warning(typhoon_data)
                except Exception:
                    pass

                if success:
                    sync_result = f"已成功更新 {saved} 筆氣象資料"
                else:
                    sync_result = f"同步提醒: {msg}"
            except Exception as e:
                sync_result = f"同步發生錯誤: {str(e)}"

        try:
            payload = get_weather_payload(region, date)
            if sync_result:
                payload["sync_message"] = sync_result

            response_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(response_data)
        except Exception as e:
            err_data = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_data)


# 支援本機直接執行測試
if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(("127.0.0.1", 8080), handler)
    print("Vercel Function Local test running at http://127.0.0.1:8080")
    server.serve_forever()
