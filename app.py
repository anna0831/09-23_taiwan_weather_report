"""Taiwan Weather Forecast Web App 主程式。

整合 CWA API、SQLite、SQL 查詢、Streamlit 圖表與 Folium 台灣天氣地圖。
對應課程圖片之 Step 11 ~ 19。
"""

import sqlite3
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from src.config import (
    CWA_API_KEY,
    REGION_COORDINATES,
    get_temp_color,
    DB_PATH,
)
from src.db import (
    init_db,
    get_distinct_regions,
    get_forecasts_by_region,
    get_distinct_dates,
    get_forecasts_by_date,
    seed_mock_data,
)
from src.fetch_data import sync_cwa_to_db

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自訂 CSS 提升介面質感
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .legend-box {
        display: inline-block;
        width: 14px;
        height: 14px;
        margin-right: 6px;
        border-radius: 3px;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)


def check_and_prepare_db():
    """確保資料庫存在；若為空則自動載入示範資料。"""
    init_db()
    regions = get_distinct_regions()
    if not regions:
        seed_mock_data()


# 初始資料庫準備
check_and_prepare_db()

# --- 側邊欄控制與資料管理 ---
with st.sidebar:
    st.header("⚙️ 系統設定與資料來源")
    
    st.markdown("### 🔑 CWA API 設定")
    if CWA_API_KEY:
        st.success("已讀取到 CWA_API_KEY 環境變數")
    else:
        st.warning("尚未設定 CWA_API_KEY，目前運行於示範資料模式。")
        st.info("如需抓取即時資料，請在 `.env` 設定 `CWA_API_KEY`。")

    # 手動輸入 API Key 測試 (可選)
    manual_key = st.text_input("或在此輸入 CWA API Key 進行連線：", type="password")
    effective_key = manual_key.strip() if manual_key.strip() else CWA_API_KEY

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 同步 CWA 資料", use_container_width=True):
            if not effective_key:
                st.error("請先提供 CWA API Key！")
            else:
                with st.spinner("正在向氣象署發送請求並更新資料庫..."):
                    success, msg, count = sync_cwa_to_db(api_key=effective_key)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"同步失敗：{msg}")

    with col_btn2:
        if st.button("🌱 載入示範資料", use_container_width=True):
            count = seed_mock_data()
            st.success(f"已重設並載入 {count} 筆課程示範資料！")
            st.rerun()

    st.markdown("---")
    st.markdown("""
    **專案特色**
    - 串接中央氣象署 CWA API
    - SQLite 參數化查詢與防重複寫入
    - 一週最高/最低溫折線圖
    - Folium 互動地圖與氣溫分色
    """)

# --- 主頁面標題 ---
st.markdown('<div class="main-header">⛅ Taiwan Weather Forecast</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">從氣象資料到互動式天氣預報應用 (CWA API × SQLite × Streamlit × Folium)</div>', unsafe_allow_html=True)

# 讀取可用地區清單 (圖二 Step 10 & 13)
regions = get_distinct_regions()

if not regions:
    st.warning("資料庫中目前尚無資料，請點擊側邊欄的「載入示範資料」或「同步 CWA 資料」。")
    st.stop()

# --- 分頁或區塊展示 ---
tab1, tab2 = st.tabs(["📈 地區一週氣溫預報", "🗺️ 全台天氣互動地圖"])

# ==========================================
# 分頁 1: 地區一週氣溫預報 (圖二 Step 13, 14, 15, 16)
# ==========================================
with tab1:
    st.subheader("選地區看氣溫預報")
    
    col_select, col_info = st.columns([1, 2])
    with col_select:
        # 下拉選單選擇地區 (Step 13)
        default_index = 0
        if "中部地區" in regions:
            default_index = regions.index("中部地區")
        elif "北部地區" in regions:
            default_index = regions.index("北部地區")

        selected_region = st.selectbox(
            "Select Region (選擇地區)",
            options=regions,
            index=default_index,
            key="region_select",
        )

    # 查詢所選地區資料 (Step 10 & 12: 參數化 SQL 查詢)
    df_region = get_forecasts_by_region(selected_region)

    if df_region.empty:
        st.info(f"查無 {selected_region} 的預報資料。")
    else:
        # 統計資訊小卡
        min_temp_all = df_region["mint"].min()
        max_temp_all = df_region["maxt"].max()
        avg_temp_all = round(((df_region["mint"] + df_region["maxt"]) / 2).mean(), 1)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("一週最低溫 (Min)", f"{min_temp_all} °C")
        m_col2.metric("一週最高溫 (Max)", f"{max_temp_all} °C")
        m_col3.metric("一週平均溫 (Avg)", f"{avg_temp_all} °C")

        st.markdown("#### 一週最高與最低氣溫折線圖")
        # 繪製折線圖 (Step 14: MaxT 紅線, MinT 藍線)
        # 整理成適合 Streamlit 圖表的結構
        chart_df = df_region.copy()
        chart_df = chart_df.rename(columns={"dataDate": "Date", "mint": "MinT", "maxt": "MaxT"})
        chart_df = chart_df.set_index("Date")[["MaxT", "MinT"]]

        # 使用 Streamlit 內建折線圖，設定紅與藍兩色
        st.line_chart(
            chart_df,
            color=["#EF4444", "#3B82F6"],  # MaxT 紅色, MinT 藍色
            use_container_width=True,
        )

        st.markdown("#### 清楚呈現一週預報資料 (Step 15)")
        # 顯示資料表格 (Step 15)
        display_df = df_region.copy()
        display_df = display_df.rename(columns={
            "dataDate": "Date",
            "mint": "MinT (°C)",
            "maxt": "MaxT (°C)",
        })
        display_df["溫差 (°C)"] = (display_df["MaxT (°C)"] - display_df["MinT (°C)"]).round(1)
        st.dataframe(
            display_df[["Date", "MinT (°C)", "MaxT (°C)", "溫差 (°C)"]],
            hide_index=True,
            use_container_width=True,
        )

