"""中央氣象署 (CWA) 開放資料 API 抓取與 JSON 解析模組。

對應圖二之 Step 4、5、6、7。
使用 requests 取得 JSON，解析 MinT (最低溫) 與 MaxT (最高溫)，
使用 pandas 整理資料結構，最後存入 SQLite 資料庫。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
import pandas as pd

from src.config import CWA_API_KEY, CWA_API_URL
from src.db import save_forecasts

logger = logging.getLogger(__name__)


def fetch_cwa_json(api_key: Optional[str] = None) -> Dict[str, Any]:
    """向中央氣象署 Open Data API 發送請求並回傳原始 JSON 資料。
    
    對應圖二 Step 4:
    url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-003'
    headers = {'Authorization': api_key}
    resp = requests.get(url, headers=headers)
    """
    key = api_key or CWA_API_KEY
    if not key:
        raise ValueError("未設定 CWA API Key！請在環境變數或 .env 中設定 CWA_API_KEY。")

    params = {
        "Authorization": key,
        "format": "JSON",
    }
    headers = {
        "Authorization": key,
        "User-Agent": "Taiwan-Weather-App/1.0",
    }

    try:
        response = requests.get(
            CWA_API_URL,
            headers=headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        
        # 檢查氣象署回傳的 success 旗標
        if isinstance(data, dict) and data.get("success") == "false":
            msg = data.get("message", "API 回應錯誤")
            raise RuntimeError(f"CWA API 回應失敗: {msg}")

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"發送 CWA API 請求時發生網路錯誤: {e}")
        raise


def parse_weather_json(data: Dict[str, Any]) -> pd.DataFrame:
    """解析 CWA JSON 資料結構並整理為 DataFrame。
    
    對應圖二 Step 5、6、7：
    1. 找到 records -> location
    2. 取出 locationName (地區名稱)
    3. 找到 weatherElement 中的 MinT 與 MaxT
    4. 依日期 (YYYY-MM-DD) 整合最低溫與最高溫
    5. 產出欄位：regionName, dataDate, mint, maxt
    """
    records_section = data.get("records", {})
    # 支援 location 或 locations
    location_list = records_section.get("location") or records_section.get("locations") or []

    if not location_list and "dataset" in records_section:
        location_list = records_section["dataset"].get("location", [])

    rows: List[Dict[str, Any]] = []

    for loc in location_list:
        region_name = loc.get("locationName", "").strip()
        if not region_name:
            continue

        weather_elements = loc.get("weatherElement", [])
        
        # 暫存每日的溫度數值清單，格式: { '2026-04-14': {'min': [18, 19], 'max': [26, 27]} }
        daily_temps: Dict[str, Dict[str, List[float]]] = {}

        for elem in weather_elements:
            elem_name = elem.get("elementName", "")
            time_intervals = elem.get("time", [])

            if elem_name not in ["MinT", "MaxT"]:
                continue

            for t_item in time_intervals:
                # 取得開始時間 (格式例: 2026-04-14T06:00:00+08:00 或 2026-04-14 06:00:00)
                start_time_str = t_item.get("startTime", "")
                if not start_time_str:
                    continue
                
                # 擷取日期部分 YYYY-MM-DD
                data_date = start_time_str[:10]

                # 取得溫度數值
                param = t_item.get("parameter", {})
                param_name = param.get("parameterName")
                if param_name is None:
                    # 部分結構可能直接存在 elementValue
                    param_name = t_item.get("elementValue", [{}])[0].get("value")

                if param_name is None:
                    continue

                try:
                    temp_val = float(param_name)
                except (ValueError, TypeError):
                    continue

                if data_date not in daily_temps:
                    daily_temps[data_date] = {"min": [], "max": []}

                if elem_name == "MinT":
                    daily_temps[data_date]["min"].append(temp_val)
                elif elem_name == "MaxT":
                    daily_temps[data_date]["max"].append(temp_val)

        # 彙整每日代表溫度：取當日所有時段最低溫之最小值，最高溫之最大值
        for date_str, temps in sorted(daily_temps.items()):
            min_list = temps["min"]
            max_list = temps["max"]
            
            # 若僅有其一，則適當填補
            if min_list and max_list:
                mint = min(min_list)
                maxt = max(max_list)
            elif min_list:
                mint = min(min_list)
                maxt = mint
            elif max_list:
                maxt = max(max_list)
                mint = maxt
            else:
                continue

            rows.append({
                "regionName": region_name,
                "dataDate": date_str,
                "mint": round(mint, 1),
                "maxt": round(maxt, 1),
            })

    df = pd.DataFrame(rows)
    return df


def sync_cwa_to_db(api_key: Optional[str] = None, db_path: Optional[Path] = None) -> Tuple[bool, str, int]:
    """一站式流程：自 CWA 取得預報資料 -> 解析成 DataFrame -> 儲存/更新至 SQLite。
    
    :return: (是否成功, 訊息字串, 寫入筆數)
    """
    try:
        raw_json = fetch_cwa_json(api_key)
        df = parse_weather_json(raw_json)
        if df.empty:
            return False, "解析後無有效的天氣資料", 0

        count = save_forecasts(df, db_path)
        return True, f"成功同步 {count} 筆天氣預報資料至資料庫！", count
    except Exception as e:
        return False, str(e), 0


if __name__ == "__main__":
    import sys
    print("正在嘗試抓取 CWA 天氣開放資料...")
    success, msg, count = sync_cwa_to_db()
    if success:
        print(f"[OK] {msg}")
    else:
        print(f"[警告] {msg}")
        print("未設定有效的 API Key，如需測試可執行: python -m src.db 載入示範資料。")
