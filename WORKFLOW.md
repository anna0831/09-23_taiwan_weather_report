# HW10 Taiwan Weather Forecast 開發與評分檢核流程 (WORKFLOW.md)

本文件依據課程作業規格書 **「HW10 Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式」** 設計，將整體開發與評分流程結構化為 **Gate 1 至 Gate 6**。每個關卡清楚標示目標、評分權重、輸入、工作內容、產出、完成標準（DoD）與目前的實作驗證狀態。

---

## 系統總體目標與資料流程

透過 Python 串接氣象開放資料、進行資料剖析與清理、儲存至本機關聯式資料庫，並以互動式 Web 儀表板及地理地圖視覺化呈現。

```
[CWA Open Data] ──> [JSON (7-day forecast)] ──> [Python (analysis & parsing)]
                                                        │
[Taiwan Weather Dashboard] <── [Streamlit / Vercel] <── [SQLite (data.db)]
                                                        │
                              [Lifestyle Cards: Umbrella / AQI / Typhoon]
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
| **Gate 6** | 擴充：生活建議卡片與小女警形象 | **Optional (進階擴充)** | ✅ **已完成 (100%)** | `src/lifestyle.py`, `public/app.js`, `tests/test_lifestyle_cards.py` |

> 🎯 **進度自評結論**：**您已經完整通過 Gate 1 ~ Gate 4（基礎 100 分），超額完成 Gate 5（地圖視覺化），並已高質量完成 Gate 6（三大生活建議卡片、三項歷史缺陷排除、飛天小女警形象整合與 27 項自動化測試）！**

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

## Gate 6：生活建議卡片、主題擴充與歷史缺陷排除 (進階強化)

### 1. 關卡目標
* 於氣溫預報之外，擴充三張直覺且可測試的生活建議卡片（雨傘、空氣品質、颱風資訊）。
* 導入飛天小女警特派員官方形象資產（`public/powerpuff_girls.png`），完善雙平台響應式佈局。
* 徹底重現並修復三大歷史缺陷（「兩個今日天氣」、「熱門巡邏點無法點擊」、「最後同步時間錯誤」）。

### 2. 三大生活建議卡片實作規範
1. **雨量／降雨預報（今天要帶雨傘嗎？）**：
   * 資料來源：CWA 一週預報 `PoP` / `PoP12h`。
   * 指標命名：嚴格使用「降雨機率 (PoP)」，**絕不混淆為「預測雨量」**。
   * 決策閾值：
     * `≥ 60%`：建議帶傘（出門必備雨具）
     * `30% ~ 59%`：可自行斟酌（備傘為宜）
     * `< 30%`：無需帶傘（降雨機率低）
     * `None / 缺少`：資料不足
2. **空氣品質（今天要戴口罩嗎？）**：
   * 資料來源：環境部 (MOENV) 即時空氣品質監測資料。
   * 時態界定：**嚴格標記為「目前觀測值」**，未來預報日期標註「無此期間資料」。
   * 免責聲明：明載「本分級提供一般生活與戶外活動參考，非個人專屬醫療處方建議；呼吸道疾病患者請依醫師指示採取防護。」
3. **颱風資訊（需要提前準備物資嗎？）**：
   * 資料來源：CWA 颱風警報端點。
   * 狀態分級：
     * 警報發布中：提前準備物資（檢視防颱儲備、固定門窗）
     * 常態無警報：目前無相關警報（維持常態巡邏）
     * 連線異常：**資料暫時無法取得**（**嚴禁將 API 連線失敗當作無颱風！**）

### 3. 三大歷史缺陷修復記錄
1. **「兩個今日天氣」**：在 `public/app.js` 採用 `findIndex` 鎖定唯一今日索引，卡片迴圈內僅對單一元素上標籤，徹底杜絕雙重 Today。
2. **「熱門巡邏點無法點擊」**：在 `src/db.py` 種子資料中預載「臺北市」、「新北市」、「臺中市」、「高雄市」四都數據，並修復 `public/app.js` 與 `api/weather.py` 中的地區選取與按鈕狀態更新。
3. **「最後同步時間錯誤」**：建立 `SyncMetadata` 表記錄實際同步時間，並於 `api/weather.py` 取代寫死的 `"2026-09-23 11:17:26"`。

### 4. 完成標準 (Definition of Done)
- [x] `src/lifestyle.py` 核心邏輯完全解耦，閾值均可獨立測試。
- [x] 前端 Vercel Web 與 Streamlit 皆正確渲染三張生活建議卡片。
- [x] `public/powerpuff_girls.png` 於兩端介面皆能響應式呈現、無裁切、維持正確比例。
- [x] 27 項離線單元測試與整合測試全數通過（OK）。

---

## 📋 本次任務實際修改與新增檔案清單

| 類別 | 檔案路徑 | 修改性質 | 具體變更說明 |
| :--- | :--- | :---: | :--- |
| **後端核心** | `src/lifestyle.py` | **新增** | 實作帶傘判定、AQI 口罩分級、颱風狀態判定之純邏輯函式 |
| **資料儲存** | `src/db.py` | **修改** | 新增 `pop` 欄位、建立 `SyncMetadata`、`AirQualityObservations`、`TyphoonWarnings` 表與資料存取輔助函式，預載四都熱門點 |
| **資料抓取** | `src/fetch_data.py` | **修改** | 支援解析 CWA PoP 降雨機率、串接 MOENV AQI 觀測資料與 CWA 颱風警報 |
| **API 服務** | `api/weather.py` | **修改** | 整合 `lifestyle_advice` 輸出、動態讀取 `SyncMetadata` 最後同步時間、支援 `?region=...&date=...` 查詢 |
| **Web 前端** | `public/index.html` | **修改** | 加入特派員圓形頭像（`#hero-ppg-avatar`）、三張生活建議卡片容器（`.lifestyle-section`）與選中日期標籤 |
| **Web 樣式** | `public/style.css` | **修改** | 撰寫三張生活卡片之 Neo-Brutalism 普普風樣式、即時狀態徽章、特派員頭像響應式排版 |
| **Web 互動** | `public/app.js` | **修改** | 修復兩個 Today 標籤缺陷、修復熱門巡邏點點擊事件、實作日期點選與生活卡片即時聯動更新 |
| **作業儀表板** | `app.py` | **修改** | 於 Streamlit 主預報分頁嵌入特派員形象橫幅與三欄生活建議卡片（帶傘、口罩、防颱） |
| **靜態資產** | `public/powerpuff_girls.png` | **新增** | 飛天小女警特派員高清角色形象圖片（已備註著作權歸屬） |
| **自動化測試** | `tests/test_lifestyle_cards.py` | **新增** | 12 項測試：雨傘閾值（60/30）、降雨機率術語、AQI 建議與非醫療免責、觀測與預報區分、防颱與 API 失敗容錯 |
| **自動化測試** | `tests/test_vercel_api.py` | **修改** | 擴充端點整合測試，驗證靜態圖片載入、熱門都會區切換、生活建議欄位結構與異常處理 |
| **自動化測試** | `tests/test_weather_app.py` | **修改** | 調整資料庫區域數量斷言（支援 10 個預載地區），確保基礎資料庫與剖析測試全綠 |
| **專案文件** | `README.md` | **修改** | 更新核心階段、詳細記錄缺陷修復、三大生活卡片規格、/tmp 快取策略、環境變數與測試說明 |
| **專案文件** | `WORKFLOW.md` | **修改** | 擴充 Gate 6 流程、列出修改檔案、測試結果與已驗證 vs 需 API Key 驗證對照表 |

