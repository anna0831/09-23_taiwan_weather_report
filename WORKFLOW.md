# HW10 Taiwan Weather Forecast 開發與評分檢核流程 (WORKFLOW.md)

本文件依據課程作業規格書 **「HW10 Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式」** 設計，將整體開發與評分流程結構化為 **Gate 1 至 Gate 5**。每個關卡清楚標示目標、評分權重、輸入、工作內容、產出、完成標準（DoD）與目前的實作驗證狀態。

---

## 系統總體目標與資料流程

透過 Python 串接氣象開放資料、進行資料剖析與清理、儲存至本機關聯式資料庫，並以互動式 Web 儀表板及地理地圖視覺化呈現。

```
[CWA Open Data] ──> [JSON (7-day forecast)] ──> [Python (analysis & parsing)]
                                                        │
[Taiwan Weather Dashboard] <── [Streamlit (web app)] <── [SQLite (data.db)]
```

---

## 關卡一覽與進度總結 (Status Overview)

| 關卡代號 | 階段名稱 | 評分比重 | 實作狀態 | 關鍵佐證檔案 |
| :---: | :--- | :---: | :---: | :--- |
| **Gate 1** | 取得 CWA API 資料 | **20%** | ✅ **已完成 (100%)** | `src/config.py`, `src/fetch_data.py`, `.env` |
| **Gate 2** | 分析 JSON，提取氣溫資料 | **20%** | ✅ **已完成 (100%)** | `src/fetch_data.py`, `tests/test_weather_app.py` |
| **Gate 3** | 存入 SQLite 資料庫 | **20%** | ✅ **已完成 (100%)** | `src/db.py`, `data/data.db`, `tests/test_weather_app.py` |
| **Gate 4** | Streamlit 氣溫預報 Web App | **40%** | ✅ **已完成 (100%)** | `app.py`, `src/db.py` |
| **Gate 5** | 進階：台灣地圖視覺化 | **Optional (加分)** | ✅ **已完成 (100%)** | `app.py`, `src/config.py`, `tests/test_weather_app.py` |

> 🎯 **進度自評結論**：**您已經完整通過 Gate 1 ~ Gate 4（基礎 100 分），並已超額完成 Gate 5（進階加分項）！**

---

## Gate 1：取得 CWA API 資料 (配分：20%)

### 1. 關卡目標
* 使用中央氣象署（CWA）Open Data API 取得台灣六大區域（北部、中部、南部、東北部、東部、東南部）之一週天氣預報。
* 回傳格式必須為 **JSON** 格式。

### 2. 評分細項
* 取得資料：**10%**
* 觀察 JSON：**5%**
* 程式品質：**5%**

### 3. 工作內容與步驟
1. 註冊並取得個人的 CWA API Key，儲存於 `.env` 中安全隔離。
2. 使用 `requests.get()` 呼叫氣象署 API（支援 `F-D0047-091` 一週預報與 `F-C0032` 通用端點）。
3. 加入 SSL 憑證相容性容錯處理，確保 Windows 環境下不會因憑證問題中斷。
4. 使用 `resp.json()` 取得資料，並可透過 `json.dumps(data, indent=2, ensure_ascii=False)` 格式化觀察 JSON 結構。

### 4. 完成標準 (Definition of Done)
- [x] 成功取得 HTTP 200 回應與有效之天氣預報 JSON。
- [x] API 授權碼隔離於環境變數或 `.env`，不寫入程式碼或 Git。
- [x] 具備連線超時（`timeout`）與異常處理機制。

---

## Gate 2：分析 JSON，提取氣溫資料 (配分：20%)

### 1. 關卡目標
* 分析 JSON 結構，找出並提取每日最高氣溫（MaxT）與最低氣溫（MinT）。
* 在資料結構中正確對應地區（Location）與預報時段（Time）。

### 2. 評分細項
* 提取正確：**10%**
* 觀察資料：**5%**
* 程式品質：**5%**

