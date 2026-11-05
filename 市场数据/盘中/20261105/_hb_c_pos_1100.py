# -*- coding: utf-8 -*-
"""持仓分时（东财 trends 1min）+ 题材线核对"""
import json, urllib.request, os

D = r"D:\股票数据\市场数据\盘中\20261105"


def trends(secid):
    u = ("https://push2his.eastmoney.com/api/qt/stock/trends2/get?secid=%s&fields1=f1,f2,f3,f4,f5,f6,f7,f8"
         "&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&ndays=1" % secid)
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=20).read().decode("utf-8", "replace"))
    d = j.get("data") or {}
    return d.get("preClose"), (d.get("trends") or [])


SEC = {"600299": "1.600299", "600259": "1.600259", "603906": "1.603906",
       "002292": "0.002292", "002652": "0.002652"}
out = {}
for c, sid in SEC.items():
    pre, tr = trends(sid)
    rows = []
    for line in tr:
        f = line.split(",")
        # f[0] time, f[1] open? (东财: 时间,开盘,最新,最高,最低,成交量,成交额,均价)
        try:
            rows.append({"t": f[0], "px": float(f[2]), "high": float(f[3]), "low": float(f[4])})
        except Exception:
            continue
    pcts = [round((r["px"] / pre - 1) * 100, 2) for r in rows]
    lo = min(rows, key=lambda r: r["px"]) if rows else None
    hi = max(rows, key=lambda r: r["px"]) if rows else None
    # 最近2分钟（末两分钟）变化
    d2 = round(pcts[-1] - pcts[-3], 2) if len(pcts) >= 3 else None
    # 从最高点回撤
    dd = round((rows[-1]["px"] / hi["px"] - 1) * 100, 2) if rows else None
    out[c] = {"pre": pre, "n": len(rows), "last_t": rows[-1]["t"] if rows else None,
              "last_pct": pcts[-1] if pcts else None, "last_px": rows[-1]["px"] if rows else None,
              "hi_pct": round((hi["px"] / pre - 1) * 100, 2) if hi else None,
              "hi_t": hi["t"] if hi else None,
              "lo_pct": round((lo["px"] / pre - 1) * 100, 2) if lo else None,
              "lo_t": lo["t"] if lo else None,
              "d2min": d2, "dd_from_hi_pct": dd,
              "series_tail": [(rows[i]["t"], pcts[i]) for i in range(max(0, len(rows) - 6), len(rows))]}
    print(c, out[c])

# 最低点之后是否曾触板
for c, v in out.items():
    print("CHK", c, "hi_pct", v["hi_pct"], "limit?", v["hi_pct"] and v["hi_pct"] >= (19.7 if c.startswith(("30", "68")) else 9.7))

json.dump(out, open(os.path.join(D, "_hb_c_pos_trends_1100.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

pools = json.load(open(os.path.join(D, "_hb_c_pools_1100.json"), encoding="utf-8"))
from collections import Counter
print("=== 涨停题材", Counter(x.get("hybk") for x in pools["zt"]).most_common(8))
print("=== 炸板题材", Counter(x.get("hybk") for x in pools["zb"]).most_common(8))
print("=== 炸板个股全", [(x["c"], x["n"], round(x["zdp"], 2), x.get("hybk"), x.get("lbc")) for x in sorted(pools["zb"], key=lambda y: y["zdp"])])
