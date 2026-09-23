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
    """初始化資料庫與建立 TemperatureForecasts 資料表。
    
    資料表結構依據課程圖二 Step 9：
    - id: INTEGER PRIMARY KEY AUTOINCREMENT
    - regionName: TEXT
    - dataDate: TEXT
    - mint: REAL
    - maxt: REAL
    
    加上 UNIQUE(regionName, dataDate) 以確保相同地區與日期重複匯入時能安全更新。
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT NOT NULL,
        dataDate TEXT NOT NULL,
        mint REAL NOT NULL,
        maxt REAL NOT NULL,
        CONSTRAINT uq_region_date UNIQUE (regionName, dataDate)
    );
    """)
    
    conn.commit()
    conn.close()


def save_forecasts(data: Any, db_path: Optional[Path] = None) -> int:
    """儲存天氣預報資料至資料庫。
    
    使用參數化查詢與 ON CONFLICT DO UPDATE 機制：
    若 (regionName, dataDate) 已存在，則更新最低溫與最高溫，避免重複寫入。
    
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
    INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(regionName, dataDate) DO UPDATE SET
        mint = excluded.mint,
        maxt = excluded.maxt;
    """

    params = [
        (
            str(row["regionName"]),
            str(row["dataDate"]),
            float(row["mint"]),
            float(row["maxt"]),
        )
        for row in records
        if "regionName" in row and "dataDate" in row and "mint" in row and "maxt" in row
    ]

    cursor.executemany(sql, params)
    conn.commit()
    affected = len(params)
    conn.close()
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
    SELECT regionName, dataDate, mint, maxt
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
    SELECT regionName, dataDate, mint, maxt
    FROM TemperatureForecasts
    WHERE dataDate = ?
    ORDER BY regionName ASC;
    """
    df = pd.read_sql_query(query, conn, params=(data_date,))
    conn.close()
    return df


def seed_mock_data(db_path: Optional[Path] = None) -> int:
    """建立符合課程圖片範例的種子預報資料。
    
    用於當無 CWA API Key 或離線環境時，仍可完整驗證資料庫、折線圖、表格與地圖功能。
    包含：北部地區、中部地區、南部地區、東北部地區、東部地區、東南部地區 等一週預報。
    """
    mock_data = [
        # 北部地區
        {"regionName": "北部地區", "dataDate": "2026-04-14", "mint": 18.0, "maxt": 26.0},
        {"regionName": "北部地區", "dataDate": "2026-04-15", "mint": 19.0, "maxt": 27.0},
        {"regionName": "北部地區", "dataDate": "2026-04-16", "mint": 20.0, "maxt": 28.0},
        {"regionName": "北部地區", "dataDate": "2026-04-17", "mint": 21.0, "maxt": 29.0},
        {"regionName": "北部地區", "dataDate": "2026-04-18", "mint": 20.0, "maxt": 28.0},
        {"regionName": "北部地區", "dataDate": "2026-04-19", "mint": 19.0, "maxt": 27.0},
        {"regionName": "北部地區", "dataDate": "2026-04-20", "mint": 18.0, "maxt": 26.0},

        # 中部地區
        {"regionName": "中部地區", "dataDate": "2026-04-14", "mint": 20.0, "maxt": 30.0},
        {"regionName": "中部地區", "dataDate": "2026-04-15", "mint": 21.0, "maxt": 31.0},
        {"regionName": "中部地區", "dataDate": "2026-04-16", "mint": 22.0, "maxt": 32.0},
        {"regionName": "中部地區", "dataDate": "2026-04-17", "mint": 21.0, "maxt": 30.0},
        {"regionName": "中部地區", "dataDate": "2026-04-18", "mint": 22.0, "maxt": 31.0},
        {"regionName": "中部地區", "dataDate": "2026-04-19", "mint": 21.0, "maxt": 30.0},
        {"regionName": "中部地區", "dataDate": "2026-04-20", "mint": 20.0, "maxt": 29.0},

        # 南部地區
        {"regionName": "南部地區", "dataDate": "2026-04-14", "mint": 22.0, "maxt": 31.0},
        {"regionName": "南部地區", "dataDate": "2026-04-15", "mint": 23.0, "maxt": 32.0},
        {"regionName": "南部地區", "dataDate": "2026-04-16", "mint": 24.0, "maxt": 33.0},
        {"regionName": "南部地區", "dataDate": "2026-04-17", "mint": 23.0, "maxt": 32.0},
        {"regionName": "南部地區", "dataDate": "2026-04-18", "mint": 24.0, "maxt": 33.0},
        {"regionName": "南部地區", "dataDate": "2026-04-19", "mint": 23.0, "maxt": 32.0},
        {"regionName": "南部地區", "dataDate": "2026-04-20", "mint": 22.0, "maxt": 31.0},

        # 東北部地區
        {"regionName": "東北部地區", "dataDate": "2026-04-14", "mint": 18.0, "maxt": 27.0},
        {"regionName": "東北部地區", "dataDate": "2026-04-15", "mint": 19.0, "maxt": 26.0},
        {"regionName": "東北部地區", "dataDate": "2026-04-16", "mint": 20.0, "maxt": 27.0},
        {"regionName": "東北部地區", "dataDate": "2026-04-17", "mint": 20.0, "maxt": 28.0},
        {"regionName": "東北部地區", "dataDate": "2026-04-18", "mint": 19.0, "maxt": 27.0},
        {"regionName": "東北部地區", "dataDate": "2026-04-19", "mint": 18.0, "maxt": 26.0},
        {"regionName": "東北部地區", "dataDate": "2026-04-20", "mint": 18.0, "maxt": 25.0},

        # 東部地區
        {"regionName": "東部地區", "dataDate": "2026-04-14", "mint": 21.0, "maxt": 29.0},
        {"regionName": "東部地區", "dataDate": "2026-04-15", "mint": 21.0, "maxt": 28.0},
        {"regionName": "東部地區", "dataDate": "2026-04-16", "mint": 22.0, "maxt": 29.0},
        {"regionName": "東部地區", "dataDate": "2026-04-17", "mint": 22.0, "maxt": 30.0},
        {"regionName": "東部地區", "dataDate": "2026-04-18", "mint": 21.0, "maxt": 29.0},
        {"regionName": "東部地區", "dataDate": "2026-04-19", "mint": 20.0, "maxt": 28.0},
        {"regionName": "東部地區", "dataDate": "2026-04-20", "mint": 20.0, "maxt": 28.0},

        # 東南部地區
        {"regionName": "東南部地區", "dataDate": "2026-04-14", "mint": 22.0, "maxt": 30.0},
        {"regionName": "東南部地區", "dataDate": "2026-04-15", "mint": 23.0, "maxt": 31.0},
        {"regionName": "東南部地區", "dataDate": "2026-04-16", "mint": 23.0, "maxt": 31.0},
        {"regionName": "東南部地區", "dataDate": "2026-04-17", "mint": 24.0, "maxt": 32.0},
        {"regionName": "東南部地區", "dataDate": "2026-04-18", "mint": 23.0, "maxt": 31.0},
        {"regionName": "東南部地區", "dataDate": "2026-04-19", "mint": 22.0, "maxt": 30.0},
        {"regionName": "東南部地區", "dataDate": "2026-04-20", "mint": 22.0, "maxt": 30.0},
    ]
    return save_forecasts(mock_data, db_path)


if __name__ == "__main__":
    init_db()
    count = seed_mock_data()
    print(f"[OK] 資料庫初始化並寫入 {count} 筆種子資料。")
    regions = get_distinct_regions()
    print(f"地區清單: {regions}")
