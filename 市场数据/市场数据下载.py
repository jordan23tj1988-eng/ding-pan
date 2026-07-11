# -*- coding: utf-8 -*-
"""
市场数据下载.py —— 免费源(akshare)抓每日短线情绪数据(实测稳口径)
落地到 BASE/YYYYMMDD/: zt_pool/dt_pool/zb_pool/strong_pool/lhb .csv + summary.json
用法: python 市场数据下载.py [YYYYMMDD]
(2026-07-07 main()因挂载长行写入被截断,按现有schema重建;helper保持原样)
"""
import sys, os, json, time, datetime, glob, collections
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q")
    import akshare as ak
import pandas as pd, requests

def _safe_dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2, default=str)); f.truncate()

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据")
    BASE = g[0] if g else BASE

def retry(fn, tries=3, wait=2, label=""):
    for i in range(tries):
        try:
            r = fn()
            if r is not None and (not hasattr(r, "__len__") or len(r) > 0):
                return r
        except Exception:
            time.sleep(wait)
    print("  [跳过] " + label)
    return None

def turnover_yi():
    """两市成交额(亿)=上证(全沪)+深证综指(全深),sina源。"""
    try:
        sp = ak.stock_zh_index_spot_sina().set_index("代码")
        sh = float(sp.loc["sh000001", "成交额"]); sz = float(sp.loc["sz399106", "成交额"])
        return round((sh + sz) / 1e8, 0)
    except Exception:
        return None

def fetch_lhb_direct(date_str):
    """龙虎榜直连回退(akshare挂时用)。东财16:30后才全。"""
    try:
        sess = requests.Session(); sess.trust_env = False
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        cols = ("SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,EXPLAIN,CLOSE_PRICE,"
                "CHANGE_RATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,"
                "BILLBOARD_DEAL_AMT,ACCUM_AMOUNT,DEAL_NET_RATIO,DEAL_AMOUNT_RATIO,TURNOVERRATE,"
                "FREE_MARKET_CAP,EXPLANATION,D1_CLOSE_ADJCHRATE,D2_CLOSE_ADJCHRATE,"
                "D5_CLOSE_ADJCHRATE,D10_CLOSE_ADJCHRATE")
        params = {"sortColumns": "SECURITY_CODE,TRADE_DATE", "sortTypes": "1,-1",
                  "pageSize": "5000", "pageNumber": 1,
                  "reportName": "RPT_DAILYBILLBOARD_DETAILSNEW", "columns": cols,
                  "source": "WEB", "client": "WEB",
                  "filter": "(TRADE_DATE<='%s')(TRADE_DATE>='%s')" % (date_str, date_str)}
        r = sess.get(url, params=params, timeout=15); data = r.json()
        if not data.get("success") or not data.get("result"):
            return None
        total_pages = int(data["result"]["pages"]); all_rows = data["result"].get("data", []) or []
        for page in range(2, total_pages + 1):
            params["pageNumber"] = page; d2 = sess.get(url, params=params, timeout=15).json()
            if d2.get("success") and d2["result"] and d2["result"].get("data"):
                all_rows.extend(d2["result"]["data"])
        if not all_rows:
            return None
        rec = []
        for row in all_rows:
            rec.append({"代码": str(row.get("SECURITY_CODE", "")).zfill(6),
                        "名称": row.get("SECURITY_NAME_ABBR", ""),
                        "上榜日": str(row.get("TRADE_DATE", ""))[:10] if row.get("TRADE_DATE") else "",
                        "解读": row.get("EXPLANATION", "") or "", "收盘价": row.get("CLOSE_PRICE"),
                        "涨跌幅": row.get("CHANGE_RATE"), "龙虎榜净买额": row.get("BILLBOARD_NET_AMT"),
                        "龙虎榜买入额": row.get("BILLBOARD_BUY_AMT"), "龙虎榜卖出额": row.get("BILLBOARD_SELL_AMT"),
                        "龙虎榜成交额": row.get("BILLBOARD_DEAL_AMT"), "市场总成交额": row.get("ACCUM_AMOUNT"),
                        "换手率": row.get("TURNOVERRATE"), "流通市值": row.get("FREE_MARKET_CAP"),
                        "上榜原因": row.get("EXPLAIN", "") or ""})
        return pd.DataFrame(rec)
    except Exception as e:
        print("  [直接API龙虎榜失败] " + str(e)); return None

def _junk(name):
    """ST/退市整理/N/C新股 -> 统计层剔除(原始csv保留)。2026-07-11 P0-2。"""
    s = str(name or "")
    return ("ST" in s.upper()) or ("退" in s) or s.startswith("N") or s.startswith("C")

def _stat(df):
    """统计口径过滤:剔ST/退/N/C。df可为None。"""
    if df is None or "名称" not in getattr(df, "columns", []):
        return df
    return df[~df["名称"].astype(str).map(_junk)]

