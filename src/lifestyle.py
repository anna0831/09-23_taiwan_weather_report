"""生活建議卡片邏輯模組 (Lifestyle Advice Logic)。

包含三項生活建議判斷規則：
1. 雨量／降雨預報：「今天要帶雨傘嗎？」
2. 空氣品質：「今天要戴口罩嗎？」
3. 颱風資訊：「需要提前準備物資嗎？」

原始數值事實 (Data Facts)、判斷門檻 (Thresholds) 與輸出文字 (Output Text) 分離實作，
提供精確且易於單元測試的純函式。
"""

from typing import Dict, Any, Optional


def evaluate_umbrella_advice(
    pop: Optional[float],
    date_str: str = "",
    time_range: str = "全日",
    region_name: str = ""
) -> Dict[str, Any]:
    """評估帶傘生活建議。
    
    規則：
    - pop is None 或無法取得: 資料不足 / 無此期間資料
    - pop >= 60%: 建議帶傘 (降雨機率高)
    - 30% <= pop < 60%: 可自行斟酌 (可能降雨，備傘為宜)
    - pop < 30%: 無需帶傘 (降雨機率低)
    
    注意：資料僅有降雨機率時，嚴禁稱為「預測雨量」。
    """
    rule_explanation = "依據氣象署預報降雨機率 (PoP)：≥60% 建議帶傘、30%~59% 可自行斟酌、<30% 無需帶傘。"
    
    if pop is None or pop < 0:
        return {
            "status": "資料不足",
            "badge": "無此期間資料",
            "level": "unknown",
            "pop_value": None,
            "metric_name": "降雨機率 (PoP)",
            "date": date_str,
            "time_range": time_range,
            "region": region_name,
            "advice": "暫無該日降雨機率預報資料，出門前請留意最新天候變化。",
            "rule_explanation": rule_explanation,
            "source": "交通部中央氣象署 (CWA)"
        }
    
    pop_val = round(float(pop), 1)
    
    if pop_val >= 60.0:
        return {
            "status": "建議帶傘",
            "badge": "攜帶雨具",
            "level": "high",
            "pop_value": pop_val,
            "metric_name": "降雨機率 (PoP)",
            "date": date_str,
            "time_range": time_range,
            "region": region_name,
            "advice": f"降雨機率達 {int(pop_val)}%（≥60%），出門請務必攜帶雨傘或雨衣，防範降雨！",
            "rule_explanation": rule_explanation,
            "source": "交通部中央氣象署 (CWA)"
        }
    elif pop_val >= 30.0:
        return {
            "status": "可自行斟酌",
            "badge": "備傘為宜",
            "level": "medium",
            "pop_value": pop_val,
            "metric_name": "降雨機率 (PoP)",
            "date": date_str,
            "time_range": time_range,
            "region": region_name,
            "advice": f"降雨機率為 {int(pop_val)}%（30%~59%），天氣可能較為不穩定，建議隨身攜帶折疊傘備用。",
            "rule_explanation": rule_explanation,
            "source": "交通部中央氣象署 (CWA)"
        }
    else:
        return {
            "status": "無需帶傘",
            "badge": "安心出門",
            "level": "low",
            "pop_value": pop_val,
            "metric_name": "降雨機率 (PoP)",
            "date": date_str,
            "time_range": time_range,
            "region": region_name,
            "advice": f"降雨機率僅 {int(pop_val)}%（<30%），天氣相對穩定，可安心輕裝出門！",
            "rule_explanation": rule_explanation,
            "source": "交通部中央氣象署 (CWA)"
        }


