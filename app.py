"""Taiwan Weather Forecast Web App - Modern Glassmorphism Edition.

具備即時自動同步 (Auto Self-Update)、Altair 雙色流暢曲線圖、7天預報動態卡片與 Folium 全台互動地圖。
"""

from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st
import altair as alt
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
    get_metadata,
)
from src.fetch_data import sync_cwa_to_db

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast | 台灣天氣預報",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------
# 1. 自動自我更新機制 (Auto Self-Update Engine)
# -------------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def auto_self_update_data():
    """背景自動同步函式：每 30 分鐘自動檢查 CWA 最新資料並寫入 SQLite。
    
    遵守架構規範：由後端同步至 SQLite，前端一律從 SQLite 查詢。
    """
    if CWA_API_KEY:
        try:
            success, msg, count = sync_cwa_to_db()
            return success, msg
        except Exception as e:
            return False, str(e)
    return False, "未設定 API Key"


def check_and_prepare_db():
    """確保資料庫具備資料；若為空庫則先初始化種子資料。"""
    init_db()
    regions = get_distinct_regions()
    if not regions:
        seed_mock_data()


# 執行初次準備與自動同步
check_and_prepare_db()
if CWA_API_KEY:
    auto_self_update_data()

# 取得最後同步時間
last_sync = get_metadata("last_sync_time", default="即時連線中")

