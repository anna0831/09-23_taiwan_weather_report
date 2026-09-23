"""系統設定與常數定義。

包含環境變數讀取 (CWA_API_KEY)、資料庫路徑、各分區地理座標與溫度分級顏色。
"""

import os
from pathlib import Path

# 專案根目錄
BASE_DIR = Path(__file__).resolve().parent.parent

# 資料庫路徑 (支援 data/data.db)
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "data.db"


def load_env_file(env_path: Path = None):
    """讀取 .env 檔案並載入至環境變數 (不依賴第三方套件)。"""
    if env_path is None:
        env_path = BASE_DIR / ".env"

    if env_path.is_file():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except Exception:
            pass


# 自動載入 .env
load_env_file()

# CWA 氣象開放資料 API 設定
CWA_API_KEY = os.environ.get("CWA_API_KEY", "").strip()
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-003"

# 臺灣各地區代表中心經緯度 (依據課程圖片所示之區域劃分)
REGION_COORDINATES = {
    "北部地區": {"lat": 25.04, "lon": 121.55, "label": "北部"},
    "東北部地區": {"lat": 24.75, "lon": 121.75, "label": "東北部"},
    "中部地區": {"lat": 24.15, "lon": 120.68, "label": "中部"},
    "東部地區": {"lat": 23.99, "lon": 121.60, "label": "東部"},
    "南部地區": {"lat": 22.62, "lon": 120.31, "label": "南部"},
    "東南部地區": {"lat": 22.75, "lon": 121.15, "label": "東南部"},
    "澎湖地區": {"lat": 23.57, "lon": 119.58, "label": "澎湖"},
    "金門地區": {"lat": 24.44, "lon": 118.37, "label": "金門"},
    "連江地區": {"lat": 26.15, "lon": 119.93, "label": "馬祖"},
    "馬祖地區": {"lat": 26.15, "lon": 119.93, "label": "馬祖"},
}


def get_temp_color(temp_avg: float) -> str:
    """根據平均氣溫回傳對應的標記顏色名稱 (藍、綠、橘、紅)。
    
    規則 (依據課程圖二 Step 17):
    - < 20°C: 藍色 (blue)
    - 20 - 25°C: 綠色 (green)
    - 25 - 30°C: 橘色 (orange)
    - > 30°C: 紅色 (red)
    """
    if temp_avg < 20.0:
        return "blue"
    elif temp_avg <= 25.0:
        return "green"
    elif temp_avg <= 30.0:
        return "orange"
    else:
        return "red"