def evaluate_air_quality_advice(
    aqi: Optional[float],
    site_name: str = "",
    obs_time: str = "",
    is_forecast: bool = False,
    region_name: str = ""
) -> Dict[str, Any]:
    """評估空氣品質與口罩生活建議。
    
    規則：
    - aqi is None: 資料暫時無法取得
    - aqi <= 50: 良好 (無需特別佩戴口罩)
    - 51 <= aqi <= 100: 普通 (普通良好，敏感族群可評估佩戴)
    - 101 <= aqi <= 150: 對敏感族群不健康 (建議敏感族群佩戴口罩)
    - 151 <= aqi <= 200: 對所有族群不健康 (建議外出佩戴口罩防護)
    - aqi > 200: 非常不健康 / 危害 (應佩戴口罩並減少戶外停留)
    
    誠實原則：明確標示「目前觀測值」或「未來預報」；此指標為一般生活提醒，非個人醫療診斷建議。
    """
    guideline = "本分級提供一般生活與戶外活動參考，非個人專屬醫療處方建議；呼吸道疾病患者請依醫師指示採取防護。"
    data_type_label = "未來預報" if is_forecast else "目前觀測值"
    
    if aqi is None or aqi < 0:
        return {
            "status": "資料暫時無法取得",
            "badge": "無此期間資料",
            "level": "unknown",
            "aqi_value": None,
            "site_name": site_name or region_name or "未指定測站",
            "obs_time": obs_time or "無觀測時間",
            "data_type": data_type_label,
            "region": region_name,
            "advice": "暫無該區域之空氣品質指標資料，敬請稍後重新整理查看。",
            "guideline": guideline,
            "source": "環境部 (MOENV) 空氣品質監測網"
        }
    
    aqi_val = round(float(aqi), 1)
    
    if aqi_val <= 50:
        return {
            "status": "良好",
            "badge": "日常舒適",
            "level": "good",
            "aqi_value": aqi_val,
            "site_name": site_name or region_name or "鄰近測站",
            "obs_time": obs_time,
            "data_type": data_type_label,
            "region": region_name,
            "advice": f"AQI 為 {int(aqi_val)}，空氣品質良好，所有族群皆可正常戶外活動，無需特別佩戴口罩。",
            "guideline": guideline,
            "source": "環境部 (MOENV) 空氣品質監測網"
        }
    elif aqi_val <= 100:
        return {
            "status": "普通",
            "badge": "自主評估",
            "level": "moderate",
            "aqi_value": aqi_val,
            "site_name": site_name or region_name or "鄰近測站",
            "obs_time": obs_time,
            "data_type": data_type_label,
            "region": region_name,
            "advice": f"AQI 為 {int(aqi_val)}，空氣品質普通，一般民眾可正常活動，極敏感族群可視個人狀況評估是否佩戴口罩。",
            "guideline": guideline,
            "source": "環境部 (MOENV) 空氣品質監測網"
        }
    elif aqi_val <= 150:
        return {
            "status": "對敏感族群不健康",
            "badge": "敏感族群佩戴",
            "level": "orange",
            "aqi_value": aqi_val,
            "site_name": site_name or region_name or "鄰近測站",
            "obs_time": obs_time,
            "data_type": data_type_label,
            "region": region_name,
            "advice": f"AQI 為 {int(aqi_val)}，對敏感族群不健康，心血管或呼吸道敏感族群外出建議佩戴口罩，並減少戶外長時間劇烈運動。",
            "guideline": guideline,
            "source": "環境部 (MOENV) 空氣品質監測網"
        }
    elif aqi_val <= 200:
        return {
            "status": "對所有族群不健康",
            "badge": "建議外出佩戴",
            "level": "unhealthy",
            "aqi_value": aqi_val,
            "site_name": site_name or region_name or "鄰近測站",
            "obs_time": obs_time,
            "data_type": data_type_label,
            "region": region_name,
            "advice": f"AQI 為 {int(aqi_val)}，對所有族群不健康，外出建議佩戴口罩防護，敏感族群應留在室內並減少體力消耗。",
            "guideline": guideline,
            "source": "環境部 (MOENV) 空氣品質監測網"
        }
    else:
        return {
            "status": "非常不健康 / 危害",
            "badge": "嚴加防護",
            "level": "hazardous",
            "aqi_value": aqi_val,
            "site_name": site_name or region_name or "鄰近測站",
            "obs_time": obs_time,
            "data_type": data_type_label,
            "region": region_name,
            "advice": f"AQI 高達 {int(aqi_val)}，空氣品質達危害等級，外出應佩戴防護口罩，所有民眾應避免戶外活動並留在室內關閉門窗。",
            "guideline": guideline,
            "source": "環境部 (MOENV) 空氣品質監測網"
        }