# ==========================================
# 分頁 2: 全台天氣互動地圖 (圖二 Step 17, 18, 19)
# ==========================================
with tab2:
    st.subheader("Taiwan Weather Dashboard")
    
    # 取得可用日期清單 (Step 18)
    available_dates = get_distinct_dates()
    if not available_dates:
        st.info("尚無日期預報資料。")
    else:
        col_date, col_legend = st.columns([1, 2])
        with col_date:
            selected_date = st.selectbox(
                "Select Date (選擇日期)",
                options=available_dates,
                index=0,
                key="date_select",
            )
        with col_legend:
            st.markdown("""
            **平均溫度顏色標記 (Step 17)：**  
            <span style="color:#2196F3; font-weight:bold;">● &lt; 20°C (藍)</span> &nbsp;&nbsp;|&nbsp;&nbsp;
            <span style="color:#4CAF50; font-weight:bold;">● 20 - 25°C (綠)</span> &nbsp;&nbsp;|&nbsp;&nbsp;
            <span style="color:#FF9800; font-weight:bold;">● 25 - 30°C (橘)</span> &nbsp;&nbsp;|&nbsp;&nbsp;
            <span style="color:#F44336; font-weight:bold;">● &gt; 30°C (紅)</span>
            """, unsafe_allow_html=True)

        # 查詢所選日期的全台預報資料 (Step 10 & 18)
        df_date = get_forecasts_by_date(selected_date)

        col_map, col_table = st.columns([3, 2])

        with col_map:
            # 初始化 Folium 地圖，台灣中心點約 23.7, 120.9
            m = folium.Map(
                location=[23.7, 120.9],
                zoom_start=7.3,
                tiles="OpenStreetMap",
            )

            # 在地圖上為每個地區建立標記 (Step 17 & 18)
            for _, row in df_date.iterrows():
                r_name = row["regionName"]
                coord_info = REGION_COORDINATES.get(r_name)
                
                # 若找不到精準匹配，嘗試模糊比對開頭名稱
                if not coord_info:
                    for k, v in REGION_COORDINATES.items():
                        if k in r_name or r_name in k:
                            coord_info = v
                            break

                if not coord_info:
                    continue

                lat = coord_info["lat"]
                lon = coord_info["lon"]
                label = coord_info.get("label", r_name)

                mint = row["mint"]
                maxt = row["maxt"]
                avg_t = round((mint + maxt) / 2.0, 1)
                color_name = get_temp_color(avg_t)

                # 點擊標記 Popup (Step 18: 中部地區 Min: 20°C Max: 30°)
                popup_html = f"""
                <div style="font-family:sans-serif; min-width:130px;">
                    <h4 style="margin:0 0 6px 0; color:#1E3A8A;">{r_name}</h4>
                    <p style="margin:2px 0;"><b>最低溫:</b> {mint} °C</p>
                    <p style="margin:2px 0;"><b>最高溫:</b> {maxt} °C</p>
                    <p style="margin:2px 0;"><b>平均溫:</b> {avg_t} °C</p>
                    <p style="margin:4px 0 0 0; font-size:12px; color:#6B7280;">日期: {selected_date}</p>
                </div>
                """

                # 圓形標記配合顏色
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=16,
                    color=color_name,
                    fill=True,
                    fill_color=color_name,
                    fill_opacity=0.85,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{r_name} (平均 {avg_t}°C)",
                ).add_to(m)

                # 在標記旁附加文字標籤
                folium.map.Marker(
                    [lat, lon],
                    icon=folium.DivIcon(
                        html=f"""<div style="font-size:11px; font-weight:bold; color:#1F2937; text-shadow:1px 1px 2px white; margin-left:18px; margin-top:-10px;">{label}<br>{avg_t}°C</div>"""
                    ),
                ).add_to(m)

            st_folium(m, width=580, height=450)

        with col_table:
            st.markdown(f"#### {selected_date} 各地區氣溫表")
            if not df_date.empty:
                table_display = df_date.copy()
                table_display["avg_temp"] = ((table_display["mint"] + table_display["maxt"]) / 2).round(1)
                table_display = table_display.rename(columns={
                    "regionName": "地區",
                    "mint": "最低溫 (°C)",
                    "maxt": "最高溫 (°C)",
                    "avg_temp": "平均溫 (°C)",
                })
                st.dataframe(
                    table_display[["地區", "最低溫 (°C)", "最高溫 (°C)", "平均溫 (°C)"]],
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("該日期無預報資料。")
