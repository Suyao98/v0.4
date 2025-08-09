# -*- coding: utf-8 -*-
import datetime
from datetime import date, timedelta
import streamlit as st
from geopy.geocoders import Nominatim

# === 注意：st.set_page_config 必须在 Streamlit 相关显示前调用 ===
st.set_page_config(page_title="流年吉凶", layout="centered")

# ========== 基础：干支、甲子表 ==========
tiangan = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
dizhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
GZS_LIST = [tiangan[i%10] + dizhi[i%12] for i in range(60)]

def ganzhi_list():
    return GZS_LIST

# 五行（按天干）
WUXING_OF_GAN = {
    "甲":"木","乙":"木",
    "丙":"火","丁":"火",
    "戊":"土","己":"土",
    "庚":"金","辛":"金",
    "壬":"水","癸":"水"
}
# 五行（按地支）
WUXING_OF_DZ = {
    "子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
    "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"
}

# 五行颜色（你指定的土色与金色）
WUXING_COLOR = {
    "木": "#2e7d32",   # 绿
    "火": "#d32f2f",   # 红
    "土": "#c19a6b",   # 土色（类似沙土色）
    "金": "#ffd700",   # 金黄色（黄金色）
    "水": "#1565c0"    # 蓝
}

# ========== 合/冲 规则 ==========
gan_he = {"甲":"己","己":"甲","乙":"庚","庚":"乙","丙":"辛","辛":"丙","丁":"壬","壬":"丁","戊":"癸","癸":"戊"}
gan_chong = {"甲":"庚","庚":"甲","乙":"辛","辛":"乙","丙":"壬","壬":"丙","丁":"癸","癸":"丁"}
zhi_he = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯","辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
zhi_chong = {dz: dizhi[(i+6)%12] for i, dz in enumerate(dizhi)}

def zhi_next(z): return dizhi[(dizhi.index(z)+1)%12]
def zhi_prev(z): return dizhi[(dizhi.index(z)-1)%12]

def unique_list(seq):
    seen=set(); out=[]
    for s in seq:
        if s not in seen:
            seen.add(s); out.append(s)
    return out

def calc_jixiong(gz):
    """按既定规则计算某柱的 吉/凶 干支（双合进一/双冲退一）"""
    if not gz or len(gz) < 2:
        return {"吉":[], "凶":[]}
    tg, dz = gz[0], gz[1]
    res = {"吉":[], "凶":[]}
    tg_he = gan_he.get(tg, "")
    dz_he = zhi_he.get(dz, "")
    tg_ch = gan_chong.get(tg, "")
    dz_ch = zhi_chong.get(dz, "")
    if tg_he and dz_he:
        shuang_he = tg_he + dz_he
        jin_yi = tg_he + zhi_next(dz_he)
        res["吉"].extend([shuang_he, jin_yi])
    if tg_ch and dz_ch:
        shuang_ch = tg_ch + dz_ch
        tui_yi = tg_ch + zhi_prev(dz_ch)
        res["凶"].extend([shuang_ch, tui_yi])
    return res

def analyze_bazi(year_zhu, month_zhu, day_zhu, time_zhu):
    pillars = [p for p in (year_zhu, month_zhu, day_zhu) if p]
    if time_zhu and str(time_zhu).strip() and str(time_zhu).strip().lower() not in ["不要","不要时","不知道"]:
        pillars.append(time_zhu)
    all_ji=[]; all_xiong=[]
    for p in pillars:
        r = calc_jixiong(p)
        all_ji.extend(r["吉"]); all_xiong.extend(r["凶"])
    return unique_list(all_ji), unique_list(all_xiong)

# ========== 八字推算：锚点日法（改为 1900-02-04 13:51:31） & 月柱/时柱规则 ==========
# 新锚点（含时间）
ANCHOR_DATETIME = datetime.datetime(1900, 2, 4, 13, 51, 31)
# 为了计算 ANCHOR_INDEX（六十甲子序号），用 1984-01-01 (甲午) 作为参考
BASE_REF_DATE = date(1984,1,1)
BASE_REF_INDEX = GZS_LIST.index("甲午")
ANCHOR_INDEX = (BASE_REF_INDEX + (ANCHOR_DATETIME.date() - BASE_REF_DATE).days) % 60

