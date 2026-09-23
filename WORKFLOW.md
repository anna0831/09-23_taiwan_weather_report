# Taiwan Weather Forecast Web App 開發流程指南 (WORKFLOW.md)

本文件為 **Taiwan Weather Forecast Web App** 之標準開發流程與技術規格指引，專門設計給軟體工程團隊與資訊工程系學生閱讀與維護。本指南詳細定義專案目標、系統資料流程、分階段開發規範（包含輸入、工作內容、產出與完成標準）、安全準則、測試策略與目前實作進度。

---

## 一、專案目標與系統定位

本專案旨在透過中央氣象署（CWA）開放資料平臺，獲取台灣各分區之氣象預報資料，經過自動化資料清理與關聯式資料庫持久化儲存後，運用現代化 Web 視覺化技術建立具備折線圖、統計表格與地理空間地圖的互動式天氣預報 Web 應用程式。

* **GitHub Repository**：[https://github.com/anna0831/09-23_taiwan_weather_report](https://github.com/anna0831/09-23_taiwan_weather_report)
* **核心技術棧**：Python 3.10+、Requests、Pandas、SQLite 3、Streamlit、Folium、Unittest

---

## 二、端到端資料流程 (Data Flow)

資料從外部氣象署端點流向使用者瀏覽器之完整路徑如下：

```
[中央氣象署 CWA API] (資料集代碼: F-C0032-003)
         │
         ▼  (1) requests GET 請求 (攜帶授權金鑰 Authorization)
[原始 JSON 封裝資料]
         │
         ▼  (2) Python JSON 解析與階層巡覽
[巢狀資料萃取 (MinT / MaxT / 時段)]
         │
         ▼  (3) Pandas 清理、跨日時段聚合 (取每日 MinT 最小值、MaxT 最大值)
[結構化 DataFrame] (欄位: regionName, dataDate, mint, maxt)
         │
         ▼  (4) SQLite 參數化寫入 (UPSERT: ON CONFLICT DO UPDATE)
[SQLite 資料庫 (data/data.db)] (資料表: TemperatureForecasts)
         │
         ▼  (5) 參數化 SQL 查詢 (按地區查詢、按日期查詢)
[Streamlit 應用程式 (app.py)]
   ├── 📈 地區選擇與氣溫趨勢折線圖 (MaxT 紅線 / MinT 藍線) & 數據表格
   └── 🗺️ 日期選擇與 Folium 台灣天氣地圖 (座標標記、四段氣溫分色、Popup 互動視窗)
```

---

## 三、安全與資料處理三大黃金法則 (Core Engineering Rules)

在專案的任何開發或維護過程中，必須嚴格遵守以下三項原則：

| 原則項目 | 規則說明 | 實作要求 |
| :--- | :--- | :--- |
| **1. API Key 不入庫** | 任何環境變數、授權碼或機密資訊絕不寫入程式碼、測試檔案或 Git 歷史。 | 授權碼必須透過 `.env` 檔案或系統環境變數（`CWA_API_KEY`）注入，`.gitignore` 必須嚴格忽略 `.env`。 |
| **2. 參數化 SQL 查詢** | 杜絕字串拼接 SQL，防止 SQL Injection（隱碼攻擊）。 | 所有動態條件查詢必須使用參數化語法（例如：`WHERE regionName = ?`，傳入元組 `(region_name,)`）。 |
| **3. 防重防呆 UPSERT** | 同一地區與日期的資料重複匯入時，必須自動更新數值而非新增重複紀錄。 | 資料表必須建立 `UNIQUE(regionName, dataDate)` 約束，插入資料時採用 `ON CONFLICT(...) DO UPDATE SET` 語法。 |

---

## 四、漸進式開發階段規範 (Development Phases)

本專案將整體工程拆解為 12 個明確的開發階段。每一階段皆可單獨開發、驗證與審查：

```
[階段 1: API 取得] ──> [階段 2: JSON 解析] ──> [階段 3: 資料清理] ──> [階段 4: 資料庫建立]
                                                                             │
[階段 8: 折線圖] <── [階段 7: 地區選擇] <── [階段 6: Streamlit 介面] <── [階段 5: SQL 查詢]
         │
         ▼
[階段 9: 資料表] ──> [階段 10: 日期選擇] ──> [階段 11: 台灣地圖] ──> [階段 12: README 與測試]
```

---

### 階段 1：API 取得 (CWA API 請求)
* **輸入**：CWA 開放資料 API URL (`https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-003`) 與授權金鑰 `CWA_API_KEY`。
* **工作內容**：
  1. 建立設定讀取函式，優先自系統環境變數或 `.env` 檔案載入 `CWA_API_KEY`。
  2. 使用 `requests.get()` 呼叫氣象署端點，加入 Header 或 URL 參數認證。
  3. 實作 HTTP 狀態碼檢查（`raise_for_status()`）與連線異常處理機制。
* **產出**：原始 JSON 回應字典物件（Dictionary）。
* **完成標準 (DoD)**：
  * [x] 當環境變數未提供金鑰時，程式拋出清晰警告或錯誤提示，不致未預期崩潰。
  * [x] API 授權碼不硬編碼在任何模組中。

---

### 階段 2：JSON 解析 (階層巡覽)
* **輸入**：氣象署回傳的原始 JSON 資料。
* **工作內容**：
  1. 巡覽 JSON 階層結構：`records -> location -> weatherElement -> time -> parameter`。
  2. 定位代表地區名稱之 `locationName`。
  3. 篩選目標天氣要素：`elementName == 'MinT'`（最低溫）與 `elementName == 'MaxT'`（最高溫）。
* **產出**：提取出各地區、預報時段（`startTime` / `endTime`）與溫度數值之未加工清單。
* **完成標準 (DoD)**：
  * [x] 成功解析標準 CWA JSON 結構。
  * [x] 面對缺少欄位或空陣列之異常 JSON，能優雅回傳空結果而不拋出未處理異常。

---

### 階段 3：資料清理 (Pandas 整合與跨日時段彙整)
* **輸入**：解析後的時段與溫度列表。
* **工作內容**：
  1. 擷取時間字串的前 10 碼作為日期基準（`YYYY-MM-DD`）。
  2. 解決跨日與日夜時段拆分問題：同一個地區在同一日期若有多筆預報時段，**最低溫取當日所有時段之最小值**，**最高溫取當日所有時段之最大值**。
  3. 數值型別轉換為浮點數（`float`），並防呆過濾非數值字串。
  4. 整合為包含欄位 `regionName`, `dataDate`, `mint`, `maxt` 之 Pandas DataFrame。
* **產出**：乾淨、規範化之預報 DataFrame。
* **完成標準 (DoD)**：
  * [x] 每個地區每個日期僅產生唯一一筆代表記錄。
  * [x] 數值四捨五入至小數點後第一位。

---

### 階段 4：資料庫建立 (SQLite 與資料表設計)
* **輸入**：資料庫路徑 `data/data.db`。
* **工作內容**：
  1. 建立 SQLite 資料庫檔案及連線工廠函式。
  2. 執行 DDL 建立資料表 `TemperatureForecasts`：
     * `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
     * `regionName`: `TEXT NOT NULL`
     * `dataDate`: `TEXT NOT NULL`
     * `mint`: `REAL NOT NULL`
     * `maxt`: `REAL NOT NULL`
     * 唯一約束：`CONSTRAINT uq_region_date UNIQUE (regionName, dataDate)`
  3. 實作以 `ON CONFLICT(regionName, dataDate) DO UPDATE SET mint=excluded.mint, maxt=excluded.maxt` 之寫入邏輯（UPSERT）。
* **產出**：具備防重機制的 SQLite 資料庫檔案與持久化資料表。
* **完成標準 (DoD)**：
  * [x] 呼叫寫入函式多次寫入相同資料時，總筆數不增加，溫度欄位被更新。

---

### 階段 5：SQL 查詢模組 (參數化查詢)
* **輸入**：查詢條件（地區名稱 `regionName` 或日期 `dataDate`）。
* **工作內容**：
  1. 撰寫 `get_distinct_regions()`：`SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY id;`
  2. 撰寫 `get_forecasts_by_region(region_name)`：`SELECT * FROM TemperatureForecasts WHERE regionName = ? ORDER BY dataDate ASC;`
  3. 撰寫 `get_distinct_dates()`：`SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate ASC;`
  4. 撰寫 `get_forecasts_by_date(data_date)`：`SELECT * FROM TemperatureForecasts WHERE dataDate = ? ORDER BY regionName ASC;`
* **產出**：回傳地區字串陣列或對應查詢結果之 Pandas DataFrame。
* **完成標準 (DoD)**：
  * [x] 全數採用參數化佔位符 `?`，通過 SQL 注入攻擊字串（如 `' OR '1'='1`）安全測試。

---

### 階段 6：Streamlit 介面與基本架構
* **輸入**：Streamlit 框架環境與資料庫查詢函式。
* **工作內容**：
  1. 設定頁面屬性 `st.set_page_config(layout="wide")`。
  2. 規劃系統側邊欄（API 狀態顯示、手動同步按鈕、示範資料載入按鈕）。
  3. 規劃主畫面分頁結構：分頁一「📈 地區一週氣溫預報」、分頁二「🗺️ 全台天氣互動地圖」。
  4. 加入資料庫初次載入檢查：若為空庫則自動注入示範種子資料（Seed Data）。
* **產出**：可運行的 Web 前端應用程式入口 `app.py`。
* **完成標準 (DoD)**：
  * [x] 執行 `python -m streamlit run app.py` 能成功啟動 Web 服務並在瀏覽器顯示頁面。

---

### 階段 7：地區選擇 (Select Region 互動操作)
* **輸入**：從資料庫查詢所得之 `regions` 清單。
* **工作內容**：
  1. 於分頁一設置 `st.selectbox("Select Region (選擇地區)", options=regions)`。
  2. 預設選取「中部地區」或「北部地區」。
  3. 聯動查詢函式，依選定地區即時提取該區一週數據。
* **產出**：所選地區之一週預報數據及最低溫/最高溫/平均溫統計指標卡。
* **完成標準 (DoD)**：
  * [x] 切換下拉選單時，畫面數據即時動態刷新。

---

### 階段 8：溫度折線圖 (一週最高與最低溫)
* **輸入**：所選地區之一週預報 DataFrame。
* **工作內容**：
  1. 重新索引資料（Index 為 `Date`，欄位為 `MaxT` 與 `MinT`）。
  2. 繪製折線圖：**MaxT 為紅色線條（#EF4444）**，**MinT 為藍色線條（#3B82F6）**。
  3. 設定 X 軸為日期，Y 軸為溫度數值。
* **產出**：清楚標示一週高低溫走勢之互動式雙色折線圖。
* **完成標準 (DoD)**：
  * [x] 圖表同時正確呈現最高溫與最低溫兩條走勢曲線，色彩對比清晰。

---

### 階段 9：資料表呈現 (預報明細與溫差)
* **輸入**：所選地區之一週預報 DataFrame。
* **工作內容**：
  1. 欄位重新命名：`Date`, `MinT (°C)`, `MaxT (°C)`。
  2. 新增衍生計算欄位：`溫差 (°C) = MaxT - MinT`。
  3. 透過 `st.dataframe` 呈現整齊的結構化表格。
* **產出**：完整、清晰之一週數據明細表。
* **完成標準 (DoD)**：
  * [x] 表格資料與折線圖完全一致，溫差計算準確。

---

### 階段 10：日期選擇 (Select Date 聯動地圖)
* **輸入**：從資料庫查詢所得之 `available_dates` 清單。
* **工作內容**：
  1. 於分頁二設置 `st.selectbox("Select Date (選擇日期)", options=available_dates)`。
  2. 聯動查詢特定日期全台各地區預報資料。
* **產出**：該特定日期全台灣所有地區的溫度集合。
* **完成標準 (DoD)**：
  * [x] 能依使用者指定日期精準過濾當日全台數據。

---

### 階段 11：台灣天氣地圖 (Folium 視覺化與溫度分色)
* **輸入**：當日全台數據、各分區中心地理座標與平均氣溫計算邏輯。
* **工作內容**：
  1. 初始化 Folium 地圖（中心定位：23.7°N, 120.9°E，底圖：OpenStreetMap）。
  2. 設定台灣主要分區代表座標：
     * 北部：(25.04, 121.55)、東北部：(24.75, 121.75)、中部：(24.15, 120.68)
     * 東部：(23.99, 121.60)、南部：(22.62, 120.31)、東南部：(22.75, 121.15)
  3. 依據平均溫度 `(mint + maxt) / 2` 判定標記顏色：
     * 🔵 **< 20°C**：藍色 (`blue`)
     * 🟢 **20°C ~ 25°C**：綠色 (`green`)
     * 🟠 **25°C ~ 30°C**：橘色 (`orange`)
     * 🔴 **> 30°C**：紅色 (`red`)
  4. 為各分區加入 `CircleMarker` 與點擊彈出視窗（Popup），顯示地區、最低溫、最高溫與平均溫。
  5. 結合 `streamlit-folium` 嵌入 Web 頁面，並在右側並列展示當日全區氣溫表。
* **產出**：直觀之全台天氣熱區互動地圖儀表板。
* **完成標準 (DoD)**：
  * [x] 點擊標記能正常彈出 Popup 視窗。
  * [x] 標記顏色嚴格符合溫度區間規則。

---

### 階段 12：README 文件與自動化測試套件
* **輸入**：完整專案程式碼與規格需求。
* **工作內容**：
  1. 撰寫單元測試套件 `tests/test_weather_app.py`（離線測試架構）。
  2. 撰寫 `README.md`，詳述專案架構、安裝指令、離線測試與手動連線驗收指引。
  3. 配置 `.gitignore` 排除 SQLite 資料庫與本機機密。
* **產出**：高品質之測試程式碼與教學文件。
* **完成標準 (DoD)**：
  * [x] 執行 `python -m unittest tests/test_weather_app.py` 全數通過。

---

## 五、測試與驗收雙軌策略 (Testing & Acceptance Strategy)

為落實資安與可重複測試性，本專案將測試與驗收嚴格區分為兩大類別：

### 1. 離線自動化測試 (無需 API Key、無需即時外網)
* **適用範疇**：所有程式邏輯、JSON 資料解析、日期匯總、SQLite 操作、SQL 參數化防注入、溫度顏色映射、Folium HTML 生成。
* **測試機制**：
  * 採用測試程式內嵌之少量、結構標準的範例 JSON。
  * 採用暫存資料庫（`tempfile.TemporaryDirectory`），測試完畢自動銷毀，不污染正式資料庫。
* **執行命令**：
  ```bash
  python -m unittest discover -s tests -p "test_*.py"
  ```
* **驗收標準**：測試應在無網路環境下 100% 通過（8 項測試全數 `OK`）。

### 2. 真實 API 手動驗收 (需授權碼、需對外網路連線)
* **適用範疇**：中央氣象署 CWA 伺服器即時通訊、網路憑證驗證與線上最新預報下載。
* **驗收前提**：
  1. 開發者已至氣象資料開放平臺取得個人 API 授權碼。
  2. 本地已建立 `.env` 檔案並填寫 `CWA_API_KEY=您的授權碼`。
* **手動驗收步驟**：
  1. 在終端機執行同步模組：
     ```bash
     python -m src.fetch_data
     ```
  2. 觀察終端機輸出，確認出現 `[OK] 成功同步 ... 筆天氣預報資料至資料庫！`。
  3. 開啟 Web 介面（`streamlit run app.py`），點擊側邊欄「🔄 同步 CWA 資料」，確認介面能正確反映線上即時數據。
* **注意事項**：若缺少金鑰，系統將明確維持「示範資料模式」，絕不虛報為通過真實 API 驗證。

---

## 六、目前實作進度追蹤 (Progress Tracker)

依據目前工作區的實際檔案分析，各項模組與功能的實作現況如下：

| 開發階段 | 項目名稱 | 實作狀態 | 代碼佐證與佐證檔案 |
| :---: | :--- | :---: | :--- |
| **01** | API 請求模組 | **已完成** | `src/fetch_data.py` (實作 requests 與授權帶入) |
| **01-驗收** | 真實 CWA 線上連線 | **待驗證** | *需手動提供授權碼驗證，目前處於離線示範模式* |
| **02** | JSON 階層解析 | **已完成** | `src/fetch_data.py`、`tests/test_weather_app.py` (單元測試通過) |
| **03** | 資料清理與跨日聚合 | **已完成** | `src/fetch_data.py` (Pandas 日期最小/最大溫聚合) |
| **04** | SQLite 資料表與 UPSERT | **已完成** | `src/db.py` (實作 `ON CONFLICT DO UPDATE`)、`tests/test_weather_app.py` |
| **05** | 參數化 SQL 查詢 | **已完成** | `src/db.py`、`tests/test_weather_app.py` (防注入測試通過) |
| **06** | Streamlit 介面與導航 | **已完成** | `app.py` (Tab 分頁與側邊欄控制) |
| **07** | 地區選擇互動 | **已完成** | `app.py` (Select Region 聯動查詢) |
| **08** | 溫度折線圖 (紅/藍) | **已完成** | `app.py` (`st.line_chart` 紅線 MaxT、藍線 MinT) |
| **09** | 資料表與溫差計算 | **已完成** | `app.py` (`st.dataframe` 顯示預報明細與溫差) |
| **10** | 日期選擇互動 | **已完成** | `app.py` (Select Date 聯動查詢) |
| **11** | Folium 台灣地圖視覺化 | **已完成** | `app.py` (`st_folium`、溫度四段分色、Popup 標記) |
| **12** | 測試套件與說明文件 | **已完成** | `tests/test_weather_app.py` (8/8 通過)、`README.md` |

### 實作狀態說明：
- ✅ **已完成 (8/8 單元測試通過)**：JSON 解析、資料清理、SQLite 建立、UPSERT 防重複、參數化 SQL 查詢、Streamlit 介面、折線圖、資料表、日期選擇、Folium 地圖、離線測試與說明文件。
- ⏳ **待驗證 (手動驗收項目)**：使用真實 CWA 授權碼向氣象署伺服器發送 live 請求（因受限於資安規則，未配置個人真實金鑰時保持安全防呆）。