# -------------------------------------------------------------
# 2. 現代化視覺設計 CSS (Modern Glassmorphism & Sleek Aesthetics)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;600;700;800&display=swap');

    /* 全域字體與背景美化 (飛天小女警 The Powerpuff Girls 風格) */
    html, body, [class*="css"] {
        font-family: 'Fredoka', 'Noto Sans TC', sans-serif;
    }
    
    /* 頂部導覽列與標題 */
    .top-hero {
        background: linear-gradient(135deg, #FFE8F2 0%, #E8F7FE 50%, #EDFCEB 100%);
        border: 2.5px solid #231244;
        border-radius: 24px;
        padding: 24px 30px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 4px 4px 0px #231244;
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .hero-icon {
        font-size: 2.4rem;
        display: inline-block;
        -webkit-text-fill-color: initial !important;
        background: none !important;
        line-height: 1;
    }
    
    .hero-text {
        background: linear-gradient(115deg, #FF3377 0%, #00B4D8 50%, #52B72A 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    .hero-desc {
        color: #5B487A;
        font-size: 0.95rem;
        margin-top: 6px;
        font-weight: 600;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #059669;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 9999px;
        gap: 8px;
    }
    
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* 氣溫動態卡片 */
    .weather-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-align: center;
    }
    
    .weather-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    
    .card-day {
        font-size: 0.88rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
    }
    
    .card-date {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-bottom: 8px;
    }
    
    .card-icon {
        font-size: 2rem;
        margin: 6px 0;
    }
    
    .card-temp-range {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
    }
    
    .card-temp-sub {
        font-size: 0.78rem;
        color: #64748B;
        margin-top: 4px;
    }
    
    /* 統計小卡 Glassmorphism */
    .metric-pill {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-val {
        font-size: 1.7rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. 頂部儀表板 Hero 區塊
# -------------------------------------------------------------
st.markdown(f"""
<div class="top-hero">
    <div>
        <div style="display:flex; gap:8px; margin-bottom:8px;">
            <span style="background:#FFE4EE; color:#FF3377; border:1.5px solid #231244; font-size:12px; font-weight:700; padding:3px 10px; border-radius:99px; box-shadow:1.5px 1.5px 0px #231244;">🌸 花花 Blossom</span>
            <span style="background:#E0F7FD; color:#0077B6; border:1.5px solid #231244; font-size:12px; font-weight:700; padding:3px 10px; border-radius:99px; box-shadow:1.5px 1.5px 0px #231244;">🫧 泡泡 Bubbles</span>
            <span style="background:#EAF8E6; color:#2D6A4F; border:1.5px solid #231244; font-size:12px; font-weight:700; padding:3px 10px; border-radius:99px; box-shadow:1.5px 1.5px 0px #231244;">⚡ 毛毛 Buttercup</span>
        </div>
        <h1 class="hero-title"><span class="hero-icon">⛅</span><span class="hero-text">Taiwan Weather Forecast</span></h1>
        <div class="hero-desc">💖 飛天小女警特派氣象站 · 糖、香料與一切美好事物 · 為您擊退壞天氣！✨</div>
    </div>
    <div style="text-align: right;">
        <div class="status-badge">
            <div class="pulse-dot"></div>
            <span>⚡ 活力守護中 (Active)</span>
        </div>
        <div style="font-size: 0.8rem; color: #5B487A; margin-top: 6px; font-weight:600;">最後同步時間：{last_sync}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# 讀取地區清單
regions = get_distinct_regions()
if not regions:
    st.warning("資料庫載入中，請稍候...")
    st.stop()

# -------------------------------------------------------------
# 4. 側邊欄控制與手動更新
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ 系統設定與資料源")
    st.caption("CWA API × SQLite × Streamlit 視覺化")
    
    st.markdown("#### 🔄 自我更新排程 (Self-Update)")
    st.success("✅ 自動同步機制已啟用 (每 30 分鐘自動對齊氣象署最新發布資料)")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("⚡ 強制即時同步", use_container_width=True):
            with st.spinner("正在向氣象署端點發送請求..."):
                auto_self_update_data.clear()
                s, m, c = sync_cwa_to_db()
                if s:
                    st.toast(f"同步成功！已更新 {c} 筆預報", icon="✅")
                    st.rerun()
                else:
                    st.error(f"同步異常：{m}")
    with col_f2:
        if st.button("🌱 重設示範資料", use_container_width=True):
            seed_mock_data()
            st.toast("已重載本週標準示範資料！", icon="🌱")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🎨 溫度配色圖例")
    st.markdown("""
    <div style="font-size:0.85rem; line-height:1.8;">
        <span style="color:#2196F3; font-weight:bold;">● &lt; 20°C</span> 低溫涼爽 (藍色)<br>
        <span style="color:#10B981; font-weight:bold;">● 20 - 25°C</span> 舒適宜人 (綠色)<br>
        <span style="color:#F59E0B; font-weight:bold;">● 25 - 30°C</span> 溫暖微熱 (橘色)<br>
        <span style="color:#EF4444; font-weight:bold;">● &gt; 30°C</span> 炎熱高溫 (紅色)
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. 主導航分頁 (Sleek Tabs)
# -------------------------------------------------------------
tab_forecast, tab_map, tab_analytics = st.tabs([
    "📈 地區一週氣溫趨勢",
    "🗺️ 全台氣溫互動地圖",
    "📊 全台綜合分析明細"
])

# =============================================================
# 分頁 1: 地區一週氣溫預報 (高質感圖表與卡片)
# =============================================================
with tab_forecast:
    c_sel, c_stat1, c_stat2, c_stat3 = st.columns([1.5, 1, 1, 1])
    
    with c_sel:
        # 預設首選地區
        default_idx = 0
        if "中部地區" in regions:
            default_idx = regions.index("中部地區")
        elif "臺中市" in regions:
            default_idx = regions.index("臺中市")
            
        selected_region = st.selectbox(
            "📍 選擇預報地區 (Select Region)",
            options=regions,
            index=default_idx,
            help="選擇要檢視未來一週天氣走勢的分區或縣市",
        )
    
    # 查詢所選地區
    df_reg = get_forecasts_by_region(selected_region)
    
    if df_reg.empty:
        st.info("查無此地區的預報紀錄。")
    else:
        # 計算統計數據
        t_min = df_reg["mint"].min()
        t_max = df_reg["maxt"].max()
        t_avg = round(((df_reg["mint"] + df_reg["maxt"]) / 2).mean(), 1)
        max_delta = round((df_reg["maxt"] - df_reg["mint"]).max(), 1)
        
        with c_stat1:
            st.markdown(f"""
            <div class="metric-pill">
                <div class="metric-label">一週最低溫 (Min)</div>
                <div class="metric-val" style="color:#0284C7;">{t_min}°C</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_stat2:
            st.markdown(f"""
            <div class="metric-pill">
                <div class="metric-label">一週最高溫 (Max)</div>
                <div class="metric-val" style="color:#EF4444;">{t_max}°C</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_stat3:
            st.markdown(f"""
            <div class="metric-pill">
                <div class="metric-label">一週平均氣溫 (Avg)</div>
                <div class="metric-val" style="color:#10B981;">{t_avg}°C</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # --- 7 天預報精美卡片列 ---
        st.markdown("##### 📅 未來一週每日預報預覽")
        cols = st.columns(min(len(df_reg), 7))
        
        weekdays_map = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}
        
        for idx, (_, r) in enumerate(df_reg.head(7).iterrows()):
            d_str = r["dataDate"]
            try:
                dt_obj = datetime.strptime(d_str, "%Y-%m-%d")
                weekday_name = weekdays_map.get(dt_obj.weekday(), "")
                display_date = dt_obj.strftime("%m/%d")
            except Exception:
                weekday_name = "預報"
                display_date = d_str
                
            day_min = r["mint"]
            day_max = r["maxt"]
            day_avg = round((day_min + day_max) / 2, 1)
            
            # 天氣圖示推估
            if day_avg > 30:
                emoji = "☀️"
            elif day_avg > 25:
                emoji = "⛅"
            elif day_avg > 22:
                emoji = "🌤️"
            else:
                emoji = "🌥️"
                
            with cols[idx]:
                st.markdown(f"""
                <div class="weather-card">
                    <div class="card-day">{weekday_name}</div>
                    <div class="card-date">{display_date}</div>
                    <div class="card-icon">{emoji}</div>
                    <div class="card-temp-range">{int(day_max)}° / {int(day_min)}°</div>
                    <div class="card-temp-sub">均溫 {day_avg}°C</div>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # --- Altair 頂級雙色流暢曲線圖 ---
        st.markdown("##### 📊 一週最高溫與最低溫走勢圖 (MaxT / MinT Spline Chart)")
        
        # 繪圖用資料
        melted_df = df_reg.melt(
            id_vars=["dataDate"],
            value_vars=["maxt", "mint"],
            var_name="temp_type",
            value_name="temperature"
        )
        melted_df["指標名稱"] = melted_df["temp_type"].map({"maxt": "最高溫 (MaxT)", "mint": "最低溫 (MinT)"})
        
        # Altair 互動圖表
        base = alt.Chart(melted_df).encode(
            x=alt.X("dataDate:N", title="預報日期", axis=alt.Axis(labelAngle=0, labelFont="Plus Jakarta Sans", labelFontSize=12)),
            y=alt.Y("temperature:Q", title="氣溫 (°C)", scale=alt.Scale(zero=False, padding=20)),
            color=alt.Color("指標名稱:N", scale=alt.Scale(
                domain=["最高溫 (MaxT)", "最低溫 (MinT)"],
                range=["#EF4444", "#0284C7"]
            ), legend=alt.Legend(orient="top", title=None, labelFontSize=12))
        )
        
        lines = base.mark_line(interpolate="monotone", strokeWidth=3.5)
        points = base.mark_circle(size=70, opacity=1).encode(
            tooltip=[
                alt.Tooltip("dataDate:N", title="日期"),
                alt.Tooltip("指標名稱:N", title="項目"),
                alt.Tooltip("temperature:Q", title="溫度 (°C)", format=".1f")
            ]
        )
        
        chart = (lines + points).properties(
            height=320,
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
        # 數據表格
        st.markdown("##### 📋 詳細預報數值表格")
        disp_df = df_reg.copy()
        disp_df["溫差 (°C)"] = (disp_df["maxt"] - disp_df["mint"]).round(1)
        disp_df["平均溫 (°C)"] = ((disp_df["maxt"] + disp_df["mint"]) / 2).round(1)
        disp_df = disp_df.rename(columns={
            "dataDate": "日期",
            "mint": "最低溫 (°C)",
            "maxt": "最高溫 (°C)",
        })
        st.dataframe(
            disp_df[["日期", "最低溫 (°C)", "最高溫 (°C)", "平均溫 (°C)", "溫差 (°C)"]],
            hide_index=True,
            use_container_width=True,
        )

# =============================================================
# 分頁 2: 全台氣溫互動地圖 (Folium Visualizer)
# =============================================================
with tab_map:
    dates_list = get_distinct_dates()
    if not dates_list:
        st.info("尚無可用日期資料。")
    else:
        col_d, col_hint = st.columns([1.5, 2.5])
        with col_d:
            selected_date = st.selectbox(
                "📅 選擇日期顯示地圖標記 (Select Date)",
                options=dates_list,
                index=0,
                key="map_date_sel",
            )
        with col_hint:
            st.markdown(f"""
            <div style="padding-top:24px; color:#64748B; font-size:0.9rem;">
                點擊地圖標記可檢視分區高低溫氣泡視窗；標記顏色即時依據當日平均氣溫判定。
            </div>
            """, unsafe_allow_html=True)
            
        df_for_date = get_forecasts_by_date(selected_date)
        
        map_col, table_col = st.columns([1.7, 1.3])
        
        with map_col:
            # 建立地圖 (移除浮水印)
            m = folium.Map(
                location=[23.75, 120.95],
                zoom_start=7.4,
                tiles="OpenStreetMap",
                control_scale=False,
            )
            m.get_root().header.add_child(folium.Element("<style>.leaflet-control-attribution { display: none !important; }</style>"))

            
            for _, r in df_for_date.iterrows():
                r_name = r["regionName"]
                coord = REGION_COORDINATES.get(r_name)
                
                # 模糊匹配
                if not coord:
                    for k, v in REGION_COORDINATES.items():
                        if k in r_name or r_name in k:
                            coord = v
                            break
                            
                if not coord:
                    continue
                    
                lat = coord["lat"]
                lon = coord["lon"]
                label = coord.get("label", r_name)
                
                d_min = r["mint"]
                d_max = r["maxt"]
                d_avg = round((d_min + d_max) / 2, 1)
                color = get_temp_color(d_avg)
                
                # Popup HTML
                pop_html = f"""
                <div style="font-family:'Plus Jakarta Sans',sans-serif; min-width:140px; padding:4px;">
                    <div style="font-size:15px; font-weight:700; color:#1E3A8A; margin-bottom:4px;">{r_name}</div>
                    <div style="font-size:13px; color:#475569;">最低溫: <b>{d_min}°C</b></div>
                    <div style="font-size:13px; color:#475569;">最高溫: <b>{d_max}°C</b></div>
                    <div style="font-size:13px; color:#059669; margin-top:2px;">平均溫: <b>{d_avg}°C</b></div>
                    <div style="font-size:11px; color:#94A3B8; margin-top:6px; border-top:1px solid #E2E8F0; padding-top:4px;">日期: {selected_date}</div>
                </div>
                """
                
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=14,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.85,
                    popup=folium.Popup(pop_html, max_width=240),
                    tooltip=f"{r_name} ({d_avg}°C)",
                ).add_to(m)
                
                folium.map.Marker(
                    [lat, lon],
                    icon=folium.DivIcon(
                        html=f"""<div style="font-size:11px; font-weight:700; color:#0F172A; text-shadow:0px 0px 4px #FFFFFF; margin-left:16px; margin-top:-8px;">{label} {d_avg}°</div>"""
                    ),
                ).add_to(m)
                
            st_folium(m, width=540, height=480)
            
        with table_col:
            st.markdown(f"##### 📌 {selected_date} 全區即時摘要")
            if not df_for_date.empty:
                t_df = df_for_date.copy()
                t_df["平均溫 (°C)"] = ((t_df["mint"] + t_df["maxt"]) / 2).round(1)
                t_df["狀態標籤"] = t_df["平均溫 (°C)"].apply(
                    lambda x: "🔵 涼爽" if x < 20 else ("🟢 舒適" if x <= 25 else ("🟠 溫暖" if x <= 30 else "🔴 炎熱"))
                )
                t_df = t_df.rename(columns={
                    "regionName": "地區名稱",
                    "mint": "最低溫",
                    "maxt": "最高溫",
                })
                st.dataframe(
                    t_df[["地區名稱", "最低溫", "最高溫", "平均溫 (°C)", "狀態標籤"]],
                    hide_index=True,
                    height=440,
                    use_container_width=True,
                )

# =============================================================
# 分頁 3: 全台綜合分析明細
# =============================================================
with tab_analytics:
    st.markdown("##### 🔍 全台氣象分區完整資料檢視")
    
    # 統計全體數據指標
    all_dates = get_distinct_dates()
    if all_dates:
        latest_d = all_dates[-1]
        all_df = get_forecasts_by_date(latest_d)
        
        if not all_df.empty:
            hot_row = all_df.loc[all_df["maxt"].idxmax()]
            cold_row = all_df.loc[all_df["mint"].idxmin()]
            
            a1, a2, a3 = st.columns(3)
            with a1:
                st.metric("🔥 當日最高溫地區", f"{hot_row['regionName']} ({hot_row['maxt']}°C)")
            with a2:
                st.metric("❄️ 當日最低溫地區", f"{cold_row['regionName']} ({cold_row['mint']}°C)")
            with a3:
                nat_avg = round(((all_df["mint"] + all_df["maxt"]) / 2).mean(), 1)
                st.metric("🌐 當日全台平均氣溫", f"{nat_avg}°C")
                
    st.markdown("---")
    
    all_regions = get_distinct_regions()
    st.caption(f"目前資料庫中涵蓋 {len(all_regions)} 個地區/縣市與 {len(all_dates)} 個預報日期。所有資料皆自 SQLite 資料庫安全查詢。")
    
    # 快速關鍵字查詢
    search_q = st.text_input("輸入關鍵字搜尋地區 (如: 臺北, 中部, 臺南):")
    conn = sqlite3.connect(DB_PATH)
    if search_q:
        q_df = pd.read_sql_query(
            "SELECT regionName as 地區, dataDate as 日期, mint as 最低溫, maxt as 最高溫 FROM TemperatureForecasts WHERE regionName LIKE ? ORDER BY dataDate DESC",
            conn,
            params=(f"%{search_q}%",)
        )
    else:
        q_df = pd.read_sql_query(
            "SELECT regionName as 地區, dataDate as 日期, mint as 最低溫, maxt as 最高溫 FROM TemperatureForecasts ORDER BY dataDate DESC LIMIT 100",
            conn
        )
    conn.close()
    
    st.dataframe(q_df, hide_index=True, use_container_width=True)