def day_ganzhi_by_anchor(y,m,d,h=None, minute=0):
    """
    用新的 1900 锚点（含时间）按日差计算日柱。
    保持此前规则：若提供小时且小时>=23，则按次日计算（原逻辑）。
    """
    # 构造目标 datetime（含分钟）
    if h is None:
        target_dt = datetime.datetime(y, m, d, 0, 0)
    else:
        target_dt = datetime.datetime(y, m, d, int(h), int(minute or 0))
        # 保持原有规则：23:00及以后属于次日
        if int(h) >= 23:
            target_dt = target_dt + timedelta(days=1)
    # 以天为单位（使用 floor 整天差）
    delta_days = int((target_dt - ANCHOR_DATETIME).total_seconds() // 86400)
    idx = (ANCHOR_INDEX + delta_days) % 60
    return GZS_LIST[idx]

def get_li_chun_datetime(year):
    # 保持原先近似：立春采用 2 月 4 日 00:00 作为分界（与之前代码一致）
    return datetime.datetime(year,2,4,0,0)

def year_ganzhi(year, month, day, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute)
    lichun = get_li_chun_datetime(year)
    adj_year = year if dt >= lichun else year-1
    return GZS_LIST[(adj_year - 1984) % 60], adj_year

JIEQI = [
    (2,4,"寅"), (3,6,"卯"), (4,5,"辰"), (5,6,"巳"), (6,6,"午"),
    (7,7,"未"), (8,7,"申"), (9,7,"酉"), (10,8,"戌"), (11,7,"亥"),
    (12,7,"子"), (1,6,"丑"),
]
def get_month_branch(year, month, day):
    bd = date(year, month, day)
    for i,(m,d,branch) in enumerate(JIEQI):
        dt = date(year if m != 1 else year+1, m, d)
        dt_next = date(year if JIEQI[(i+1)%12][0] != 1 else year+1, JIEQI[(i+1)%12][0], JIEQI[(i+1)%12][1])
        if dt <= bd < dt_next:
            return branch
    return "寅"

def month_stem_by_fihu_dun(year_tg, month_branch):
    if year_tg in ("甲","己"): first = "丙"
    elif year_tg in ("乙","庚"): first = "戊"
    elif year_tg in ("丙","辛"): first = "庚"
    elif year_tg in ("丁","壬"): first = "壬"
    elif year_tg in ("戊","癸"): first = "甲"
    else: first = "丙"
    start_idx = tiangan.index(first)
    offset = (dizhi.index(month_branch) - dizhi.index("寅")) % 12
    tg_idx = (start_idx + offset) % 10
    return tiangan[tg_idx] + month_branch

def get_hour_branch_by_minute(hour, minute):
    if hour is None:
        return None
    tot = int(hour)*60 + int(minute or 0)
    if tot >= 23*60 or tot < 1*60:
        return "子", 0
    intervals = [
        (1*60, 3*60, "丑"),
        (3*60, 5*60, "寅"),
        (5*60, 7*60, "卯"),
        (7*60, 9*60, "辰"),
        (9*60, 11*60, "巳"),
        (11*60, 13*60, "午"),
        (13*60, 15*60, "未"),
        (15*60, 17*60, "申"),
        (17*60, 19*60, "酉"),
        (19*60, 21*60, "戌"),
        (21*60, 23*60, "亥"),
    ]
    for i,(s,e,name) in enumerate(intervals):
        if s <= tot < e:
            return name, i+1
    return "子", 0

def time_ganzhi_by_rule(day_gz, hour, minute):
    if hour is None or hour < 0:
        return "不知道"
    branch, idx = get_hour_branch_by_minute(hour, minute)
    day_gan = day_gz[0]
    if day_gan in ("甲","己"): start = tiangan.index("甲")
    elif day_gan in ("乙","庚"): start = tiangan.index("丙")
    elif day_gan in ("丙","辛"): start = tiangan.index("戊")
    elif day_gan in ("丁","壬"): start = tiangan.index("庚")
    elif day_gan in ("戊","癸"): start = tiangan.index("壬")
    else: start = 0
    tg_idx = (start + idx) % 10
    return tiangan[tg_idx] + branch

def year_ganzhi_map(start=1900, end=2100):
    base = 1984
    return {y: GZS_LIST[(y-base) % 60] for y in range(start, end+1)}

def color_of_gan(gan_ch):
    el = WUXING_OF_GAN.get(gan_ch, "土")
    return WUXING_COLOR.get(el, "#000000")

def color_of_dz(dz_ch):
    el = WUXING_OF_DZ.get(dz_ch, "土")
    return WUXING_COLOR.get(el, "#000000")

def render_four_pillars_two_rows(year_p, month_p, day_p, hour_p):
    """
    四柱拆成两行：上行天干（五行颜色），下行地支（五行颜色）
    """
    pillars = [year_p, month_p, day_p, hour_p]
    pillars = [p if p and len(p) == 2 else "  " for p in pillars]
    tiangan_row = [p[0] for p in pillars]
    dizhi_row = [p[1] for p in pillars]

    html = "<div style='display:flex;justify-content:center;margin-bottom:10px;'>"
    for tg in tiangan_row:
        c = color_of_gan(tg)
        html += f"<div style='width:60px;text-align:center;font-size:32px;font-weight:700;color:{c};margin:0 8px'>{tg}</div>"
    html += "</div>"

    html += "<div style='display:flex;justify-content:center;'>"
    for dz in dizhi_row:
        c = color_of_dz(dz)
        html += f"<div style='width:60px;text-align:center;font-size:32px;font-weight:700;color:{c};margin:0 8px'>{dz}</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def show_jixiong(ji_list, xiong_list, birth_year):
    current_year = datetime.datetime.now().year
    start = birth_year
    end = 2100
    ymap = year_ganzhi_map(start, end)

    order_key = lambda x: GZS_LIST.index(x) if x in GZS_LIST else 999

    st.subheader("🎉 吉年")
    if not ji_list:
        st.info("无吉年（按当前规则）")
    else:
        for gz in sorted(ji_list, key=order_key):
            years = [y for y,g in ymap.items() if g == gz]
            if not years: continue
            years.sort()
            past = [y for y in years if y <= current_year]
            future = [y for y in years if y > current_year]
            parts = []
            for y in past:
                parts.append(f"{y}年")
            for y in future:
                parts.append(f"<b>{y}年★</b>")
            st.markdown(
                f"<div style='padding:8px;border-left:4px solid #2e7d32;background:#f1fbf1;border-radius:6px;margin-bottom:6px;color:#145214'><b>{gz}</b>: {'，'.join(parts)}</div>",
                unsafe_allow_html=True
            )

    st.subheader("☠️ 凶年")
    if not xiong_list:
        st.info("无凶年（按当前规则）")
    else:
        for gz in sorted(xiong_list, key=order_key):
            years = [y for y,g in ymap.items() if g == gz]
            if not years: continue
            years.sort()
            past = [y for y in years if y <= current_year]
            future = [y for y in years if y > current_year]
            parts = []
            for y in past:
                parts.append(f"{y}年")
            for y in future:
                parts.append(f"<b>{y}年★</b>")
            st.markdown(
                f"<div style='padding:8px;border-left:4px solid #8b0000;background:#fff6f6;border-radius:6px;margin-bottom:6px;color:#5b0000'><b>{gz}</b>: {'，'.join(parts)}</div>",
                unsafe_allow_html=True
            )

# === 真太阳时辅助函数 ===
def geocode_place(place_name):
    try:
        geolocator = Nominatim(user_agent="bazi_streamlit_app")
        loc = geolocator.geocode(place_name, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
        else:
            return None, None
    except Exception as e:
        return None, None

def apply_true_solar_correction(year, month, day, hour, minute, lon):
    """
    简化真太阳时修正：
    标准经度取 lon 对应时区中心经度 = round(lon/15) * 15
    修正分钟 = 4 * (lon - 标准经度)
    返回修正后的 (year, month, day, hour, minute)
    （注意：这是简化处理，不考虑夏令时或行政时区例外）
    """
    try:
        base_dt = datetime.datetime(year, month, day, int(hour), int(minute))
    except Exception:
        base_dt = datetime.datetime(year, month, day, 0, 0)
    tz_hours = int(round(lon / 15.0))
    std_meridian = tz_hours * 15.0
    minutes_offset = 4.0 * (lon - std_meridian)  # 可以正负
    corrected_dt = base_dt + timedelta(minutes=minutes_offset)
    return corrected_dt.year, corrected_dt.month, corrected_dt.day, corrected_dt.hour, corrected_dt.minute

# ========== Streamlit 页面 ==========
st.title("流年吉凶")

mode = st.radio("", ["阳历生日", "直接输入四柱八字"])

if mode == "阳历生日":
    col1, col2 = st.columns([2,1])
    with col1:
        byear = st.number_input("出生年", min_value=1900, max_value=2100, value=1990, step=1)
        bmonth = st.number_input("出生月（数字）", min_value=1, max_value=12, value=5, step=1)
        bday = st.number_input("出生日", min_value=1, max_value=31, value=18, step=1)
    with col2:
        unknown_time = st.checkbox("时辰未知（跳过时柱）", value=False)
        # 真太阳时开关与地名输入
        use_true_solar = st.checkbox("使用真太阳时换算（按出生地经纬度，需网络）", value=False)
        if use_true_solar:
            place_name = st.text_input("出生地（地名，例如：Beijing, China）", value="")

        if unknown_time:
            bhour = -1
            bmin = 0
        else:
            bhour = st.number_input("小时（0-23）", min_value=0, max_value=23, value=8, step=1)
            bmin = st.number_input("分钟（0-59）", min_value=0, max_value=59, value=0, step=1)

    if st.button("查询吉凶"):
        hour_val = None if bhour == -1 else int(bhour)
        min_val = None if bhour == -1 else int(bmin)
        try:
            # 如果启用真太阳时并提供出生地且提供时分，则尝试 geocode 并修正时间
            calc_year = byear; calc_month = bmonth; calc_day = bday
            calc_hour = hour_val; calc_min = min_val
            if use_true_solar and hour_val is not None and place_name.strip():
                lat, lon = geocode_place(place_name.strip())
                if lat is None:
                    st.warning("无法解析该地名的经纬度，已使用原始出生时间进行推算。")
                else:
                    # 应用真太阳时修正（简化）
                    ny, nm, nd, nh, nmin = apply_true_solar_correction(byear, bmonth, bday, hour_val, min_val, lon)
                    st.info(f"地点解析：经度 {lon:.4f}，纬度 {lat:.4f}；真太阳时（近似）为 {ny}-{nm:02d}-{nd:02d} {nh:02d}:{nmin:02d}")
                    calc_year, calc_month, calc_day, calc_hour, calc_min = ny, nm, nd, nh, nmin

            # 主计算（使用可能被修正的 calc_* 值）
            year_p, adj_year = year_ganzhi(calc_year, calc_month, calc_day, calc_hour or 0, calc_min or 0)
            day_p = day_ganzhi_by_anchor(calc_year, calc_month, calc_day, calc_hour, calc_min)
            mb = get_month_branch(calc_year, calc_month, calc_day)
            month_p = month_stem_by_fihu_dun(year_p[0], mb)
            hour_p = "不知道" if (calc_hour is None) else time_ganzhi_by_rule(day_p, calc_hour, calc_min or 0)

            st.markdown("## 四柱八字")
            render_four_pillars_two_rows(year_p, month_p, day_p, hour_p)

            ji, xiong = analyze_bazi(year_p, month_p, day_p, hour_p)
            st.markdown("---")
            show_jixiong(ji, xiong, byear)
        except Exception as e:
            st.error(f"计算出错：{e}")

else:
    st.markdown("请直接输入四柱八字（例如：庚午、辛巳），时柱可填“不知道”以跳过。")
    nianzhu = st.text_input("年柱", max_chars=2)
    yuezhu = st.text_input("月柱", max_chars=2)
    rizhu = st.text_input("日柱", max_chars=2)
    shizhu = st.text_input("时柱", max_chars=2)
    start_year = st.number_input("用于列出吉凶年份的起始年（例如出生年）", min_value=1600, max_value=2100, value=1990, step=1)

    if st.button("分析吉凶"):
        try:
            ji, xiong = analyze_bazi(nianzhu.strip(), yuezhu.strip(), rizhu.strip(), shizhu.strip())
            st.markdown("## 你输入的四柱")
            render_four_pillars_two_rows(nianzhu.strip() or "  ", yuezhu.strip() or "  ", rizhu.strip() or "  ", shizhu.strip() or "  ")
            st.markdown("---")
            show_jixiong(ji, xiong, int(start_year))
        except Exception as e:
            st.error(f"计算出错：{e}")
