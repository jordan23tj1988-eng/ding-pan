# -*- coding: utf-8 -*-
"""分析引擎.py —— 当日数据→题材树+核心标的龙头分+席位动向→analysis.json。不编造。
龙头分=身位30+封单质量25+资金20+题材地位15+席位加成(按_席位胜率库真实胜率加权)。
用法: python 分析引擎.py [YYYYMMDD]"""
import sys, os, json, glob, datetime, socket, time as _time
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q"); import akshare as ak
import pandas as pd, numpy as np
try:
    import requests as _requests
except Exception:
    _requests = None
socket.setdefaulttimeout(5)

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

def _safe_dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2, default=str)); f.truncate()

SEATS = {
    "太华路": ("西安太华路", "量化", "开源量化最凶;1字板不接"),
    "西大街": ("西安西大街", "量化", "首板1-2套利;胜率一般"),
    "成章路": ("高新成章路", "量化", "锁仓认节点"),
    "紫阳东路": ("紫阳东路", "量化", "大长腿地天"),
    "知春路": ("北京知春路(派神)", "量化", "审美好"),
    "永城路": ("永城路", "量化", "专做地天;分时丑不接"),
    "万豪世家": ("万豪世家(紫阳系)", "量化", "紫阳系"),
    "光复路": ("章盟主(章建平)", "顶级游资", "格局派善庄"),
    "溧阳路": ("中信溧阳路系", "顶级游资", "顶流打板"),
    "上塘路": ("欢乐海岸系", "顶级游资", "造抱团穿越"),
    "机构专用": ("机构", "机构", "价投趋势"),
    "沪股通": ("外资(北向)", "机构", "外资/GJD"),
    "深股通": ("外资(北向)", "机构", "外资/GJD"),
}
def map_seat(name):
    for k, v in SEATS.items():
        if k in str(name):
            return v
    return (None, "其他/未知", "")

def latest_dir(guess):
    for dd in range(0, 8):
        d = (guess - datetime.timedelta(days=dd)).strftime("%Y%m%d")
        if os.path.isfile(os.path.join(BASE, d, "zt_pool.csv")):
            return d
    return None

def _fetch_seat_direct(code, date_str):
    """akshare挂时用 datacenter-web 直连回退。"""
    if _requests is None:
        return None
    try:
        sess = _requests.Session(); sess.trust_env = False
        rows = []
        for flag in ["RPT_BILLBOARD_DAILYDETAILSBUY", "RPT_BILLBOARD_DAILYDETAILSSELL"]:
            params = {"reportName": flag, "columns": "ALL",
                      "filter": "(TRADE_DATE='%s-%s-%s')(SECURITY_CODE=\"%s\")" % (date_str[0:4], date_str[4:6], date_str[6:8], code),
                      "pageNumber": "1", "pageSize": "500", "source": "WEB", "client": "WEB"}
            r = sess.get("https://datacenter-web.eastmoney.com/api/data/v1/get", params=params, timeout=8)
            data = r.json()
            if data.get("result") and data["result"].get("data"):
                for row in data["result"]["data"]:
                    net = float(row.get("NET", 0) or 0)
                    if "SELL" in flag: net = -abs(net)
                    rows.append({"交易营业部名称": row.get("OPERATEDEPT_NAME", ""), "净额": net})
        return pd.DataFrame(rows) if rows else None
    except Exception:
        return None

def seat_scan(codes_names, d, budget=28):
    agg = {}; t0 = _time.time()
    for code, name in codes_names:
        if _time.time() - t0 > budget: break
        code = str(code).zfill(6); df = None
        try:
            df = ak.stock_lhb_stock_detail_em(symbol=code, date=d, flag="买入")
        except Exception:
            pass
        if df is None or len(df) == 0:
            df = _fetch_seat_direct(code, d)
        if df is None or len(df) == 0: continue
        for _, r in df.iterrows():
            seat_name = str(r.get("交易营业部名称", ""))
            net = float(r.get("净额", 0) or 0)
            youzi, typ, style = map_seat(seat_name)
            key = (code, seat_name)
            if key in agg: agg[key]["净额"] += net
            else: agg[key] = dict(代码=code, 名称=name, 营业部=seat_name, 游资=youzi, 类型=typ, 净额=net)
    return list(agg.values())

def _norm_seat(n):
    n = str(n).replace(" ", "")
    for suf in ("股份有限公司", "证券有限责任公司", "证券有限公司", "有限责任公司", "有限公司"):
        n = n.replace(suf, "")
    return n