### 3. 分析重點與資料階層
```
JSON
 └─ records
      └─ Locations / location[] (地區名稱: LocationName / locationName)
           └─ WeatherElement / weatherElement[] (天氣要素)
                ├─ elementName: MinT / 最低溫度
                └─ elementName: MaxT / 最高溫度
                     └─ time / Time[] (預報日期與時間)
                          └─ ElementValue / parameter (氣溫數值)
```

### 4. 提取結果結構規範
整理為標準 Pandas DataFrame，欄位必須包含：
| 欄位名稱 | 型別 | 說明 | 範例 |
| :--- | :--- | :--- | :--- |
| `regionName` | TEXT | 地區或縣市名稱 | 北部地區、中部地區、南部地區 |
| `dataDate` | TEXT | 預報日期 (`YYYY-MM-DD`) | 2026-09-23 |
| `mint` | REAL | 最低氣溫 (°C) | 22.0 |
| `maxt` | REAL | 最高氣溫 (°C) | 30.0 |

### 5. 完成標準 (Definition of Done)
- [x] 能解析包含六大區域在內的全台各分區預報。
- [x] 同一日期的多時段資料正確彙整（最低溫取最小值，最高溫取最大值）。
- [x] 通過單元測試（包含缺少欄位與異常字串之容錯檢查）。

---

## Gate 3：存入 SQLite 資料庫 (配分：20%)

### 1. 關卡目標
* 將整理後的氣溫資料持久化儲存到 SQLite 資料庫 `data.db`。
* 撰寫驗證 SQL 查詢，確認資料已正確寫入。

### 2. 評分細項
* 儲存資料：**10%**
* 查詢驗證：**5%**
* 程式品質：**5%**

### 3. 資料庫設計規格
建立資料表 `TemperatureForecasts`：
```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    mint REAL NOT NULL,
    maxt REAL NOT NULL,
    CONSTRAINT uq_region_date UNIQUE (regionName, dataDate)
);
```

### 4. 防重防呆機制 (UPSERT)
執行儲存時採用參數化更新語法，重複匯入時自動更新原紀錄，避免資料重複：
```sql
INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
VALUES (?, ?, ?, ?)
ON CONFLICT(regionName, dataDate) DO UPDATE SET
    mint = excluded.mint,
    maxt = excluded.maxt;
```

### 5. 驗證查詢
1. **列出所有地區名稱**：
   ```sql
   SELECT DISTINCT regionName FROM TemperatureForecasts;
   ```
2. **查詢指定地區（如中部地區）資料**：
   ```sql
   SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區' ORDER BY dataDate;
   ```

### 6. 完成標準 (Definition of Done)
- [x] `data/data.db` 成功建立並包含 `TemperatureForecasts` 表。
- [x] 資料重複寫入時總筆數不增加，數值被更新。
- [x] 所有查詢均採用 `?` 參數化查詢，杜絕 SQL 注入攻擊。

---

## Gate 4：Streamlit 氣溫預報 Web App (配分：40%)

### 1. 關卡目標
* 建立互動式 Web App，**從 SQLite 查詢資料**（嚴禁直接呼叫 API）。
* 提供下拉選單選擇地區，即時顯示該地區未來一週氣溫折線圖與資料表格。

### 2. 評分細項
* 下拉選單：**10%**
* 折線圖與表格：**15%**
* SQLite 查詢：**10%**
* 程式品質：**5%**

### 3. 功能需求規範
1. **下拉選單選擇地區**：
   * 選項動態來自 `SELECT DISTINCT regionName FROM TemperatureForecasts`。
   * 使用者選擇後，即時切換對應地區的預報。
2. **最高/最低溫折線圖**：
   * X 軸為日期（Date），Y 軸為氣溫（°C）。
   * 雙色線條：**MaxT 為紅色**、**MinT 為藍色**。
3. **一週資料表格**：
   * 清楚呈現日期（Date）、最低溫（MinT）、最高溫（MaxT）。
   * 額外計算衍生欄位「溫差 (°C)」，提升可讀性。
4. **架構約束**：
   * Web App 的所有圖表與表格數據**必須自 SQLite 資料庫查詢**，不可在使用者刷新頁面時直接連線外部 API。

