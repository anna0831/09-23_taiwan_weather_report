# Taiwan Weather Forecast Web App ⛅

本專案依據「AI 創新微課程：從氣象資料到互動式天氣預報應用」課程圖表設計與實作。透過串接中央氣象署（CWA）天氣開放資料 API，使用 Python 與 pandas 進行資料萃取與整理，存入 SQLite 資料庫，並運用 Streamlit 與 Folium 打造具備折線圖、資料表以及分區氣溫互動地圖的 Web 應用程式。

專案整合了 **GitHub Actions CI/CD 自動化工作流程**，確保程式碼品質與單元測試在每次提交與 Pull Request 時皆能通過檢查。

---

## 一、專案功能與特色

* **CWA API 資料介接與 JSON 解析**：自動自氣象資料開放平臺取得「臺灣各區一週天氣預報」（`F-C0032-003`），解析 MinT（最低溫）與 MaxT（最高溫）。
* **SQLite 資料庫儲存與防重防呆**：
  * 資料表 `TemperatureForecasts` 採用 `UNIQUE(regionName, dataDate)` 約束。
  * 支援 **UPSERT** 機制（`ON CONFLICT DO UPDATE`），重複執行時自動更新數值，不產生重複記錄。
  * 嚴格採用**參數化 SQL 查詢**，防止 SQL Injection 並提升效能。
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

## 二、資料流程架構

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

## 三、開發階段與完成標準 (Definition of Done)

本專案採模組化漸進式開發，各階段劃分與完成驗收標準如下：

### 階段 1：環境設定與安全規範 (Environment & Security Setup)
* **目標**：建立虛擬環境、版本控制忽略清單與環境變數規範。
* **完成標準 (DoD)**：
  1. `.gitignore` 正確排除 `.env`、`data/*.db` 與 `__pycache__/`，確保機密資訊不入庫。
  2. `requirements.txt` 明確鎖定執行所需依賴。
  3. `.env.example` 提供清楚的 CWA API Key 設定範本。

### 階段 2：資料庫設計與防重機制 (Database & Storage)
* **目標**：建立 SQLite `data.db` 及 `TemperatureForecasts` 資料表。
* **完成標準 (DoD)**：
  1. 資料表包含 `id`、`regionName`、`dataDate`、`mint`、`maxt` 欄位。
  2. 具備 `UNIQUE(regionName, dataDate)` 約束。
  3. 實作以 `ON CONFLICT DO UPDATE` 為核心的 UPSERT 邏輯，經單元測試驗證重複寫入時原紀錄被更新且不增加重複行數。
  4. 所有資料庫查詢皆採用參數化查詢（`?` 佔位符），防範 SQL 注入。

### 階段 3：API 介接、JSON 解析與資料清理 (API & Data Cleaning)
* **目標**：介接 CWA `F-C0032-003` 預報，解析巢狀 JSON 並以 pandas 整合。
* **完成標準 (DoD)**：
  1. 支援從環境變數或 `.env` 讀取 `CWA_API_KEY`。
  2. 解析函式能安全萃取各地區在預報週期內的最低溫與最高溫。
  3. 跨日與多時段資料依日期聚合（最低溫取最小值，最高溫取最大值）。
  4. 單元測試使用本地 Mock JSON 資料集驗證解析邏輯，**不依賴真實網路與 API 金鑰**。
  5. 缺少 API Key 時，系統能優雅捕捉並提供清晰指引，不引發未預期崩潰。

### 階段 4：Streamlit 視覺化前端 (Interactive Web Dashboard)
* **目標**：建立折線圖、統計指標與資料表格。
* **完成標準 (DoD)**：
  1. 可從資料庫動態載入不重複的地區清單供使用者下拉選取。
  2. 依選取地區即時呈現一週最高溫（紅線）與最低溫（藍線）折線圖。
  3. 資料表格清楚標示日期、MinT、MaxT 與溫差。
  4. 首次啟動若資料庫為空，自動載入課程標準示範資料以利即時預覽。

### 階段 5：Folium 台灣互動天氣地圖 (Geospatial Mapping)
* **目標**：結合 Folium 地圖與氣溫分級色彩呈現全台分區天氣。
* **完成標準 (DoD)**：
  1. 提供日期選擇器，依日期動態切換標記。
  2. 精準映射各地區中心座標（北部、中部、南部、東北部、東部、東南部）。
  3. 依平均溫度自動設定標記顏色（<20 藍、20~25 綠、25~30 橘、>30 紅）。
  4. 點擊標記跳出 Popup，顯示地區名稱、最低溫、最高溫與平均溫。