def _codes(df):
    return set(df["代码"].astype(str)) if (df is not None and "代码" in df.columns) else set()

def main():
    guess = datetime.date.today()
    if len(sys.argv) > 1:
        guess = datetime.datetime.strptime(sys.argv[1], "%Y%m%d").date()
    now = datetime.datetime.now()
    is_before_close = now.hour < 15 or (now.hour == 15 and now.minute < 10)

    # 探测最近交易日:涨停池非空
    d, zt = None, None
    for dd in range(0, 8):
        cand = (guess - datetime.timedelta(days=dd)).strftime("%Y%m%d")
        z = retry(lambda c=cand: ak.stock_zt_pool_em(date=c), label="涨停池 " + cand)
        if z is not None and len(z) > 0:
            d, zt = cand, z; break
    if d is None:
        print("[失败] 8天内未探到涨停数据"); return

    # 盘前脏数据护栏:收盘前若"当日"与前一交易日雷同,顺延
    if is_before_close and d == guess.strftime("%Y%m%d"):
        for dd2 in range(1, 8):
            c2 = (guess - datetime.timedelta(days=dd2)).strftime("%Y%m%d")
            z2 = retry(lambda c=c2: ak.stock_zt_pool_em(date=c), label="prev " + c2)
            if z2 is not None and len(z2) > 0:
                if _codes(zt) == _codes(z2):
                    print("[护栏] 盘前数据与前日雷同,顺延为 " + c2); d, zt = c2, z2
                break

    OUT = os.path.join(BASE, d); os.makedirs(OUT, exist_ok=True)
    zt.to_csv(os.path.join(OUT, "zt_pool.csv"), index=False, encoding="utf-8-sig")

    dt = retry(lambda: ak.stock_zt_pool_dtgc_em(date=d), label="跌停池")
    zb = retry(lambda: ak.stock_zt_pool_zbgc_em(date=d), label="炸板池")
    strong = retry(lambda: ak.stock_zt_pool_strong_em(date=d), label="强势股池")
    for df, fn in [(dt, "dt_pool.csv"), (zb, "zb_pool.csv"), (strong, "strong_pool.csv")]:
        if df is not None and len(df) > 0:
            df.to_csv(os.path.join(OUT, fn), index=False, encoding="utf-8-sig")

    lhb = retry(lambda: ak.stock_lhb_detail_em(start_date=d, end_date=d), label="龙虎榜")
    if lhb is None or len(lhb) == 0:
        lhb = fetch_lhb_direct(d)
    if lhb is not None and len(lhb) > 0:
        lhb.to_csv(os.path.join(OUT, "lhb.csv"), index=False, encoding="utf-8-sig")

    # 汇总(统计口径剔ST/退/N/C,与THS三池历史口径对齐;原始csv不动)
    zt_s = _stat(zt); dt_s = _stat(dt); zb_s = _stat(zb)
    lb = collections.Counter(); top = 0
    if "连板数" in zt_s.columns:
        for v in zt_s["连板数"].fillna(1):
            try: n = int(float(v))
            except Exception: n = 1
            lb[str(n)] += 1; top = max(top, n)
    ind = collections.Counter(); ind2 = collections.Counter()
    for _, row in zt_s.iterrows():
        try: n = int(float(row.get("连板数", 1)))
        except Exception: n = 1
        hy = row.get("所属行业") if "所属行业" in zt_s.columns else None
        if hy:
            ind[hy] += 1
            if n >= 2: ind2[hy] += 1
    n_zt = len(zt_s); n_dt = len(dt_s) if dt_s is not None else 0; n_zb = len(zb_s) if zb_s is not None else 0
    n_cut = len(zt) - len(zt_s)
    rate = round(n_zb / (n_zt + n_zb), 3) if (n_zt + n_zb) > 0 else None
    summary = {"日期": d, "两市成交额_亿": turnover_yi(), "涨停家数": n_zt, "跌停家数": n_dt,
               "炸板家数": n_zb, "炸板率": rate, "最高连板": top,
               "连板梯队": {k: lb[k] for k in sorted(lb, key=lambda x: -int(x))},
               "涨停行业扎堆Top12": ind.most_common(12), "连板≥2行业Top8": ind2.most_common(8),
               "统计口径": "剔ST/退/N/C(原始csv保留)", "剔除涨停家数": n_cut,
               "龙虎榜条数": len(lhb) if lhb is not None else 0,
               "抓取时间": now.strftime("%Y-%m-%d %H:%M:%S")}
    _safe_dump(summary, os.path.join(OUT, "summary.json"))
    print("[完成] %s 涨停%d 跌停%d 炸板%d 最高%d板 量能%s亿 龙虎榜%d" % (
        d, n_zt, n_dt, n_zb, top, summary["两市成交额_亿"], summary["龙虎榜条数"]))

if __name__ == "__main__":
    main()
