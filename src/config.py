"""系統設定與常數定義。

包含環境變數讀取 (CWA_API_KEY)、資料庫路徑、各分區地理座標與溫度分級顏色。
"""

import os
from pathlib import Path

# 專案根目錄
BASE_DIR = Path(__file__).resolve().parent.parent

# 資料庫路徑 (支援本機 data/data.db 與 Vercel Serverless /tmp/data.db)
DATA_DIR = BASE_DIR / "data"

def get_db_path() -> Path:
    """取得 SQLite 資料庫路徑。在 Vercel 唯讀無伺服器環境下自動使用 /tmp/data.db。"""
    default_db = DATA_DIR / "data.db"
    if os.environ.get("VERCEL") or "/var/task" in str(BASE_DIR):
        tmp_db = Path("/tmp/data.db")
        if not tmp_db.exists() and default_db.exists():
            import shutil
            try:
                shutil.copyfile(default_db, tmp_db)
            except Exception:
                pass
        return tmp_db
    return default_db

DB_PATH = get_db_path()



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

# CWA API 端點：優先使用最新 7 天預報 F-D0047-091，備選 F-C0032-001 與 F-C0032-003
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
CWA_API_URL_C0032 = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

# 縣市至六大分區對應表 (供彙整與雙向查詢)
COUNTY_TO_REGION = {
    # 北部地區
    "基隆市": "北部地區", "臺北市": "北部地區", "新北市": "北部地區",
    "桃園市": "北部地區", "新竹市": "北部地區", "新竹縣": "北部地區", "苗栗縣": "北部地區",
    # 中部地區
    "臺中市": "中部地區", "彰化縣": "中部地區", "南投縣": "中部地區",
    "雲林縣": "中部地區", "嘉義市": "中部地區", "嘉義縣": "中部地區",
    # 南部地區
    "臺南市": "南部地區", "高雄市": "南部地區", "屏東縣": "南部地區",
    # 東北部地區
    "宜蘭縣": "東北部地區",
    # 東部地區
    "花蓮縣": "東部地區",
    # 東南部地區
    "臺東縣": "東南部地區",
    # 離島地區
    "澎湖縣": "澎湖地區",
    "金門縣": "金門地區",
    "連江縣": "連江地區",
}

# 臺灣各地區與縣市代表中心經緯度
REGION_COORDINATES = {
    # 六大分區 (課程標準)
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
    # 22 縣市座標備用
    "基隆市": {"lat": 25.13, "lon": 121.74, "label": "基隆"},
    "臺北市": {"lat": 25.04, "lon": 121.53, "label": "臺北"},
    "新北市": {"lat": 25.01, "lon": 121.46, "label": "新北"},
    "桃園市": {"lat": 24.99, "lon": 121.31, "label": "桃園"},
    "新竹市": {"lat": 24.80, "lon": 120.97, "label": "新竹市"},
    "新竹縣": {"lat": 24.83, "lon": 121.01, "label": "新竹縣"},
    "苗栗縣": {"lat": 24.56, "lon": 120.82, "label": "苗栗"},
    "臺中市": {"lat": 24.16, "lon": 120.68, "label": "臺中"},
    "彰化縣": {"lat": 24.08, "lon": 120.54, "label": "彰化"},
    "南投縣": {"lat": 23.91, "lon": 120.68, "label": "南投"},
    "雲林縣": {"lat": 23.70, "lon": 120.43, "label": "雲林"},
    "嘉義市": {"lat": 23.48, "lon": 120.44, "label": "嘉義市"},
    "嘉義縣": {"lat": 23.45, "lon": 120.25, "label": "嘉義縣"},
    "臺南市": {"lat": 22.99, "lon": 120.21, "label": "臺南"},
    "高雄市": {"lat": 22.63, "lon": 120.30, "label": "高雄"},
    "屏東縣": {"lat": 22.67, "lon": 120.49, "label": "屏東"},
    "宜蘭縣": {"lat": 24.75, "lon": 121.75, "label": "宜蘭"},
    "花蓮縣": {"lat": 23.98, "lon": 121.60, "label": "花蓮"},
    "臺東縣": {"lat": 22.76, "lon": 121.14, "label": "臺東"},
    "澎湖縣": {"lat": 23.57, "lon": 119.58, "label": "澎湖"},
    "金門縣": {"lat": 24.44, "lon": 118.37, "label": "金門"},
    "連江縣": {"lat": 26.15, "lon": 119.93, "label": "馬祖"},
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
