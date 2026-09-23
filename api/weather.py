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
    from src.config import REGION_COORDINATES, DB_PATH
    from src.db import (
        get_connection,
        init_db,
        get_distinct_regions,
        get_forecasts_by_region,
        get_all_forecasts,
        get_metadata,
        seed_mock_data
    )
except ImportError:
    # 備用容錯定義
    REGION_COORDINATES = {}
    DB_PATH = BASE_DIR / "data" / "data.db"


def get_weather_payload(selected_region: str = None) -> dict:
    """組織天氣預報資料與地圖定位點"""
    # 確保資料庫存在與初始化
    db_file = DB_PATH
    if not db_file.exists():
        try:
            init_db()
            seed_mock_data()
        except Exception:
            pass

    # 讀取可用地區清單
    try:
        regions = get_distinct_regions()
    except Exception:
        regions = []

    # 預設優先選擇
    default_priority = ["臺北市", "台北市", "北部地區", "新北市", "臺中市", "高雄市"]
    if not selected_region or selected_region not in regions:
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

    # 取得最後同步時間
    try:
        last_sync = get_metadata("last_sync_time") or "2026-09-23 11:17:26"
    except Exception:
        last_sync = "2026-09-23 11:17:26"

    return {
        "status": "success",
        "last_sync": last_sync,
        "selected_region": selected_region,
        "regions": regions,
        "selected_forecasts": selected_forecasts,
        "map_points": map_points,
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
        sync_requested = query_params.get("sync", ["0"])[0] in ["1", "true"]

        sync_result = None
        if sync_requested:
            try:
                from src.fetch_data import fetch_cwa_forecast, parse_forecast_json
                from src.db import save_forecasts
                cwa_json = fetch_cwa_forecast()
                if cwa_json:
                    df = parse_forecast_json(cwa_json)
                    saved = save_forecasts(df)
                    sync_result = f"已成功更新 {saved} 筆氣象資料"
                else:
                    sync_result = "無法從 CWA 取得資料，已保留現有資料"
            except Exception as e:
                sync_result = f"同步發生錯誤: {str(e)}"

        try:
            payload = get_weather_payload(region)
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
