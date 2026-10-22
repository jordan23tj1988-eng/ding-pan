# -*- coding: utf-8 -*-
"""跌停池正确口径重取(sort=fund:asc) + 高位/照会票报价留档, 供哨兵核对"""
import json, urllib.request, io, datetime

D = r"D:\股票数据\市场数据\盘中\20261022"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

u = ("https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989"
     "&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fund%3Aasc&date=20261022")
r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
j = json.loads(urllib.request.urlopen(r, timeout=15).read().decode("utf-8"))
pl = (j.get("data") or {}).get("pool") or []
io.open(D + r"\_hb_d_pools_1330_dtfix.json", "w", encoding="utf-8").write(
    json.dumps({"fetched": NOW, "url": u, "rc": j.get("rc"), "n": len(pl), "pool": pl}, ensure_ascii=False, indent=1))
print("DT池(正确口径) n=%d rc=%s" % (len(pl), j.get("rc")))
print(sorted(p["c"] for p in pl))

codes = "sz002696,sz000530,sh600202,sz002520,sh601091,sz002724,sh603278,sh600293,sz002076"
u2 = "https://qt.gtimg.cn/q=" + codes
rq = urllib.request.Request(u2, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
raw = urllib.request.urlopen(rq, timeout=15).read().decode("gbk", "replace")
rows = {}
for seg in raw.strip().split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    key = seg.partition("=")[0].strip()[2:]
    f = seg.partition("=")[2].strip().strip('"').split("~")
    if len(f) < 40:
        continue
    rows[key] = {"code": f[2], "name": f[1], "px": float(f[3]), "pct": float(f[32]),
                 "open": float(f[5]), "high": float(f[33]), "low": float(f[34]), "t": f[30]}
io.open(D + r"\_hb_d_quote_hi.json", "w", encoding="utf-8").write(
    json.dumps({"fetched": NOW, "rows": rows}, ensure_ascii=False, indent=1))
for k, v in rows.items():
    print(k, v["name"], v["px"], v["pct"], "o", v["open"], "h", v["high"], "l", v["low"], v["t"])