---

## 🧪 自動化測試結果 (Test Discovery Log)

於虛擬環境執行全套測試發現：
```text
$ .venv/bin/python -m unittest discover -s tests
...........................
----------------------------------------------------------------------
Ran 27 tests in 0.166s

OK
```

### 測試分組涵蓋明細：
1. **`tests/test_weather_app.py` (8 Tests)**：
   * `test_init_db`: 驗證資料表建立與欄位完整性。
   * `test_save_forecasts_upsert`: 驗證重複資料更新不重覆（UPSERT 防呆）。
   * `test_parse_weather_json_valid`: 驗證真實 CWA 範例 JSON 氣溫解析。
   * `test_parse_weather_json_fallback`: 驗證不合規 JSON 自動退回示範資料機制。
   * `test_parse_weather_json_missing_fields`: 驗證欄位缺失容錯機制。
   * `test_temperature_aggregation`: 驗證同日多時段最高溫取最大、最低溫取最小。
   * `test_color_categorization`: 驗證作業指定四段氣溫分色規則（<20, 20-25, 25-30, >30）。
   * `test_end_to_end_pipeline`: 驗證資料庫查詢與 Pandas 欄位型態轉換。
2. **`tests/test_lifestyle_cards.py` (12 Tests)**：
   * `test_umbrella_high_pop_suggests_umbrella`: 降雨機率 70% 建議帶傘。
   * `test_umbrella_medium_pop_optional`: 降雨機率 45% 可自行斟酌。
   * `test_umbrella_low_pop_no_umbrella`: 降雨機率 15% 無需帶傘。
   * `test_umbrella_missing_pop_insufficient_data`: 降雨機率為 None 標註資料不足。
   * `test_umbrella_metric_name_strict_pop`: 嚴禁使用「預測雨量」，必須標示「降雨機率 (PoP)」。
   * `test_air_quality_levels`: 驗證 AQI 30 (良好)、75 (普通)、120 (敏感族群注意)、160 (不健康)。
   * `test_air_quality_guideline_non_medical`: 驗證非醫療處方免責聲明。
   * `test_air_quality_observation_vs_forecast_distinction`: 驗證觀測值 vs 未來預報日期之無資料防護。
   * `test_typhoon_warning_active`: 驗證警報發布時防颱物資建議。
   * `test_typhoon_no_warning_normal`: 驗證常態無警報維持常態巡邏。
   * `test_typhoon_api_error_strict_not_no_warning`: **連線異常嚴格標示「資料暫時無法取得」，絕不可判定為無警報**。
   * `test_evaluate_umbrella_threshold_boundaries`: 驗證 60.0% 與 30.0% 邊界值。
