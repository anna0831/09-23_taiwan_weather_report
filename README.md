# Taiwan Weather Forecast Web App ⛅ · 飛天小女警特派氣象站 💖

> **全台即時氣象大數據儀表板 · 5-Stage 完整開發 · The Powerpuff Girls 普普漫畫風 · Vercel Serverless 雲端部署**

[![CI Workflow](https://github.com/anna0831/09-23_taiwan_weather_report/actions/workflows/ci.yml/badge.svg)](https://github.com/anna0831/09-23_taiwan_weather_report/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-black?logo=vercel)](https://09-23-taiwan-weather-report.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 線上展示與快速預覽 (Live Demo Links)

* 🚀 **Vercel 正式上線網址 (Live Demo)**：[https://09-23-taiwan-weather-report.vercel.app](https://09-23-taiwan-weather-report.vercel.app)
* 🐙 **GitHub 專案原始碼**：[https://github.com/anna0831/09-23_taiwan_weather_report](https://github.com/anna0831/09-23_taiwan_weather_report)
* 💻 **本機一鍵啟動預覽**：
  * **Vercel Web 原生版**（HTML5 + Vanilla CSS + Chart.js + Leaflet）：`http://localhost:3000`
  * **Streamlit 作業版**（Streamlit + Folium + Altair）：`http://localhost:8501`

---

## 🎀 專案特色與主題設計 (The Powerpuff Girls Theme)

本專案全面注入 **飛天小女警 (The Powerpuff Girls)** 經典美式卡通普普風（Retro Cartoon Pop & Neo-Brutalism）：
1. 🌸 **花花 Blossom (隊長)**：櫻桃熱粉紅（`#FF3377`），守護一週最高溫 (MaxT) 曲線與標題光暈。
2. 🫧 **泡泡 Bubbles (甜美)**：晴空蔚藍（`#00B4D8`），標示一週最低溫 (MinT) 曲線與當前均溫。
3. ⚡ **毛毛 Buttercup (活力)**：青檸鮮綠（`#52B72A`），擔任活力監控標籤與最大溫差把關。
4. 🍬 **精緻視覺排版**：採用 Google Fonts **Fredoka** 圓潤字體、立體漫畫實心陰影（`4px 4px 0px #231244`）、愛心背景漸層，並**徹底解決今日氣溫卡片遮擋問題**，以及**完全移除 OpenStreetMap 地圖浮水印**。

---

## 🎯 核心開發階段 (Core Stages)

本專案依據作業規範與軟體工程最佳實踐，劃分為六大漸進式關卡（Gate 1 ~ Gate 6）：

```
[Stage 1: CWA API Ingestion] ──> [Stage 2: JSON Parsing & ETL]
                                         │
[Stage 5: Map Visualization] <── [Stage 4: Web Dashboard] <── [Stage 3: SQLite Storage]
                                         │
                   [Stage 6: Lifestyle Advice Cards & PPG Expansion]
```

| 階段 | 階段名稱 | 關鍵職責 | 核心產出檔案 | 完成標準 (DoD) |
| :---: | :--- | :--- | :--- | :--- |
| **Stage 1** | **CWA API 資料介接** | 串接氣象署 Open Data API，處理 SSL 憑證相容性，機密金鑰環境隔離 | `src/config.py`, `src/fetch_data.py`, `.env` | ✅ 成功取得 HTTP 200 JSON，API Key 不入庫 |
| **Stage 2** | **JSON 解析與清洗** | 剖析巢狀 JSON，萃取各地區每日 MaxT、MinT，跨時段日期聚合 | `src/fetch_data.py`, `tests/test_weather_app.py` | ✅ 支援全台 22 縣市與分區，清洗為標準 DataFrame |
| **Stage 3** | **SQLite 資料庫儲存** | 設計 `TemperatureForecasts` 表，實作 UPSERT（防重防呆）與參數化查詢 | `src/db.py`, `data/data.db` | ✅ 重複執行時更新不重複，杜絕 SQL Injection |
| **Stage 4** | **互動氣象 Web App** | 打造雙色平滑折線圖、7天預報卡片與即時縣市切換儀表板 | `public/index.html`, `public/app.js`, `app.py` | ✅ 雙平台（Vercel & Streamlit）皆流暢自適應 |
| **Stage 5** | **台灣地圖視覺化** | 呈現全台氣溫分級色彩地圖、Popup 彈窗、完全移除底圖浮水印 | `public/app.js`, `src/config.py` | ✅ 無任何第三方水印，點擊標籤即時聯動切換地區 |
| **Stage 6** | **生活建議卡片與主題擴充** | 擴充雨傘建議、即時空氣品質、颱風警戒卡片，修復三大歷史缺陷 | `src/lifestyle.py`, `public/app.js`, `public/index.html`, `app.py` | ✅ 27 項測試全數通過，遵循非醫療與正確術語約束 |

---

## 🛠️ 開發歷程與步驟記錄 (Develop Steps By Steps)

以下完整記錄本專案從零到有的開發、重構與擴充歷程：

### Step 1：專案基礎設施與安全規範建立
* 初始化 Git 儲存庫，建立標準目錄結構（`src/`、`tests/`、`data/`）。
* 配置 `.gitignore` 嚴格排除 `.env`、`data/*.db` 與快取目錄，確保機密資訊絕不進入版本控制。
* 撰寫 `.env.example` 與 `requirements.txt`，確保跨環境一致性。

### Step 2：中央氣象署 API 介接與 SSL 相容性處理
* 深入研究 CWA Open Data API，串接未來一週預報端點（優先 `F-D0047-091`，相容 `F-C0032-003`）。
* **關鍵除錯**：解決 Windows 環境下 Python 3.14 存取特定公務機關憑證時因缺少 *Subject Key Identifier* 引發的 `SSLError`，加入自動降級與警告忽略容錯機制。

### Step 3：資料清洗、日期聚合與 SQLite UPSERT 機制實作
* 解析複雜的 JSON 結構（`records -> Locations -> Location -> WeatherElement`）。
* 實作跨時段溫度聚合邏輯：當日多筆時段中，最低溫取最小值，最高溫取最大值。
* 建立 `TemperatureForecasts` 資料表，加入 `UNIQUE(regionName, dataDate)` 約束。
* 使用 `ON CONFLICT(regionName, dataDate) DO UPDATE SET` 實作 **UPSERT**，即使多次重新同步亦不會產生重複髒資料。

### Step 4：Streamlit 互動儀表板與 Folium 地圖建置
* 開發 `app.py`，支援地區下拉選單動態載入。
* 繪製最高溫（紅）與最低溫（藍）雙色 Altair 曲線走勢圖。
* 整合 Folium 互動地圖，依照平均氣溫四段分級（`<20°C` 藍、`20~25°C` 綠、`25~30°C` 橘、`>30°C` 紅）標記台灣各分區。

### Step 5：自動化 CI/CD 與單元測試工程化
* 於 `tests/` 目錄建立 12 項完整的單元測試與端點測試。
* 測試全數採用 Mock 離線設計，不依賴外部網路或真實金鑰，確保 CI 永遠穩定綠燈。
* 撰寫 `.github/workflows/ci.yml`，在每次 push 與 pull request 時自動於 Ubuntu 矩陣環境驗證語法與邏輯。

### Step 6：架構大升級：從 Streamlit 遷移至 Vercel Serverless
* 因 Streamlit 需常駐 WebSocket 伺服器，無法於 Vercel Serverless 平台直接部署。
* 重新架構 Web 應用程式：
  * **前端**：純 Vanilla CSS + HTML5 + 原生 JavaScript，極速載入且無打包負擔。
  * **後端 API**：撰寫 `api/weather.py`，作為 Vercel Python Serverless Function（提供 `/api/weather`）。
  * **部署配置**：配置 `vercel.json` 整合靜態資源與後端無伺服器路由。
  * **本機開發**：撰寫 `dev_server.py`，讓本機在 `http://localhost:3000` 即可預覽 Vercel 完整功能。

### Step 7：視覺改造：注入 The Powerpuff Girls (飛天小女警) 經典主題
* 引入 Google Fonts **Fredoka** 圓潤字體與三主角經典色（花花粉紅 `#FF3377`、泡泡天藍 `#00B4D8`、毛毛青檸綠 `#52B72A`）。
* 打造新野獸派 / 普普漫畫風實心陰影（`box-shadow: 4px 4px 0px #231244`）與 Q 彈懸停微動畫。
* 曲線圖同步升級為 Chart.js 平滑貝茲曲線（花花粉紅 MaxT + 泡泡天藍 MinT）。

### Step 8：細節排版優化：今日氣溫遮擋修復與地圖浮水印徹底移除
* **今日氣溫排版修復**：去除絕對定位的負座標位移，改用內部自然排列的 `.today-tag-wrap` 與 `.today-tag-pill`，使今日預報膠囊不再被邊界切斷，日期與溫度數字（`31.5° / 24.5°`）100% 完整呈現。
* **地圖浮水印移除**：將原本含有 `API KEY REQUIRED` 水印的 CartoDB 瓦片替換為官方純淨 OpenStreetMap，並在 Leaflet 初始化時關閉 `attributionControl` 與加入 CSS 隱藏，整張地圖乾淨無瑕。

### Step 9：雲端部署除錯：Vercel 唯讀環境資料庫映射與函式別名修正
* **唯讀環境問題解決**：Vercel 執行環境（`/var/task`）為唯讀檔案系統，在 `src/config.py` 實作動態映射，自動將資料庫導向至可讀寫的 `/tmp/data.db`。
* **相容性修復**：補齊 `fetch_cwa_forecast = fetch_cwa_json` 與 `parse_forecast_json = parse_weather_json` 函式別名，使線上同步一鍵順暢完成。

### Step 10：缺陷修復與三大歷史問題徹底排除
* **「兩個今日天氣」修復**：在 `public/app.js` 採用精準陣列比對（`findIndex`），在 7 天卡片迴圈中只判定第一個符合今日或第 3 項為 Today，徹底杜絕畫面出現重複標籤。
* **「熱門巡邏點無法點擊」修復**：熱門巡邏點原本包含「臺北市」、「新北市」、「臺中市」、「高雄市」，但在舊版資料庫中僅預置六大區域。修復方案為在 `src/db.py` 預載此四個主要都會區資料，並在 `public/app.js` 與 `api/weather.py` 完善狀態同步與按鈕 active 樣式切換。
* **「最後同步時間錯誤」修復**：清除 `api/weather.py` 中寫死的 `"2026-09-23 11:17:26"` fallback 字串，改由 `SyncMetadata` 表記錄實際同步時間，無紀錄時回傳當前動態時間，不再顯示過期時間。

### Step 11：三大生活建議卡片架構實作與解耦設計
* 建立 `src/lifestyle.py` 純粹業務邏輯模組，將事實數據（Facts）、閾值標準（Thresholds）、文案呈現（Copywriting）完全解耦，易於單獨進行單元測試。
* 支援降雨機率（帶傘決策）、空氣品質（AQI 戴口罩提醒）、颱風警報（防颱物資建議）三大生活卡片，並支援點擊 7 天預報卡片即時切換日期聯動更新。

### Step 12：飛天小女警特派員形象整合
* 將特派員全體合照放置於 `public/powerpuff_girls.png`。
* 於 Vercel Web 端 Header 嵌入圓形普普風頭像，並於 Streamlit 端加入特派員形象卡片。
* 採用 `object-fit: contain` 與彈性邊框，確保在桌面與手機行動裝置上均不變形、不裁切臉部。

---

## ☂️ 三大生活建議卡片規格與決策依據 (Lifestyle Advice Cards)

為提升民眾出門實用性，本氣象站擴充三張直覺的生活建議卡片，並遵循嚴謹的資料與語意規範：

| 卡片名稱 | 核心提問 | 官方資料來源 | 指標與名稱規範 | 判定規則與建議文字 | 限制與免責聲明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **雨量／降雨預報卡** | 今天要帶雨傘嗎？ | 交通部中央氣象署 (CWA) 7天預報端點 | **降雨機率 (PoP)**<br>*(嚴禁稱為「預測雨量」)* | 🌧️ **≥ 60%**：建議帶傘（出門必備雨具）<br>⛅ **30% ~ 59%**：可自行斟酌（備傘為宜）<br>☀️ **< 30%**：無需帶傘（降雨機率低）<br>❓ **無資料**：資料不足 | 僅反映降雨機率（百分比），非累積降雨量（毫米）。介面清楚揭示時間範圍與更新時間。 |
| **空氣品質卡** | 今天要戴口罩嗎？ | 環境部 (MOENV) 空氣品質監測資料 | **空氣品質指標 (AQI)**<br>*(即時測站實測數據)* | 🟢 **0 ~ 50**：良好（日常舒適，正常活動）<br>🟡 **51 ~ 100**：普通（日常防護，敏感族群注意）<br>🟠 **101 ~ 150**：對敏感族群不健康（建議佩戴口罩）<br>🔴 **> 150**：對所有族群不健康（外出建議佩戴口罩） | **嚴格區分「目前觀測值」與未來預報**。測站資料為即時觀測，未來日期標註「無此期間資料」。本分級為一般生活建議，**非個人專屬醫療處方**。 |
| **颱風資訊卡** | 需要提前準備物資嗎？ | 交通部中央氣象署 (CWA) 颱風警報 | **颱風警報發布狀態**<br>*(警報種類、警戒分區)* | 🚨 **警報發布中**：提前準備物資（檢視防颱儲備、固定門窗）<br>🍃 **常態（無警報）**：目前無相關警報（維持常態巡邏）<br>⚠️ **連線異常**：**資料暫時無法取得** | **嚴禁將 API 失敗當作無颱風**！連線異常時明確回報錯誤狀態，並顯示最後更新時間與官方查詢連結。 |

---

## 🐛 重現與修復缺陷清單 (Bug Fixes)

| 缺陷項目 | 原始現象（重現步驟） | 根因分析 (Root Cause) | 修復策略與修改檔案 |
| :--- | :--- | :--- | :--- |
| **兩個今日天氣** | 進入首頁預報清單時，清單內同時出現兩張帶有「Today / 今日天氣」標籤的卡片。 | 舊程式碼在卡片生成迴圈中使用了重複的寬鬆日期比對或同時將固定 index 2 與比對命中者皆標記為 Today。 | 在 `public/app.js` 中先以 `findIndex` 鎖定唯一的主目標索引（`targetTodayIdx`），在渲染迴圈中嚴格以 `idx === targetTodayIdx` 判定，保證全畫面僅有唯一一張今日卡片。 |
| **熱門巡邏點無法點擊** | 點擊上方熱門巡邏點「臺北市」、「新北市」、「臺中市」、「高雄市」藥丸按鈕時，選中樣式未切換或內容未更新。 | 1. 舊資料庫 Mock 資料中僅預置六大區域，無四個直轄市名稱。<br>2. 前端 `selectRegion()` 中比對邏輯在點選相同選區時直接 return，且未正確觸發資料請求。 | 1. 在 `src/db.py` 預載資料中加入四大熱門都會區資料。<br>2. 修改 `public/app.js` 的 `selectRegion()`，即時更新按鈕 `.active` 類別並主動重拉 `/api/weather` 資料。 |
| **最後同步時間錯誤** | 頁面上方資料最後同步時間永遠固定顯示為 `2026-09-23 11:17:26`。 | `api/weather.py` 中寫死了 fallback 時間字串 `"2026-09-23 11:17:26"`，未從資料庫動態讀取。 | 在 `src/db.py` 建立 `SyncMetadata` 表記錄實際同步時間，並於 `api/weather.py` 動態取出；無紀錄時以當前即時時間呈現，徹底移除寫死字串。 |

---

## ☁️ Vercel Serverless 資料庫快取與失效策略 (/tmp Caching Strategy)

在 Vercel Serverless Function 部署環境中，運行時根目錄（`/var/task`）為**唯讀檔案系統 (Read-Only Filesystem)**，無法直接建立或修改 SQLite 檔案。

### 1. 儲存路徑映射
* 本專案透過 `src/config.py` 動態判斷環境：當偵測到 Vercel 雲端環境時，自動將 `DB_PATH` 導向至可讀寫的 `/tmp/data.db`。

### 2. 快取生命週期 (Cache Lifecycle)
* **/tmp 特性**：同一 Serverless 執行個體（Container Instance）在處於暖機（Warm）狀態時，`/tmp` 目錄內的檔案會被保留並重複使用。
* **資料庫初始化**：若執行個體遭遇冷啟動（Cold Start）或換機，系統自動偵測 `/tmp/data.db` 是否存在，若無則呼叫 `init_db()` 自動建表並注入完整種子預報資料。

### 3. 快取更新與失效機制 (Cache Invalidation)
* 透過 `SyncMetadata` 紀錄最後同步時間 `last_sync`。
* 呼叫 `/api/weather?action=sync` 或定時抓取時，資料庫使用 `UPSERT (ON CONFLICT DO UPDATE)` 原子操作更新紀錄。
* 前端設定 5 分鐘自動刷新機制，確保使用者總是看到最新的氣象與警報數據。

---

## 🔑 環境變數設定 (Environment Variables)

於本機開發時請建立 `.env` 檔案；於 Vercel 部署時請至 **Project Settings -> Environment Variables** 設定：

| 變數名稱 | 必填 / 選用 | 說明 | 範例 |
| :--- | :---: | :--- | :--- |
| `CWA_API_KEY` | **必填** (生產同步) | 中央氣象署氣象資料開放平臺授權碼，用於存取一週氣溫、降雨機率及颱風警報 | `CWA-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` |
| `MOENV_API_KEY` | 選用 | 環境部空氣品質開放資料授權碼（若無設定，系統自動使用開放觀測端點或高品質種子資料） | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |

*(註：若未填寫 API Key，系統將啟動全功能離線安全展示模式，確保介面與 27 項自動化測試隨時可用)*

---

## 📂 專案檔案目錄結構

```
0923 天氣預測/
├── api/
│   ├── weather.py            # Vercel Serverless Function (/api/weather, 支援生活卡片與動態時間)
│   └── requirements.txt      # Vercel 後端依賴 (requests, pandas, urllib3)
├── public/
│   ├── index.html            # 前端 HTML5 (飛天小女警特派氣象站 + 三大生活卡片 + 特派員形象)
│   ├── style.css             # Vanilla CSS (Neo-Brutalism 普普漫畫風、純淨無浮水印、響應式)
│   ├── app.js                # 前端互動邏輯 (7天卡片切換、生活建議聯動、唯一 Today 標籤)
│   └── powerpuff_girls.png   # 飛天小女警特派員形象圖檔
├── src/
│   ├── __init__.py           # 套件識別檔
│   ├── config.py             # 系統常數、全台座標定義、Vercel /tmp 資料庫路徑映射
│   ├── db.py                 # SQLite 連線、UPSERT 防重、SyncMetadata、空品與颱風資料表
│   ├── fetch_data.py         # CWA API 抓取、PoP 降雨機率解析、MOENV 空品、CWA 颱風警報
│   └── lifestyle.py          # 三大生活建議卡片純商業邏輯（帶傘、口罩、防颱決策模組）
├── tests/
│   ├── __init__.py
│   ├── test_weather_app.py   # 資料庫、API 解析、分色邏輯單元測試 (離線運行)
│   ├── test_vercel_api.py    # Vercel 本機伺服器、靜態資產與 API 端點整合測試
│   └── test_lifestyle_cards.py # 雨傘、口罩、颱風卡片閾值、術語與容錯邏輯單元測試
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions 自動化 CI 工作流程
├── app.py                    # Streamlit 課程作業版 (已整合三大生活建議卡片與小女警形象)
├── dev_server.py             # 本機一鍵開發伺服器 (http://localhost:3000)
├── package.json              # npm 腳本設定檔
├── vercel.json               # Vercel 部署路由設定
├── requirements.txt          # 本機 Python 套件依賴
├── .env.example              # API Key 環境變數範例
├── WORKFLOW.md               # HW10 開發流程檢核報告 (Gate 1 ~ Gate 6)
└── README.md                 # 專案完整說明文件
```

---

## 💻 本機安裝與執行指南

### 1. 安裝環境與套件
建議使用 Python 3.10 以上版本：
```bash
pip install -r requirements.txt
```

### 2. 設定氣象署授權碼（選用）
若欲同步最新氣象資料：
1. 複製範本建立 `.env`：
   ```bash
   cp .env.example .env
   ```
2. 在 `.env` 填入您的 CWA API Key：
   ```env
   CWA_API_KEY=CWA-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```
*(未設定 API Key 時，系統將自動啟動內建示範資料模式，所有功能皆可完整操作)*

### 3. 啟動 Web 應用程式

#### 🌸 方式 A：啟動 Vercel 網頁版（推薦，現代化飛天小女警風格）
```bash
python dev_server.py
```
或使用 npm：
```bash
npm run dev
```
瀏覽器開啟 **[http://localhost:3000](http://localhost:3000)**。

#### 🫧 方式 B：啟動 Streamlit 作業版
```bash
streamlit run app.py
```
瀏覽器開啟 **[http://localhost:8501](http://localhost:8501)**。

---

## 🚢 部署至 Vercel 指引 (Deploy to Vercel)

本專案已完全通過 Vercel 雲端無伺服器規格測試：

1. **推送最新程式碼至 GitHub**：
   ```bash
   git add .
   git commit -m "feat: complete lifestyle cards, bug fixes, and ppg expansion"
   git push origin main
   ```
2. **在 Vercel 匯入專案**：
   * 前往 [Vercel 儀表板](https://vercel.com/)，點擊 **"Add New Project"**。
   * 選擇您的 GitHub Repository `09-23_taiwan_weather_report` 匯入。
3. **設定環境變數**：
   * 在 **Environment Variables** 區塊新增 `CWA_API_KEY`，填入您的中央氣象署授權碼。
4. **點選 "Deploy"**：
   * 系統將在 30 秒內自動建置完成，並提供正式上線網址（例如 `https://09-23-taiwan-weather-report.vercel.app`）！

---

## 🧪 自動化測試驗證

本專案內建完整的離線單元測試與整合測試套件，涵蓋三套測試模組共 **27 項測試**：
```bash
# 執行所有單元測試與端點測試
python -m unittest discover -s tests

# 語法編譯檢查
python -m compileall src api tests app.py dev_server.py
```
**驗證成果**：全數 27 項測試皆通過（Ran 27 tests in 0.166s, OK）：
1. `tests/test_weather_app.py`（8 項）：資料庫初始化、UPSERT 防重、JSON 氣溫剖析、平均溫分色、多時段彙整。
2. `tests/test_lifestyle_cards.py`（12 項）：帶傘建議閾值（60%/30%/無資料）、降雨機率術語驗證（非預測雨量）、AQI 各級口罩建議、非醫療處方警語驗證、測站觀測 vs 未來預報區分、颱風警報狀態、API 異常時之「資料暫時無法取得」容錯。
3. `tests/test_vercel_api.py`（7 項）：靜態資產載入（HTML, CSS, JS, PNG 圖片）、`/api/weather` 端點回應結構、熱門巡邏點切換、生活建議欄位結構完整性。

---

## 💖 致謝、授權與版權聲明

* **氣象資料來源**：[中華民國交通部中央氣象署氣象資料開放平臺](https://opendata.cwa.gov.tw/) (CWA Open Data)
* **空氣品質來源**：[中華民國環境部空氣品質監測網](https://airtw.moenv.gov.tw/) (MOENV Open Data)
* **主題形象與著作權聲明**：
  * 本專案視覺主題與角色形象（花花 Blossom、泡泡 Bubbles、毛毛 Buttercup）之著作權及商標權屬於原版權方 **Cartoon Network / Warner Bros. Discovery** 所有。
  * 本專案僅用於程式設計課程學習、技術研究與非營利成果展示。若欲進行公開商用部署或衍生散佈，請務必替換為具備合法授權或自創之原創視覺資產。
* **軟體程式碼授權**：本專案軟體原始碼採用 [MIT License](LICENSE) 授權釋出。