### 階段 6：自動化測試與 CI/CD 工作流程 (CI Workflow)
* **目標**：建置 GitHub Actions 工作流程，保障程式品質。
* **完成標準 (DoD)**：
  1. 建立 `.github/workflows/ci.yml`。
  2. 於 `push` 與 `pull_request` 至 `main` 分支時自動觸發。
  3. 涵蓋 Python 語法編譯檢查（`compileall`）與離線單元測試（`unittest`）。
  4. 在無外部網路與無 Secrets 的環境下能全數通過測試（綠燈）。

---

## 四、檔案目錄結構

```
0923 天氣預測/
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI 工作流程設定
├── data/
│   ├── .gitkeep              # 確保 Git 追蹤資料夾結構
│   └── data.db               # SQLite 資料庫檔案 (本機產生，Git 忽略)
├── src/
│   ├── __init__.py           # Python 套件標記
│   ├── config.py             # 系統常數、座標定義與溫度顏色邏輯
│   ├── db.py                 # SQLite 連線、參數化查詢、UPSERT 與示範資料模組
│   └── fetch_data.py         # CWA API 請求與 JSON 解析模組
├── tests/
│   ├── __init__.py
│   └── test_weather_app.py   # 自動化單元與整合測試 (離線運行)
├── app.py                    # Streamlit 主應用程式
├── requirements.txt          # 依賴套件清單
├── .env.example              # CWA API Key 設定範例
├── .gitignore                # Git 忽略設定
└── README.md                 # 專案詳細說明文件
```

---

## 五、安裝與執行說明

### 1. 環境需求
* Python 3.10 或以上版本（經測試相容於 Python 3.11、3.12、3.13、3.14）

### 2. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 3. 設定 CWA API Key（選用）
若欲同步中央氣象署即時預報：
1. 前往 [中央氣象署氣象資料開放平臺](https://opendata.cwa.gov.tw/) 註冊並取得授權碼（格式例：`CWA-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）。
2. 複製 `.env.example` 為 `.env`：
   ```bash
   copy .env.example .env
   ```
3. 在 `.env` 填入授權碼：
   ```env
   CWA_API_KEY=您的授權碼
   ```
> 💡 **提示**：若未設定 API Key，系統將以示範資料模式運作，所有圖表、表格與地圖均可完整操作。

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
```bash
streamlit run app.py
```
或使用 Python 模組指令啟動：
```bash
python -m streamlit run app.py
```
啟動後，請於瀏覽器開啟 `http://localhost:8501`。

---

## 六、自動化測試與 GitHub Actions CI

### 1. 本機執行測試
本專案的測試套件完全採離線設計，使用內嵌結構化 JSON 資料進行驗證，不發送外部網路請求，亦不依賴真實 API 金鑰：
```bash
# 語法編譯檢查
python -m compileall src app.py tests

# 執行所有單元測試
python -m unittest discover -s tests -p "test_*.py"
```

### 2. GitHub Actions CI 規格
* **設定檔位置**：`.github/workflows/ci.yml`
* **觸發時機**：
  * Push 至 `main` 分支。
  * 對 `main` 分支發起 Pull Request。
* **測試環境矩陣**：Ubuntu Latest 上平行執行 Python 3.11、3.12、3.13。
* **檢查項目**：
  1. 程式碼語法檢查（`compileall`）。
  2. 離線單元測試：
     * SQLite 初始化與結構檢查。
     * UPSERT 重複匯入更新驗證。
     * 參數化 SQL 查詢與防注入驗證。
     * JSON 巢狀階層萃取與異常資料容錯。
     * 溫度顏色區間分類正確性。
     * Folium 標記與 Popup HTML 產製。

### 3. 手動驗收項目 (Manual Acceptance)
* **真實 CWA API 即時連線驗證**：
  * 由於安全規範與 GitHub 公開儲存庫考量，正式 CWA 授權碼不納入 CI 自動化測試。
  * 驗收方式：本機配置有效之 `.env` 後執行 `python -m src.fetch_data`，確認終端機顯示「成功同步」且 `data/data.db` 內容更新。

---

## 七、實作假設與設計決策

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

## 八、已知限制

1. **即時連線需憑證**：存取 CWA 即時 API 必須具備有效授權碼；若未提供或網路受阻，系統將維持示範模式。
2. **地圖底圖圖資連線**：Folium 使用 OpenStreetMap 網路圖資，瀏覽地圖時電腦需保有外網連線能力以順利載入底圖。
