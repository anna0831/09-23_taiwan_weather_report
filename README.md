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

## 🎯 五大核心開發階段 (5-Stage Architecture)

本專案依據作業規範與軟體工程最佳實踐，劃分為五大漸進式關卡（Gate 1 ~ Gate 5）：

```
[Stage 1: CWA API Ingestion] ──> [Stage 2: JSON Parsing & ETL]
                                         │
[Stage 5: Map Visualization] <── [Stage 4: Web Dashboard] <── [Stage 3: SQLite Storage]
```

| 階段 | 階段名稱 | 關鍵職責 | 核心產出檔案 | 完成標準 (DoD) |
| :---: | :--- | :--- | :--- | :--- |
| **Stage 1** | **CWA API 資料介接** | 串接氣象署 Open Data API，處理 SSL 憑證相容性，機密金鑰環境隔離 | `src/config.py`, `src/fetch_data.py`, `.env` | ✅ 成功取得 HTTP 200 JSON，API Key 不入庫 |
| **Stage 2** | **JSON 解析與清洗** | 剖析巢狀 JSON，萃取各地區每日 MaxT、MinT，跨時段日期聚合 | `src/fetch_data.py`, `tests/test_weather_app.py` | ✅ 支援全台 22 縣市與分區，清洗為標準 DataFrame |
| **Stage 3** | **SQLite 資料庫儲存** | 設計 `TemperatureForecasts` 表，實作 UPSERT（防重防呆）與參數化查詢 | `src/db.py`, `data/data.db` | ✅ 重複執行時更新不重複，杜絕 SQL Injection |
| **Stage 4** | **互動氣象 Web App** | 打造雙色平滑折線圖、7天預報卡片與即時縣市切換儀表板 | `public/index.html`, `public/app.js`, `app.py` | ✅ 雙平台（Vercel & Streamlit）皆流暢自適應 |
| **Stage 5** | **台灣地圖視覺化** | 呈現全台氣溫分級色彩地圖、Popup 彈窗、完全移除底圖浮水印 | `public/app.js`, `src/config.py` | ✅ 無任何第三方水印，點擊標籤即時聯動切換地區 |

---

## 🛠️ 開發歷程與步驟記錄 (Develop Steps By Steps)

以下完整記錄本專案從零到有的開發與重構歷程：

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

---

## 📂 專案檔案目錄結構

```
0923 天氣預測/
├── api/
│   ├── weather.py            # Vercel Serverless Function (/api/weather)
│   └── requirements.txt      # Vercel 後端依賴 (requests, pandas, urllib3)
├── public/
│   ├── index.html            # 前端 HTML5 (飛天小女警特派氣象站)
│   ├── style.css             # Vanilla CSS (飛天小女警主題、漫畫普普風、無浮水印)
│   └── app.js                # 前端互動邏輯 (Chart.js 平滑曲線、Leaflet 地圖、5分鐘自動更新)
├── src/
│   ├── __init__.py           # 套件識別檔
│   ├── config.py             # 系統常數、全台座標定義、Vercel /tmp 資料庫路徑映射
│   ├── db.py                 # SQLite 連線、UPSERT 防重防呆、參數化查詢
│   └── fetch_data.py         # CWA API 抓取、SSL 相容性處理、歷史回補、一站式同步
├── tests/
│   ├── __init__.py
│   ├── test_weather_app.py   # 資料庫、API 解析、分色邏輯單元測試 (離線運行)
│   └── test_vercel_api.py    # Vercel 本機伺服器與 API 端點整合測試
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions 自動化 CI 工作流程
├── app.py                    # Streamlit 課程作業版 (已修正圖示與飛天小女警主題)
├── dev_server.py             # 本機一鍵開發伺服器 (http://localhost:3000)
├── package.json              # npm 腳本設定檔
├── vercel.json               # Vercel 部署路由設定
├── requirements.txt          # 本機 Python 套件依賴
├── .env.example              # API Key 環境變數範例
├── WORKFLOW.md               # HW10 開發流程檢核報告 (Gate 1 ~ Gate 5)
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
   copy .env.example .env
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
   git commit -m "feat: complete 5-stage weather app with ppg theme"
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

本專案內建完整的離線測試套件：
```bash
# 執行所有單元測試與端點測試
python -m unittest discover -s tests

# 語法編譯檢查
python -m compileall src api tests app.py dev_server.py
```
**驗證成果**：全數 12 項測試皆通過（Ran 12 tests, OK）。

---

## 💖 致謝與授權

* **資料來源**：[中華民國交通部中央氣象署氣象資料開放平臺](https://opendata.cwa.gov.tw/) (CWA Open Data)
* **主題靈感**：Cartoon Network 經典動畫《飛天小女警》(The Powerpuff Girls)
* **軟體授權**：本專案採用 [MIT License](LICENSE) 授權釋出。
