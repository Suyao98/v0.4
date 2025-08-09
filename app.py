# -*- coding: utf-8 -*-
import datetime
from datetime import date, timedelta
import streamlit as st
from geopy.geocoders import Nominatim

# 可选支持 sxtwl（本地已安装则启用）
try:
    import sxtwl  # 许多环境下为 sxtwl 或 sxtwl_py
    HAS_SXTWL = True
except Exception:
    try:
        import sxtwl_py as sxtwl
        HAS_SXTWL = True
    except Exception:
        HAS_SXTWL = False

# Streamlit page config (must be near top)
st.set_page_config(page_title="流年吉凶", layout="centered")

# -----------------------
# 基本干支数据、五行、颜色
# -----------------------
tiangan = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
dizhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
GZS_LIST = [tiangan[i%10] + dizhi[i%12] for i in range(60)]

WUXING_OF_GAN = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
WUXING_OF_DZ = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}

WUXING_COLOR = {
    "木": "#2e7d32",
    "火": "#d32f2f",
    "土": "#c19a6b",   # 土色
    "金": "#ffd700",   # 金色
    "水": "#1565c0"
}

# -----------------------
# 合/冲规则（你的规则）
# -----------------------
gan_he = {"甲":"己","己":"甲","乙":"庚","庚":"乙","丙":"辛","辛":"丙","丁":"壬","壬":"丁","戊":"癸","癸":"戊"}
gan_chong = {"甲":"庚","庚":"甲","乙":"辛","辛":"乙","丙":"壬","壬":"丙","丁":"癸","癸":"丁"}
zhi_he = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯","辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
dizhi_list = dizhi[:]  # alias
zhi_chong = {dz: dizhi_list[(i+6)%12] for i,dz in enumerate(dizhi_list)}

def zhi_next(z): return dizhi_list[(dizhi_list.index(z)+1)%12]
def zhi_prev(z): return dizhi_list[(dizhi_list.index(z)-1)%12]

def unique_list(seq):
    seen=set(); out=[]
    for s in seq:
        if s not in seen:
            seen.add(s); out.append(s)
    return out

def calc_jixiong(gz):
    """按双合进一 / 双冲退一计算吉凶干支"""
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

# -----------------------
# 锚点（按你最新要求）
# ANCHOR_DATETIME = 1900-02-04 13:51:31
# 年柱：庚子，月：戊寅，日：戊申（你提供）
# -----------------------
ANCHOR_DATETIME = datetime.datetime(1900,2,4,13,51,31)
ANCHOR_YEAR_GZ = "庚子"
ANCHOR_MONTH_GZ = "戊寅"
ANCHOR_DAY_GZ = "戊申"

ANCHOR_YEAR_INDEX = GZS_LIST.index(ANCHOR_YEAR_GZ)
ANCHOR_MONTH_INDEX = GZS_LIST.index(ANCHOR_MONTH_GZ)  # note: month uses stem+branch but index ok for day offset logic if used
ANCHOR_DAY_INDEX = GZS_LIST.index(ANCHOR_DAY_GZ)

