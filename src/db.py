"""SQLite 資料庫管理模組。

負責 TemperatureForecasts 資料表的建立、參數化查詢、重複資料更新 (Upsert) 及資料庫操作。
對應圖二之 Step 8、9、10、12。
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from src.config import DB_PATH, DATA_DIR


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """取得 SQLite 資料庫連線，若目錄不存在則自動建立。"""
    if db_path is None:
        db_path = DB_PATH
    
    # 確保所在資料夾存在
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """初始化資料庫與建立 TemperatureForecasts, SyncMetadata, AirQualityObservations 及 TyphoonWarnings 資料表。"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT NOT NULL,
        dataDate TEXT NOT NULL,
        mint REAL NOT NULL,
        maxt REAL NOT NULL,
        pop REAL,
        CONSTRAINT uq_region_date UNIQUE (regionName, dataDate)
    );
    """)

    # 檢查並動態加入 pop 欄位 (若舊版資料表無此欄位)
    cursor.execute("PRAGMA table_info(TemperatureForecasts);")
    cols = [row["name"] for row in cursor.fetchall()]
    if "pop" not in cols:
        try:
            cursor.execute("ALTER TABLE TemperatureForecasts ADD COLUMN pop REAL;")
        except Exception:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SyncMetadata (
        metaKey TEXT PRIMARY KEY,
        metaValue TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AirQualityObservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT NOT NULL UNIQUE,
        siteName TEXT,
        aqi REAL,
        status TEXT,
        obsTime TEXT,
        source TEXT DEFAULT '環境部 (MOENV)'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TyphoonWarnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hasWarning INTEGER NOT NULL,
        typhoonName TEXT,
        warningType TEXT,
        issueTime TEXT,
        affectedAreas TEXT,
        headline TEXT,
        source TEXT DEFAULT '交通部中央氣象署 (CWA)',
        updateTime TEXT
    );
    """)
    
    conn.commit()
    conn.close()


