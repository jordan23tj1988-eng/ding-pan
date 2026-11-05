# -*- coding: utf-8 -*-
"""hb-d 持仓分时（东财 trends2）+ 涨停池首封时段分布"""
import json, os, urllib.request, datetime

D = r"D:\股票数据\市场数据\盘中\20261105"
POS = {"600299": ("1", "安迪苏", 8.2041, 2300), "600259": ("1", "中稀有色", 60.2301, 100),
       "603906": ("1", "龙蟠科技", 15.5678, 600), "002292": ("0", "奥飞娱乐", 9.3747, 500)}
out = {}
for code, (mk, name, cost, sh) in POS.items():
    u = ("https://push2his.eastmoney.com/api/qt/stock/trends2/get?secid=%s.%s&fields1=f1,f2,f3,f4,f5,f6,f7,f8"
         "&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&ndays=1" % (mk, code))
    try:
        r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
        j = json.loads(urllib.request.urlopen(r, timeout=20).read().decode("utf-8", "replace"))
        d = j.get("data") or {}
        pre = d.get("preClose") or d.get("prePrice")
        tr = d.get("trends") or []
        rows = []
        for line in tr:
            f = line.split(",")
            rows.append({"t": f[0], "px": float(f[2]), "pct": round((float(f[2]) / pre - 1) * 100, 2) if pre else None})
        hi = max(rows, key=lambda x: x["px"]) if rows else None
        last = rows[-1] if rows else None
        d2 = round(last["pct"] - rows[-3]["pct"], 2) if len(rows) >= 3 else None
        pnl = round((last["px"] / cost - 1) * 100, 2) if last else None
        out[code] = {"name": name, "pre": pre, "cost": cost, "shares": sh, "last": last, "hi": hi,
                     "lo": min(rows, key=lambda x: x["px"]) if rows else None,
                     "dd_from_hi_pct": round((last["px"] / hi["px"] - 1) * 100, 2) if hi and last else None,
                     "pnl_pct": pnl, "d2min_pp": d2, "rows": len(rows),
                     "limit_px": round(pre * 1.1, 2) if pre else None,
                     "touched_limit": bool(hi and pre and hi["px"] >= round(pre * 1.1, 2) - 0.005)}
        print(code, name, "pre", pre, "last", last, "hi", hi, "dd", out[code]["dd_from_hi_pct"],
              "pnl%", pnl, "d2min", d2, "涨停价", out[code]["limit_px"], "摸板", out[code]["touched_limit"])
    except Exception as e:
        out[code] = {"name": name, "err": repr(e)}
        print(code, name, "ERR", repr(e))
json.dump(out, open(os.path.join(D, "_hb_d_pos_1330.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

pools = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))
zt = pools["zt"]
def seg(x):
    t = str(x.get("fbt", "")).zfill(6)
    h = int(t[:2]) if len(t) >= 4 else 0
    m = int(t[2:4]) if len(t) >= 4 else 0
    return h * 60 + m
from collections import Counter
buckets = Counter()
for x in zt:
    s = seg(x)
    if s == 0:
        buckets["na"] += 1
    elif s < 10 * 60 + 30:
        buckets["<=10:30"] += 1
    elif s < 11 * 60 + 30:
        buckets["10:30-11:30"] += 1
    elif s < 13 * 60 + 30:
        buckets["13:00-13:30"] += 1
    else:
        buckets[">13:30"] += 1
print("首封时段分布", dict(buckets))
print("hy_cnt", Counter(x.get("hybk") for x in zt).most_common(8))
print("光伏涨停", [(x["n"], x["lbc"], round(x["zdp"], 2)) for x in zt if x.get("hybk") == "光伏设备"])
print("昨池破-8名单", [x for x in zt if False])