3. **`tests/test_vercel_api.py` (7 Tests)**：
   * `test_server_serves_html`: 驗證首頁 HTML 與特派氣象站標題。
   * `test_server_serves_static_assets`: 驗證 CSS、JS 及 `powerpuff_girls.png` 靜態圖檔載入。
   * `test_api_weather_endpoint_returns_json`: 驗證 `/api/weather` 回傳格式與資料結構。
   * `test_api_weather_returns_lifestyle_advice`: 驗證回傳 JSON 包含 `lifestyle_advice` 且包含三大卡片完整欄位。
   * `test_api_weather_sync_action`: 驗證手動觸發 sync 參數行為。
   * `test_hot_patrol_regions_available`: 驗證「臺北市」、「新北市」、「臺中市」、「高雄市」可順暢查詢。
   * `test_lifestyle_date_switching`: 驗證指定 `date=YYYY-MM-DD` 參數可精確對應當日降雨機率。

---

## 🔍 已完成驗證 vs 仍需 API Key 驗證項目對照表

| 驗證範疇 | 功能細項 | 驗證方式 | 目前狀態 | 備註說明 |
| :--- | :--- | :--- | :---: | :--- |
| **離線業務邏輯** | 降雨機率帶傘判定邏輯（60/30 閾值） | 自動化單元測試 (`test_lifestyle_cards.py`) | ✅ **100% 已驗證** | 邊界值 60.0%、30.0%、無資料皆涵蓋 |
| **離線業務邏輯** | 降雨機率術語限制（非預測雨量） | 字串比對斷言測試 | ✅ **100% 已驗證** | 介面無任何預測雨量混淆字眼 |
| **離線業務邏輯** | AQI 空品分級與非醫療處方警語 | 單元測試與文案檢驗 | ✅ **100% 已驗證** | 標註「目前觀測值」與免責說明 |
| **離線業務邏輯** | 颱風警報狀態判定與 API 異常容錯 | 單元測試容錯情境 | ✅ **100% 已驗證** | 連線失敗嚴格顯示「資料暫時無法取得」 |
| **缺陷排除** | 兩個今日天氣消除 | 前端程式碼與渲染邏輯驗證 | ✅ **100% 已驗證** | 僅鎖定單一 Today 標籤 |
| **缺陷排除** | 熱門巡邏點（北/新北/中/高）點擊 | 整合測試與 API 端點查詢 | ✅ **100% 已驗證** | 四大都會區資料與切換皆正常 |
| **缺陷排除** | 最後同步時間動態呈現 | API 回傳值驗證（移除寫死字串） | ✅ **100% 已驗證** | 透過 `SyncMetadata` 動態取得 |
| **介面與排版** | 飛天小女警形象展示（`public/powerpuff_girls.png`） | HTTP 200 靜態檔案載入測試與本機預覽 | ✅ **100% 已驗證** | 雙平台（Vercel/Streamlit）皆嵌入 |
| **介面與排版** | 7 天預報卡片點擊切換生活卡片日期 | 前端聯動事件實作與 API 參數測試 | ✅ **100% 已驗證** | 支援動態切換日期查看當日建議 |
| **線上生產介接** | CWA 一週預報即時同步 (`F-D0047-091`) | 需中央氣象署有效授權碼 | ⚠️ **需 API Key** | 目前以完整結構之 Schema 種子資料運行；使用者在 `.env` 或 Vercel 設定 `CWA_API_KEY` 後即可一鍵線上即時同步最新氣象 |
| **線上生產介接** | CWA 即時颱風警報抓取 (`W-C0034-001`) | 需中央氣象署有效授權碼 | ⚠️ **需 API Key** | 已完成解析程式與容錯保護；無金鑰時啟動示範警報資料或常態巡邏提示 |
| **線上生產介接** | MOENV 即時空氣品質抓取 | 公開 Open Data 端點 / 選用 Key | ⚠️ **選用 API Key** | 內建開放 API 端點呼叫與高品質示範觀測站資料，支援 `MOENV_API_KEY` 擴充 |

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