def set_metadata(key: str, value: str, db_path: Optional[Path] = None) -> None:
    """儲存或更新系統詮釋資料 (如上次更新時間)。"""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO SyncMetadata (metaKey, metaValue)
    VALUES (?, ?)
    ON CONFLICT(metaKey) DO UPDATE SET metaValue = excluded.metaValue;
    """, (key, str(value)))
    conn.commit()
    conn.close()


def get_metadata(key: str, default: Optional[str] = None, db_path: Optional[Path] = None) -> Optional[str]:
    """讀取系統詮釋資料。"""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT metaValue FROM SyncMetadata WHERE metaKey = ?;", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["metaValue"] if row else default


def save_forecasts(data: Any, db_path: Optional[Path] = None) -> int:
    """儲存天氣預報資料至資料庫。
    
    使用參數化查詢與 ON CONFLICT DO UPDATE 機制：
    若 (regionName, dataDate) 已存在，則更新最低溫、最高溫與降雨機率，避免重複寫入。
    
    :param data: list of dict 或 pandas DataFrame
    :return: 處理的筆數
    """
    init_db(db_path)
    
    records = []
    if isinstance(data, pd.DataFrame):
        records = data.to_dict(orient="records")
    elif isinstance(data, list):
        records = data
    else:
        return 0

    if not records:
        return 0

    conn = get_connection(db_path)
    cursor = conn.cursor()

    sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt, pop)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(regionName, dataDate) DO UPDATE SET
        mint = excluded.mint,
        maxt = excluded.maxt,
        pop = COALESCE(excluded.pop, TemperatureForecasts.pop);
    """

    params = []
    for row in records:
        if "regionName" in row and "dataDate" in row and "mint" in row and "maxt" in row:
            pop_val = None
            if "pop" in row and row["pop"] is not None:
                try:
                    pop_val = float(row["pop"])
                except (ValueError, TypeError):
                    pop_val = None
            params.append((
                str(row["regionName"]),
                str(row["dataDate"]),
                float(row["mint"]),
                float(row["maxt"]),
                pop_val,
            ))

    cursor.executemany(sql, params)
    conn.commit()
    affected = len(params)
    conn.close()

    # 自動記錄最後同步時間
    from datetime import datetime
    set_metadata("last_sync_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), db_path)

    return affected


def get_distinct_regions(db_path: Optional[Path] = None) -> List[str]:
    """查詢所有不重複的地區清單 (參數化查詢)。
    
    對應圖二 Step 10: SELECT DISTINCT regionName FROM TemperatureForecasts;
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY id;")
    rows = cursor.fetchall()
    conn.close()
    return [row["regionName"] for row in rows]


def get_forecasts_by_region(region_name: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    """使用參數化 SQL 查詢特定地區的一週預報資料。
    
    對應圖二 Step 10 & 12:
    SELECT * FROM TemperatureForecasts WHERE regionName = ? ORDER BY dataDate;
    """
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
    SELECT regionName, dataDate, mint, maxt, pop
    FROM TemperatureForecasts
    WHERE regionName = ?
    ORDER BY dataDate ASC;
    """
    df = pd.read_sql_query(query, conn, params=(region_name,))
    conn.close()
    return df


def get_distinct_dates(db_path: Optional[Path] = None) -> List[str]:
    """查詢所有不重複的日期清單。"""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [row["dataDate"] for row in rows]


def get_forecasts_by_date(data_date: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    """使用參數化 SQL 查詢特定日期的全台預報資料。"""
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
    SELECT regionName, dataDate, mint, maxt, pop
    FROM TemperatureForecasts
    WHERE dataDate = ?
    ORDER BY regionName ASC;
    """
    df = pd.read_sql_query(query, conn, params=(data_date,))
    conn.close()
    return df


def get_all_forecasts(db_path: Optional[Path] = None) -> pd.DataFrame:
    """查詢所有預報資料，依 regionName, dataDate 排序。"""
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
    SELECT regionName, dataDate, mint, maxt, pop
    FROM TemperatureForecasts
    ORDER BY regionName ASC, dataDate ASC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# ---------------------------------------------------------------------------
# 空氣品質與颱風警報相關資料庫操作
# ---------------------------------------------------------------------------
def save_air_quality(data: List[Dict[str, Any]], db_path: Optional[Path] = None) -> int:
    """儲存或更新空氣品質即時觀測資料。"""
    init_db(db_path)
    if not data:
        return 0
    conn = get_connection(db_path)
    cursor = conn.cursor()
    sql = """
    INSERT INTO AirQualityObservations (regionName, siteName, aqi, status, obsTime, source)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(regionName) DO UPDATE SET
        siteName = excluded.siteName,
        aqi = excluded.aqi,
        status = excluded.status,
        obsTime = excluded.obsTime,
        source = excluded.source;
    """
    params = [
        (
            str(r.get("regionName")),
            str(r.get("siteName", "")),
            float(r["aqi"]) if r.get("aqi") is not None else None,
            str(r.get("status", "")),
            str(r.get("obsTime", "")),
            str(r.get("source", "環境部 (MOENV)")),
        )
        for r in data
        if r.get("regionName")
    ]
    cursor.executemany(sql, params)
    conn.commit()
    conn.close()
    return len(params)


def get_air_quality(region_name: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """查詢特定地區的空氣品質即時觀測資料。若無該精確名稱，亦支援相容 fallback。"""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT regionName, siteName, aqi, status, obsTime, source
    FROM AirQualityObservations
    WHERE regionName = ?;
    """, (region_name,))
    row = cursor.fetchone()
    if not row:
        # 嘗試去除「市」、「縣」、「地區」模糊匹配
        trimmed = region_name.replace("市", "").replace("縣", "").replace("地區", "")
        cursor.execute("""
        SELECT regionName, siteName, aqi, status, obsTime, source
        FROM AirQualityObservations
        WHERE regionName LIKE ?;
        """, (f"%{trimmed}%",))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_typhoon_warning(data: Dict[str, Any], db_path: Optional[Path] = None) -> None:
    """儲存最新颱風警報資料。"""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    # 清除舊警報狀態並寫入最新一筆
    cursor.execute("DELETE FROM TyphoonWarnings;")
    sql = """
    INSERT INTO TyphoonWarnings (hasWarning, typhoonName, warningType, issueTime, affectedAreas, headline, source, updateTime)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    from datetime import datetime
    cursor.execute(sql, (
        1 if data.get("hasWarning") else 0,
        data.get("typhoonName", "無"),
        data.get("warningType", "無警報發布"),
        data.get("issueTime", ""),
        data.get("affectedAreas", "無"),
        data.get("headline", ""),
        data.get("source", "交通部中央氣象署 (CWA)"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def get_latest_typhoon_warning(db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """讀取最新颱風警報資料。"""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT hasWarning, typhoonName, warningType, issueTime, affectedAreas, headline, source, updateTime
    FROM TyphoonWarnings
    ORDER BY id DESC LIMIT 1;
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def seed_mock_data(db_path: Optional[Path] = None) -> int:
    """建立包含六大區域與熱門縣市之一週示範預報資料與生活指標。
    
    用於當無 CWA API Key 或離線環境時，仍可完整驗證資料庫、折線圖、表格、地圖與三張生活建議卡片。
    包含：北部、中部、南部、東北部、東部、東南部，以及臺北、新北、臺中、高雄、桃園、臺南等。
    """
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 包含氣溫與降雨機率 (pop)
    mock_data = [
        # 北部地區
        {"regionName": "北部地區", "dataDate": "2026-09-21", "mint": 22.0, "maxt": 28.0, "pop": 10.0},
        {"regionName": "北部地區", "dataDate": "2026-09-22", "mint": 23.0, "maxt": 29.0, "pop": 20.0},
        {"regionName": "北部地區", "dataDate": "2026-09-23", "mint": 24.0, "maxt": 30.0, "pop": 35.0},
        {"regionName": "北部地區", "dataDate": "2026-09-24", "mint": 24.0, "maxt": 29.0, "pop": 70.0},
        {"regionName": "北部地區", "dataDate": "2026-09-25", "mint": 23.0, "maxt": 28.0, "pop": 20.0},
        {"regionName": "北部地區", "dataDate": "2026-09-26", "mint": 22.0, "maxt": 29.0, "pop": 65.0},
        {"regionName": "北部地區", "dataDate": "2026-09-27", "mint": 23.0, "maxt": 30.0, "pop": 15.0},

        # 臺北市
        {"regionName": "臺北市", "dataDate": "2026-09-21", "mint": 23.0, "maxt": 29.0, "pop": 10.0},
        {"regionName": "臺北市", "dataDate": "2026-09-22", "mint": 24.0, "maxt": 30.0, "pop": 20.0},
        {"regionName": "臺北市", "dataDate": "2026-09-23", "mint": 25.0, "maxt": 31.5, "pop": 30.0},
        {"regionName": "臺北市", "dataDate": "2026-09-24", "mint": 24.5, "maxt": 30.0, "pop": 75.0},
        {"regionName": "臺北市", "dataDate": "2026-09-25", "mint": 23.5, "maxt": 29.0, "pop": 20.0},
        {"regionName": "臺北市", "dataDate": "2026-09-26", "mint": 23.0, "maxt": 29.5, "pop": 60.0},
        {"regionName": "臺北市", "dataDate": "2026-09-27", "mint": 24.0, "maxt": 31.0, "pop": 10.0},

        # 新北市
        {"regionName": "新北市", "dataDate": "2026-09-21", "mint": 22.5, "maxt": 28.5, "pop": 15.0},
        {"regionName": "新北市", "dataDate": "2026-09-22", "mint": 23.5, "maxt": 29.5, "pop": 25.0},
        {"regionName": "新北市", "dataDate": "2026-09-23", "mint": 24.5, "maxt": 30.5, "pop": 35.0},
        {"regionName": "新北市", "dataDate": "2026-09-24", "mint": 24.0, "maxt": 29.5, "pop": 70.0},
        {"regionName": "新北市", "dataDate": "2026-09-25", "mint": 23.0, "maxt": 28.5, "pop": 25.0},
        {"regionName": "新北市", "dataDate": "2026-09-26", "mint": 22.5, "maxt": 29.0, "pop": 65.0},
        {"regionName": "新北市", "dataDate": "2026-09-27", "mint": 23.5, "maxt": 30.5, "pop": 15.0},

        # 中部地區
        {"regionName": "中部地區", "dataDate": "2026-09-21", "mint": 24.0, "maxt": 31.0, "pop": 10.0},
        {"regionName": "中部地區", "dataDate": "2026-09-22", "mint": 24.0, "maxt": 32.0, "pop": 10.0},
        {"regionName": "中部地區", "dataDate": "2026-09-23", "mint": 25.0, "maxt": 33.0, "pop": 20.0},
        {"regionName": "中部地區", "dataDate": "2026-09-24", "mint": 25.0, "maxt": 32.0, "pop": 40.0},
        {"regionName": "中部地區", "dataDate": "2026-09-25", "mint": 24.0, "maxt": 31.0, "pop": 15.0},
        {"regionName": "中部地區", "dataDate": "2026-09-26", "mint": 24.0, "maxt": 32.0, "pop": 30.0},
        {"regionName": "中部地區", "dataDate": "2026-09-27", "mint": 25.0, "maxt": 32.0, "pop": 10.0},

        # 臺中市
        {"regionName": "臺中市", "dataDate": "2026-09-21", "mint": 24.5, "maxt": 31.5, "pop": 10.0},
        {"regionName": "臺中市", "dataDate": "2026-09-22", "mint": 24.5, "maxt": 32.5, "pop": 10.0},
        {"regionName": "臺中市", "dataDate": "2026-09-23", "mint": 25.5, "maxt": 33.5, "pop": 20.0},
        {"regionName": "臺中市", "dataDate": "2026-09-24", "mint": 25.0, "maxt": 32.5, "pop": 35.0},
        {"regionName": "臺中市", "dataDate": "2026-09-25", "mint": 24.5, "maxt": 31.5, "pop": 15.0},
        {"regionName": "臺中市", "dataDate": "2026-09-26", "mint": 24.5, "maxt": 32.5, "pop": 25.0},
        {"regionName": "臺中市", "dataDate": "2026-09-27", "mint": 25.0, "maxt": 32.5, "pop": 10.0},

        # 南部地區
        {"regionName": "南部地區", "dataDate": "2026-09-21", "mint": 25.0, "maxt": 32.0, "pop": 20.0},
        {"regionName": "南部地區", "dataDate": "2026-09-22", "mint": 25.0, "maxt": 33.0, "pop": 20.0},
        {"regionName": "南部地區", "dataDate": "2026-09-23", "mint": 26.0, "maxt": 33.0, "pop": 30.0},
        {"regionName": "南部地區", "dataDate": "2026-09-24", "mint": 25.0, "maxt": 32.0, "pop": 45.0},
        {"regionName": "南部地區", "dataDate": "2026-09-25", "mint": 25.0, "maxt": 32.0, "pop": 20.0},
        {"regionName": "南部地區", "dataDate": "2026-09-26", "mint": 26.0, "maxt": 33.0, "pop": 35.0},
        {"regionName": "南部地區", "dataDate": "2026-09-27", "mint": 25.0, "maxt": 32.0, "pop": 15.0},

        # 高雄市
        {"regionName": "高雄市", "dataDate": "2026-09-21", "mint": 25.5, "maxt": 32.5, "pop": 20.0},
        {"regionName": "高雄市", "dataDate": "2026-09-22", "mint": 25.5, "maxt": 33.5, "pop": 20.0},
        {"regionName": "高雄市", "dataDate": "2026-09-23", "mint": 26.5, "maxt": 33.5, "pop": 30.0},
        {"regionName": "高雄市", "dataDate": "2026-09-24", "mint": 25.5, "maxt": 32.5, "pop": 40.0},
        {"regionName": "高雄市", "dataDate": "2026-09-25", "mint": 25.5, "maxt": 32.5, "pop": 20.0},
        {"regionName": "高雄市", "dataDate": "2026-09-26", "mint": 26.0, "maxt": 33.5, "pop": 30.0},
        {"regionName": "高雄市", "dataDate": "2026-09-27", "mint": 25.5, "maxt": 32.5, "pop": 10.0},

        # 東北部地區
        {"regionName": "東北部地區", "dataDate": "2026-09-21", "mint": 22.0, "maxt": 27.0, "pop": 30.0},
        {"regionName": "東北部地區", "dataDate": "2026-09-22", "mint": 23.0, "maxt": 28.0, "pop": 40.0},
        {"regionName": "東北部地區", "dataDate": "2026-09-23", "mint": 23.0, "maxt": 28.0, "pop": 50.0},
        {"regionName": "東北部地區", "dataDate": "2026-09-24", "mint": 22.0, "maxt": 27.0, "pop": 80.0},
        {"regionName": "東北部地區", "dataDate": "2026-09-25", "mint": 22.0, "maxt": 27.0, "pop": 40.0},
        {"regionName": "東北部地區", "dataDate": "2026-09-26", "mint": 23.0, "maxt": 28.0, "pop": 70.0},
        {"regionName": "東北部地區", "dataDate": "2026-09-27", "mint": 23.0, "maxt": 28.0, "pop": 30.0},

        # 東部地區
        {"regionName": "東部地區", "dataDate": "2026-09-21", "mint": 23.0, "maxt": 29.0, "pop": 20.0},
        {"regionName": "東部地區", "dataDate": "2026-09-22", "mint": 23.0, "maxt": 30.0, "pop": 30.0},
        {"regionName": "東部地區", "dataDate": "2026-09-23", "mint": 24.0, "maxt": 30.0, "pop": 30.0},
        {"regionName": "東部地區", "dataDate": "2026-09-24", "mint": 24.0, "maxt": 29.0, "pop": 60.0},
        {"regionName": "東部地區", "dataDate": "2026-09-25", "mint": 23.0, "maxt": 29.0, "pop": 30.0},
        {"regionName": "東部地區", "dataDate": "2026-09-26", "mint": 23.0, "maxt": 30.0, "pop": 50.0},
        {"regionName": "東部地區", "dataDate": "2026-09-27", "mint": 24.0, "maxt": 30.0, "pop": 20.0},

        # 東南部地區
        {"regionName": "東南部地區", "dataDate": "2026-09-21", "mint": 24.0, "maxt": 30.0, "pop": 10.0},
        {"regionName": "東南部地區", "dataDate": "2026-09-22", "mint": 24.0, "maxt": 31.0, "pop": 20.0},
        {"regionName": "東南部地區", "dataDate": "2026-09-23", "mint": 25.0, "maxt": 31.0, "pop": 20.0},
        {"regionName": "東南部地區", "dataDate": "2026-09-24", "mint": 25.0, "maxt": 31.0, "pop": 40.0},
        {"regionName": "東南部地區", "dataDate": "2026-09-25", "mint": 24.0, "maxt": 30.0, "pop": 20.0},
        {"regionName": "東南部地區", "dataDate": "2026-09-26", "mint": 24.0, "maxt": 31.0, "pop": 30.0},
        {"regionName": "東南部地區", "dataDate": "2026-09-27", "mint": 25.0, "maxt": 31.0, "pop": 10.0},
    ]

    saved = save_forecasts(mock_data, db_path)

    # 播種即時空氣品質示範資料
    aq_data = [
        {"regionName": "臺北市", "siteName": "大同站", "aqi": 42.0, "status": "良好", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "新北市", "siteName": "板橋站", "aqi": 48.0, "status": "良好", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "臺中市", "siteName": "忠明站", "aqi": 72.0, "status": "普通", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "高雄市", "siteName": "前金站", "aqi": 108.0, "status": "對敏感族群不健康", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "北部地區", "siteName": "北部觀測區", "aqi": 45.0, "status": "良好", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "中部地區", "siteName": "中部觀測區", "aqi": 70.0, "status": "普通", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "南部地區", "siteName": "南部觀測區", "aqi": 105.0, "status": "對敏感族群不健康", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "東北部地區", "siteName": "宜蘭站", "aqi": 25.0, "status": "良好", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "東部地區", "siteName": "花蓮站", "aqi": 28.0, "status": "良好", "obsTime": now_str, "source": "環境部 (MOENV)"},
        {"regionName": "東南部地區", "siteName": "臺東站", "aqi": 22.0, "status": "良好", "obsTime": now_str, "source": "環境部 (MOENV)"},
    ]
    save_air_quality(aq_data, db_path)

    # 播種颱風警報狀態 (預設無警報)
    ty_data = {
        "hasWarning": 0,
        "typhoonName": "無",
        "warningType": "無警報發布",
        "issueTime": now_str,
        "affectedAreas": "無",
        "headline": "目前無發布颱風警報",
        "source": "交通部中央氣象署 (CWA)"
    }
    save_typhoon_warning(ty_data, db_path)

    # 記錄最後同步時間
    set_metadata("last_sync_time", now_str, db_path)

    return saved


if __name__ == "__main__":
    init_db()
    count = seed_mock_data()
    print(f"[OK] 資料庫初始化並寫入 {count} 筆種子資料。")
    regions = get_distinct_regions()
    print(f"地區清單: {regions}")