def evaluate_typhoon_advice(
    typhoon_data: Optional[Dict[str, Any]],
    region_name: str = ""
) -> Dict[str, Any]:
    """評估颱風資訊與物資準備建議。
    
    規則：
    - typhoon_data is None 或 API 錯誤: 資料暫時無法取得 (絕不可將錯誤當作無颱風！)
    - hasWarning == 0: 目前無相關警報 (正常狀態，無發布警報)
    - hasWarning == 1 且包含陸上警報: 陸上颱風警報 (提醒檢視防颱物資、門窗與排水)
    - hasWarning == 1 且僅海上警報: 海上颱風警報 (海上風浪大，避免海邊山區活動)
    
    嚴格標準：只有資料明確支持時才提示準備，不根據一般雨量自行宣稱有颱風，亦不指定特定超市賣場。
    """
    source_label = "交通部中央氣象署 (CWA)"
    
    if typhoon_data is None or typhoon_data.get("is_error"):
        return {
            "status": "資料暫時無法取得",
            "badge": "連線異常",
            "level": "unknown",
            "is_warning_active": False,
            "is_error": True,
            "typhoon_name": None,
            "warning_type": None,
            "issue_time": None,
            "affected_areas": None,
            "region": region_name,
            "advice": "目前無法連線取得最新官方颱風警報資料，請稍後重新整理，或直接參閱中央氣象署官方網站最新公告。",
            "source": source_label
        }
    
    has_warning = bool(typhoon_data.get("hasWarning", 0))
    issue_time = typhoon_data.get("issueTime", "即時查驗")
    
    if not has_warning:
        return {
            "status": "目前無相關警報",
            "badge": "常態巡邏",
            "level": "calm",
            "is_warning_active": False,
            "is_error": False,
            "typhoon_name": "無",
            "warning_type": "無警報發布",
            "issue_time": issue_time,
            "affected_areas": "無",
            "region": region_name,
            "advice": "中央氣象署目前未對台灣陸地或海域發布颱風警報，特派氣象站維持常態守護，無須提前恐慌囤積物資。",
            "source": source_label
        }
    
    typhoon_name = typhoon_data.get("typhoonName", "熱帶系統")
    warning_type = typhoon_data.get("warningType", "颱風警報")
    affected_areas = typhoon_data.get("affectedAreas", "全台警戒區域")
    headline = typhoon_data.get("headline", "")
    
    is_land_warning = "陸上" in warning_type
    
    if is_land_warning:
        return {
            "status": f"陸上颱風警報發布中 ({typhoon_name})",
            "badge": "警戒防颱",
            "level": "danger",
            "is_warning_active": True,
            "is_error": False,
            "typhoon_name": typhoon_name,
            "warning_type": warning_type,
            "issue_time": issue_time,
            "affected_areas": affected_areas,
            "headline": headline,
            "region": region_name,
            "advice": f"氣象署已發布【{typhoon_name}】{warning_type}！警戒區域（{affected_areas}）請提前加固門窗、清理陽台排水孔，並檢視手電筒與備妥 2 至 3 日份飲用水與基本家庭常備物資，隨時注意官方最新動態。",
            "source": source_label
        }
    else:
        return {
            "status": f"海上颱風警報發布中 ({typhoon_name})",
            "badge": "海上警戒",
            "level": "warning",
            "is_warning_active": True,
            "is_error": False,
            "typhoon_name": typhoon_name,
            "warning_type": warning_type,
            "issue_time": issue_time,
            "affected_areas": affected_areas,
            "headline": headline,
            "region": region_name,
            "advice": f"氣象署已發布【{typhoon_name}】{warning_type}，台灣鄰近海域風浪顯著轉強，海邊作業船隻請嚴加戒備；請民眾切勿前往海邊觀浪或從事水上活動。",
            "source": source_label
        }