def main():
    guess = datetime.date.today()
    if len(sys.argv) > 1:
        guess = datetime.datetime.strptime(sys.argv[1], "%Y%m%d").date()
    d = latest_dir(guess)
    if not d:
        print("无当日数据,先跑 市场数据下载.py"); return
    D = os.path.join(BASE, d)
    zt = pd.read_csv(os.path.join(D, "zt_pool.csv"), dtype={"代码": str}); zt["代码"] = zt["代码"].str.zfill(6)

    themes = []
    for ind, g in zt.groupby("所属行业"):
        g = g.sort_values("连板数", ascending=False)
        themes.append(dict(题材=ind, 涨停数=int(len(g)), 最高板=int(g["连板数"].max()),
                           连板2plus=int((g["连板数"] >= 2).sum()),
                           核心标的=str(g.iloc[0]["名称"]), 核心代码=str(g.iloc[0]["代码"]), 核心连板=int(g.iloc[0]["连板数"])))
    themes = sorted(themes, key=lambda x: (x["涨停数"], x["最高板"]), reverse=True)

    cand = zt[(zt["连板数"] >= 2) | (zt["封板资金"] >= zt["封板资金"].quantile(0.9))].copy()
    theme_maxban = {t["题材"]: t["最高板"] for t in themes}
    main_inds = set([t["题材"] for t in themes[:3]])
    amt_rank = zt["成交额"].rank(pct=True)
    def score(r):
        tb = max(theme_maxban.get(r["所属行业"], 1), 1)
        s_pos = 30 * min(r["连板数"] / tb, 1.0)
        fc = r["封板资金"] / max(r["流通市值"], 1)
        t = str(int(r["首次封板时间"])).zfill(6)
        early = 1.0 if t <= "093000" else (0.6 if t <= "100000" else 0.3)
        s_seal = 25 * (min(fc / 0.05, 1.0) * 0.5 + early * 0.35 + (0 if r["炸板次数"] > 0 else 0.15))
        s_amt = 20 * float(amt_rank.get(r.name, 0.5))
        is_main = r["所属行业"] in main_inds
        is_top = r["连板数"] == theme_maxban.get(r["所属行业"], 0)
        s_theme = 15 * ((0.6 if is_main else 0) + (0.4 if is_top else 0))
        return round(s_pos + s_seal + s_amt + s_theme, 1)
    cand["龙头基础分"] = cand.apply(score, axis=1)

    top_cand = cand.sort_values("龙头基础分", ascending=False).head(8)
    seats = seat_scan(list(zip(top_cand["代码"], top_cand["名称"])), d)
    winlib = {}
    libp = os.path.join(BASE, "_席位胜率库.json")
    if os.path.isfile(libp):
        try: winlib = json.load(open(libp, encoding="utf-8")).get("近三月", {})
        except Exception: winlib = {}
    idx = {}
    for k in winlib:
        idx[k] = k; idx[_norm_seat(k)] = k
    def seat_quality(name):
        rec = winlib.get(str(name)) or winlib.get(idx.get(_norm_seat(name), ""))
        if rec: return rec.get("胜率"), rec.get("涨幅"), rec.get("档")
        return None, None, None
    seat_bonus = {}
    for row in seats:
        wr, chg, dang = seat_quality(row["营业部"]); row["胜率"], row["席位档"] = wr, dang
        if row["净额"] > 0 and wr and chg:
            seat_bonus[row["代码"]] = max(seat_bonus.get(row["代码"], 0), round(max(0, min(12, chg*wr/100.0*4)), 1))
        elif row["净额"] > 0 and row["类型"] in ("顶级游资", "机构"):
            seat_bonus[row["代码"]] = max(seat_bonus.get(row["代码"], 0), 6)
        elif row["净额"] > 0 and row["类型"].startswith("量化"):
            seat_bonus[row["代码"]] = max(seat_bonus.get(row["代码"], 0), 5)
    cand["席位加成"] = cand["代码"].map(seat_bonus).fillna(0)
    cand["龙头分"] = (cand["龙头基础分"] + cand["席位加成"]).clip(upper=100)
    cand["龙头档"] = pd.cut(cand["龙头分"], [0, 45, 65, 101], labels=["低", "中", "高"])
    cand["类型"] = np.where(cand["连板数"] >= 2, "连板情绪龙", "趋势/权重票")
    core = cand.sort_values("龙头分", ascending=False)[
        ["代码", "名称", "所属行业", "类型", "连板数", "涨停统计", "封板资金", "首次封板时间", "炸板次数", "龙头基础分", "席位加成", "龙头分", "龙头档"]].head(15)

    out = dict(日期=d, 题材树=themes[:12], 核心标的=core.to_dict("records"), 席位动向=seats)
    _safe_dump(out, os.path.join(D, "analysis.json"))
    print("done ->", os.path.join(D, "analysis.json"), "| 题材%d 核心%d 席位%d" % (len(themes), len(core), len(seats)))

if __name__ == "__main__":
    main()