# -----------------------
# 日、年、月、时 推算（主方法：锚点法 + 既有规则）
# -----------------------
def day_ganzhi_by_anchor(y,m,d,h=None, minute=0):
    """用 1900-02-04 13:51:31 锚点（戊申日）计算日柱。保留 23点归次日规则。"""
    if h is None:
        target_dt = datetime.datetime(y,m,d,0,0)
    else:
        target_dt = datetime.datetime(y,m,d,int(h),int(minute or 0))
        if int(h) >= 23:
            target_dt = target_dt + timedelta(days=1)
    seconds_diff = (target_dt - ANCHOR_DATETIME).total_seconds()
    days_offset = int(seconds_diff // 86400)  # 向下取整天
    idx = (ANCHOR_DAY_INDEX + days_offset) % 60
    return GZS_LIST[idx]

def get_li_chun_datetime(year):
    # 保持你之前的近似立春判年（2月4日 00:00）
    return datetime.datetime(year,2,4,0,0)

def year_ganzhi_by_anchor_and_lichun(year, month, day, hour=0, minute=0):
    """
    年柱：以锚点年（1900年对应庚子）为基准，同时保留立春判年逻辑：
    - 先用立春判断该出生日期属于哪一年（adj_year）
    - 计算 adj_year - 1900 的偏移，叠加到 ANCHOR_YEAR_INDEX 得到年柱
    """
    dt = datetime.datetime(year, month, day, hour, minute)
    lichun = get_li_chun_datetime(year)
    adj_year = year if dt >= lichun else year - 1
    offset = adj_year - ANCHOR_DATETIME.year  # adj_year - 1900
    idx = (ANCHOR_YEAR_INDEX + offset) % 60
    return GZS_LIST[idx], adj_year

# 月支（节气近似）与月干（五虎遁）
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

# 时辰（五鼠遁）
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

# -----------------------
# 年份映射与显示（保持原来风格）
# -----------------------
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

# -----------------------
# 真太阳时：geocode 常用城市下拉（中国）或手动输入
# -----------------------
COMMON_CHINA_CITIES = {
    "北京 (Beijing)": (39.9042, 116.4074),
    "上海 (Shanghai)": (31.2304, 121.4737),
    "广州 (Guangzhou)": (23.1291, 113.2644),
    "深圳 (Shenzhen)": (22.5431, 114.0579),
    "杭州 (Hangzhou)": (30.2741, 120.1551),
    "成都 (Chengdu)": (30.5728, 104.0668),
    "重庆 (Chongqing)": (29.5630, 106.5516),
    "西安 (Xi'an)": (34.3416, 108.9398),
    "天津 (Tianjin)": (39.3434,117.3616),
    "武汉 (Wuhan)": (30.5928,114.3055),
    "南京 (Nanjing)": (32.0603,118.7969),
    "青岛 (Qingdao)": (36.0671,120.3826),
    "苏州 (Suzhou)": (31.2989,120.5853),
}

def geocode_place(place_name):
    """尝试用内置常用城市映射；否则用 geopy 在线解析"""
    if not place_name:
        return None, None
    # 先尝试匹配下拉中的城市 key
    for k,(lat,lon) in COMMON_CHINA_CITIES.items():
        if place_name.strip().lower() == k.lower() or place_name.strip().lower() in k.lower():
            return lat, lon
    # 否则尝试 geopy
    try:
        geolocator = Nominatim(user_agent="bazi_streamlit_app")
        loc = geolocator.geocode(place_name, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
    except Exception:
        pass
    return None, None

def apply_true_solar_correction_dt(dt_obj, lon):
    """
    真太阳时修正（近似）：
    标准经度 = round(lon/15) * 15
    偏移分钟 = 4 * (lon - 标准经度)
    返回修正后的 datetime
    """
    tz_hours = int(round(lon / 15.0))
    std_meridian = tz_hours * 15.0
    minutes_offset = 4.0 * (lon - std_meridian)
    corrected = dt_obj + timedelta(minutes=minutes_offset)
    return corrected

# -----------------------
# 页面交互
# -----------------------
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
        use_true_solar = st.checkbox("使用真太阳时换算（按出生地经纬度，需网络或选择城市）", value=False)
        # 城市下拉与手动输入并存
        city_choice = st.selectbox("常用城市（可选）", ["（无）"] + list(COMMON_CHINA_CITIES.keys()))
        manual_place = st.text_input("或手动输入地名（优先）", value="")
        # sxtwl 校验/覆盖选项（只有本地安装了才可选）
        sxtwl_option = False
        if HAS_SXTWL:
            sxtwl_option = st.checkbox("使用本地 sxtwl 做并列计算并可选择覆盖（若安装）", value=False)
            if sxtwl_option:
                use_sxtwl_override = st.checkbox("以 sxtwl 结果覆盖锚点结果（若 sxtwl 可用）", value=False)
        else:
            st.info("本地未检测到 sxtwl，若需更严格天文校验请在本机安装 sxtwl。")

        if unknown_time:
            bhour = -1
            bmin = 0
        else:
            bhour = st.number_input("小时（0-23）", min_value=0, max_value=23, value=8, step=1)
            bmin = st.number_input("分钟（0-59）", min_value=0, max_value=59, value=0, step=1)

    if st.button("查询吉凶"):
        hour_val = None if bhour == -1 else int(bhour)
        min_val = None if bhour == -1 else int(bmin)
        # 设定计算用的年月日时分（可能被真太阳时修正）
        calc_year, calc_month, calc_day = byear, bmonth, bday
        calc_hour, calc_min = hour_val, min_val

        # 真太阳时逻辑：如果启用并且用户提供时分，则先确定经纬度（下拉优先、手动优先）
        if use_true_solar and hour_val is not None:
            place_to_use = manual_place.strip() if manual_place.strip() else (city_choice if city_choice != "（无）" else "")
            if not place_to_use:
                st.warning("启用了真太阳时但未选择/输入城市，已跳过真太阳时修正。")
            else:
                lat, lon = geocode_place(place_to_use)
                if lat is None:
                    st.warning("无法解析该地名，经纬度获取失败，已跳过真太阳时修正。")
                else:
                    # 构造出生本地时间 datetime（不处理时区偏移，近似用本地时间）
                    base_dt = datetime.datetime(byear, bmonth, bday, hour_val or 0, min_val or 0)
                    corrected = apply_true_solar_correction_dt(base_dt, lon)
                    st.info(f"已使用地点 {place_to_use}（经度 {lon:.4f}）进行真太阳时（近似）修正：{corrected.strftime('%Y-%m-%d %H:%M')}")
                    calc_year, calc_month, calc_day, calc_hour, calc_min = corrected.year, corrected.month, corrected.day, corrected.hour, corrected.minute

        # 如果启用 sxtwl 并勾选了并列计算，尝试用 sxtwl 获取八字（捕获异常）
        sxtwl_result = None
        if HAS_SXTWL and 'sxtwl_option' in locals() and sxtwl_option:
            try:
                # 下面对 sxtwl 的调用采用通用尝试方式；不同版本可能有 API 差异
                # 我们尝试尽量处理常见的 sxtwl 接口
                try:
                    cal = sxtwl.Calendar()
                    solar = cal.solar2lunar(calc_year, calc_month, calc_day)
                    # sxtwl 的日干支获取
                    day_gz = solar.getGanZhiDay()
                    # 天干地支字符串（部分版本接口不同）
                    # 尝试一系列属性取值（容错）
                    day_gz_str = None
                    if hasattr(solar, "getDayGanZhi"):
                        day_gz_str = solar.getDayGanZhi()
                    elif hasattr(solar, "getGanZhiDay"):
                        day_gz_str = solar.getGanZhiDay()
                    elif hasattr(solar, "GanZhiDay"):
                        day_gz_str = solar.GanZhiDay
                    # year/month/day via cal.solar2lunar might yield useful fields
                    # As sxtwl API varies, we'll fallback to None if can't fetch
                    # NOTE: this block is best-effort; if your local sxtwl API differs, you can adapt this section.
                    sxtwl_result = {
                        "day_gz": day_gz_str,
                        "solar_obj": solar
                    }
                except Exception:
                    # Some sxtwl variants provide direct classes for Solar
                    try:
                        solar = sxtwl.Solar(calc_year, calc_month, calc_day)
                        # many bindings have solar.getDayGanZhi() etc.
                        if hasattr(solar, "getDayGanZhi"):
                            day_gz_str = solar.getDayGanZhi()
                        else:
                            day_gz_str = None
                        sxtwl_result = {"day_gz": day_gz_str, "solar_obj": solar}
                    except Exception:
                        sxtwl_result = None
            except Exception:
                sxtwl_result = None

        # --- 主推算（锚点法 + 五虎/五鼠规则） ---
        try:
            # 年柱（改为基于 1900 锚点 + 立春判年）
            year_p, adj_year = year_ganzhi_by_anchor_and_lichun(calc_year, calc_month, calc_day, calc_hour or 0, calc_min or 0)
            # 日柱（锚点日法）
            day_p = day_ganzhi_by_anchor(calc_year, calc_month, calc_day, calc_hour, calc_min)
            # 月柱按节气确定地支 + 五虎遁算干
            mb = get_month_branch(calc_year, calc_month, calc_day)
            month_p = month_stem_by_fihu_dun(year_p[0], mb)
            # 时柱按五鼠遁
            hour_p = "不知道" if calc_hour is None else time_ganzhi_by_rule(day_p, calc_hour, calc_min or 0)

            # 如果 sxtwl 可用且用户选择以 sxtwl 覆盖，则尝试覆盖（以 sxtwl 提供数据为准）
            if HAS_SXTWL and 'sxtwl_option' in locals() and sxtwl_option and 'use_sxtwl_override' in locals() and use_sxtwl_override and sxtwl_result:
                # 尝试解析 sxtwl_result 中的字段来获取年/月/日/时（兼容性视本地 sxtwl）
                # 这是 best-effort：不同 sxtwl 版本字段名不同，请按本地 sxtwl API 适配
                try:
                    # 如果 sxtwl_result contains day_gz that is string like "甲子"
                    if sxtwl_result.get("day_gz"):
                        day_p = sxtwl_result["day_gz"]
                    # cannot reliably get year/month/hour from best-effort extraction; keep other pillars unless you adapt
                    st.success("已使用本地 sxtwl 的日柱（如可获取）覆盖锚点日柱。")
                except Exception:
                    st.warning("尝试用 sxtwl 覆盖时失败，仍使用锚点结果。")

            # 显示四柱（天干一行、地支一行，五行着色）
            st.markdown("## 四柱八字")
            render_four_pillars_two_rows(year_p, month_p, day_p, hour_p)

            # 若 sxtwl 并列计算，显示 sxtwl 的日柱/年柱以供比对（非覆盖时）
            if HAS_SXTWL and 'sxtwl_option' in locals() and sxtwl_option and sxtwl_result:
                st.markdown("### （sxtwl 对比结果，若可用）")
                st.write("sxtwl 计算得到（如可解析）：")
                st.json(sxtwl_result)

            # 吉凶计算并显示（从出生年开始列到2100年；未来年份标★）
            ji, xiong = analyze_bazi(year_p, month_p, day_p, hour_p)
            st.markdown("---")
            show_jixiong(ji, xiong, byear)

        except Exception as e:
            st.error(f"计算出错：{e}")

else:
    # 直接输入四柱八字模式（保持不变）
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