### 4. 完成標準 (Definition of Done)
- [x] 執行 `streamlit run app.py` 能正常開啟且無警告崩潰。
- [x] 下拉選單切換流暢，圖表與表格隨選取地區即時更新。
- [x] 表格與折線圖呈現完整的一週（7 天）預報數據。

---

## Gate 5：進階：台灣地圖視覺化 (加分項，Optional)

### 1. 關卡目標
* 製作互動式台灣天氣地圖，顯示各區當日平均溫度（建議使用 Folium + Streamlit）。

### 2. 視覺化規範
1. **依平均溫度分級色彩**（依作業圖規定）：
   * 🔵 **< 20°C**：藍色
   * 🟢 **20 - 25°C**：綠色
   * 🟠 **25 - 30°C**：黃色 / 橘色
   * 🔴 **> 30°C**：紅色
2. **點擊標記彈出視窗 (Popup)**：
   * 點擊標記時，顯示：
     * 地區名稱（例如：中部地區）
     * 當日日期（Date）
     * 最低溫（Min: 20°C）
     * 最高溫（Max: 30°C）
     * 平均溫
3. **日期動態切換**：
   * 提供日期選取器（Select Date），地圖上的標記數值與顏色隨選取日期即時改變。
   * 右側並列展示當日全台各地區預報摘要表。

### 3. 完成標準 (Definition of Done)
- [x] 地圖完整定位台灣全島各分區中心座標。
- [x] 氣溫分色規則精準符合標準。
- [x] 點擊標記能彈出包含地區與高低溫之 Popup 視窗。

---

## 重要注意事項檢核清單 (作業規範對照)

對照作業簡報右下角之「重要注意事項」：

| 規範項目 | 規範內容 | 目前檢核結果 |
| :---: | :--- | :---: |
| **1** | 使用自己的 CWA API Key，不能用老師提供的金鑰繳交。 | ✅ **符合**（金鑰已放入本機 `.env`） |
| **2** | Streamlit 必須從 SQLite 查詢資料，不可直接呼叫 API。 | ✅ **符合**（`app.py` 嚴格自 `data.db` 讀取） |
| **3** | 確認六個地區的資料都正確。 | ✅ **符合**（北部、中部、南部、東北部、東部、東南部皆具備） |
| **4** | 表格與圖表需顯示一週（7天）資料。 | ✅ **符合**（涵蓋 2026-09-21 至 2026-09-27 完整一週） |
| **5** | 進階的台灣地圖為加分功能，可在基本功能完成後再製作。 | ✅ **超額完成**（Gate 5 互動地圖已實作並整合完成） |

---

## 本機執行與操作指南

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 執行資料同步（一次即可）
```bash
python -m src.fetch_data
```

### 3. 啟動 Web App

#### 模式 A：Vercel 原生網頁版 (HTML5 + Vanilla CSS + Chart.js + Leaflet)
```bash
python dev_server.py
```
或使用 npm：
```bash
npm run dev
```
瀏覽器開啟 `http://localhost:3000` 即可體驗極速響應、玻璃擬態設計、全正常氣象圖示的現代化儀表板。

#### 模式 B：Streamlit 課程作業版 (已修復圖示)
```bash
streamlit run app.py
```
啟動後於瀏覽器存取 `http://localhost:8501`。

---

## Vercel 部署指引 (Deploy to Vercel)

本專案已完整配置 Vercel 規格檔案（`vercel.json`、`api/weather.py`、`public/`）：

### 方法 1：透過 GitHub 自動部署（推薦）
1. 將專案程式碼 push 至您的 GitHub repository。
2. 登入 [Vercel 官網](https://vercel.com/)，點選 **"Add New Project"**。
3. 匯入本 GitHub repository，Vercel 將自動辨識 `vercel.json`。
4. 在 **Environment Variables** 新增 `CWA_API_KEY`（填入您的氣象署金鑰）。
5. 點選 **"Deploy"** 即可獲得專屬上線網址（例如 `https://your-project.vercel.app`）！

### 方法 2：使用 Vercel CLI 本機部署
```bash
npx vercel
```
依終端機引導登入並確認預設設定即可立即部署發布。

