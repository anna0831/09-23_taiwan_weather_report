# Taiwan Weather Forecast Web App ⛅

本專案依據「AI 創新微課程：從氣象資料到互動式天氣預報應用」課程圖表設計與實作。透過串接中央氣象署（CWA）天氣開放資料 API，使用 Python 與 pandas 進行資料萃取與整理，存入 SQLite 資料庫，並運用 Streamlit 與 Folium 打造具備折線圖、資料表以及分區氣溫互動地圖的 Web 應用程式。

---

## 專案功能與特色

* **CWA API 資料介接與 JSON 解析**：自動自氣象資料開放平臺取得「臺灣各區一週天氣預報」（`F-C0032-003`），解析 MinT（最低溫）與 MaxT（最高溫）。
* **SQLite 資料庫儲存與防重防呆**：
  * 資料表 `TemperatureForecasts` 採用 `UNIQUE(regionName, dataDate)` 約束。
  * 支援 **UPSERT** 機制（`ON CONFLICT DO UPDATE`），重複執行時自動更新數值，不產生重複記錄。
  * 嚴格採用**參數化 SQL 查詢**，提升資料安全性與效能。
* **Streamlit 視覺化互動介面**：
  * **選地區看氣溫預報**：提供下拉選單選擇地區（北部、中部、南部、東北部、東部、東南部），即時統計一週最低、最高與平均溫。
  * **一週氣溫折線圖**：紅線標示最高溫（MaxT），藍線標示最低溫（MinT）。
  * **清晰預報資料表**：列出每日最低溫、最高溫與溫差。
* **Folium 台灣互動天氣地圖**：
  * **依日期切換**：可選擇特定日期檢視全台各區天氣分佈。
  * **溫度區間分色標記**：
    * 🔵 **< 20°C**：藍色
    * 🟢 **20°C ~ 25°C**：綠色
    * 🟠 **25°C ~ 30°C**：橘色
    * 🔴 **> 30°C**：紅色
  * **地圖標記彈出視窗 (Popup)**：點擊標記可查看該地區名稱、最低溫與最高溫。
  * **示範資料模式**：無 API Key 時自動載入課程示範資料，開箱即可完整體驗全部介面與地圖功能。

---

## 資料流程架構

```
[中央氣象署 CWA API] (F-C0032-003)
         │  (requests GET + JSON 解析)
         ▼
[Python / pandas 資料整理] (提取 regionName, dataDate, mint, maxt)
         │  (UPSERT 寫入)
         ▼
[SQLite 資料庫 data/data.db] (資料表: TemperatureForecasts)
         │  (參數化 SQL 查詢)
         ▼
[Streamlit Web App (app.py)]
   ├── 📈 折線圖 (MaxT 紅線 / MinT 藍線) & 數據表格
   └── 🗺️ Folium 互動地圖 (依日期切換、氣溫區間分色、點擊 Popup)
```

---

## 檔案目錄結構

```
0923 天氣預測/
├── data/
│   ├── .gitkeep              # 確保 Git 追蹤資料夾結構
│   └── data.db               # SQLite 資料庫檔案
├── src/
│   ├── __init__.py           # Python 套件標記
│   ├── config.py             # 系統常數、座標定義與溫度顏色邏輯
│   ├── db.py                 # SQLite 連線、參數化查詢、UPSERT 與示範資料模組
│   └── fetch_data.py         # CWA API 請求與 JSON 解析模組
├── tests/
│   └── test_weather_app.py   # 自動化單元與整合測試
├── app.py                    # Streamlit 主應用程式
├── requirements.txt          # 依賴套件清單
├── .env.example              # CWA API Key 設定範例
├── .gitignore                # Git 忽略設定
└── README.md                 # 專案詳細說明文件
```

---

## 安裝與執行說明

### 1. 環境需求
* Python 3.10 或以上版本（支援最新 Python 3.14）

### 2. 安裝依賴套件
在專案根目錄下開啟終端機，執行：
```bash
pip install -r requirements.txt
```

### 3. 設定 CWA API Key（選用）
若欲同步最新氣象資料：
1. 前往 [中央氣象署氣象資料開放平臺](https://opendata.cwa.gov.tw/) 註冊並取得授權碼（格式如 `CWA-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）。
2. 複製 `.env.example` 為 `.env`：
   ```bash
   copy .env.example .env
   ```
3. 在 `.env` 填入您的授權碼：
   ```env
   CWA_API_KEY=您的授權碼
   ```
> **提示**：若暫無 API Key，系統預設會自動載入課程標準示範資料，不影響網站介面與地圖展示。

### 4. 初始化資料庫與手動同步（選用）
* **載入示範資料**：
  ```bash
  python -m src.db
  ```
* **自 CWA API 同步**：
  ```bash
  python -m src.fetch_data
  ```

### 5. 啟動 Streamlit Web 應用程式
執行以下指令啟動網站：
```bash
streamlit run app.py
```
或使用 Python 模組方式啟動：
```bash
python -m streamlit run app.py
```
啟動後，請在瀏覽器中開啟終端機顯示的網址（預設為 `http://localhost:8501`）。

---

## 執行測試

本專案附帶完整自動化測試，驗證資料庫初始化、重複插入更新、參數化查詢、JSON 萃取與溫度顏色分類：
```bash
python -m unittest tests/test_weather_app.py
```

---

## 實作假設與設計決策

1. **API 資料集代碼選擇**：
   * 課程圖二 Step 5 與 Step 7 明確顯示「北部地區、中部地區、南部地區、東北部地區、東部地區、東南部地區」等大分區，對應 CWA 開放資料平台之 `F-C0032-003`（臺灣各區一週天氣預報）。
2. **跨日時段與代表溫度處理**：
   * 氣象預報一般分為白晝與夜間。本專案按日期（`YYYY-MM-DD`）整合：取當日各時段之最低溫最小值為 `mint`，最高溫最大值為 `maxt`，作為當日代表預報值。
3. **台灣各分區地圖中心座標**：
   * 北部地區：`(25.04, 121.55)`
   * 東北部地區：`(24.75, 121.75)`
   * 中部地區：`(24.15, 120.68)`
   * 東部地區：`(23.99, 121.60)`
   * 南部地區：`(22.62, 120.31)`
   * 東南部地區：`(22.75, 121.15)`
4. **溫度區間分色定義**：
   * 以每日平均溫度 `(mint + maxt) / 2` 判定顏色：
     * `< 20°C`：藍色 (`blue`)
     * `20°C ~ 25°C`：綠色 (`green`)
     * `25°C ~ 30°C`：橘色 (`orange`)
     * `> 30°C`：紅色 (`red`)

---

## 已知限制

1. **即時連線需憑證**：存取 CWA 即時 API 必須具備有效授權碼；若未提供或網路受阻，系統將維持示範模式。
2. **地圖底圖圖資連線**：Folium 使用 CartoDB / OpenStreetMap 網路圖資，瀏覽地圖時電腦需保有外網連線能力以順利載入底圖。
