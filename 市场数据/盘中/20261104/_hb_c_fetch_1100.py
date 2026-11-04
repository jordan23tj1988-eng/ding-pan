# -*- coding: utf-8 -*-
"""hb-c 11:00 取数: 腾讯实时报价(持仓/指数) + 东财涨停/炸板/跌停池"""
import json, urllib.request, os, datetime

D = r"D:\股票数据\市场数据\盘中\20261104"
DATE = "20261104"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

codes = "sh600261,sz002652,sz603906,sh600299,sh600259,sz002365,sz001287,sh000001,sz399001,sz399006,sh000688"
url = "https://qt.gtimg.cn/q=" + codes
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
raw = urllib.request.urlopen(req, timeout=20).read().decode("gbk", "replace")
rows = {}
for seg in raw.strip().split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    key, _, body = seg.partition("=")
    key = key.strip()[2:]
    f = body.strip().strip('"').split("~")
    if len(f) < 40:
        continue
    rows[key] = {"code": f[2], "name": f[1], "px": float(f[3]), "pre": float(f[4]), "open": float(f[5]),
                 "pct": float(f[32]), "high": float(f[33]), "low": float(f[34]),
                 "amt_wan": float(f[37]) if f[37] else None,
                 "bid1": f[9], "bid1_vol": f[10], "ask1": f[19], "ask1_vol": f[20], "t": f[30]}
json.dump({"fetched": NOW, "rows": rows}, open(os.path.join(D, "_hb_c_quote_1100.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("=== 腾讯", NOW, "===")
for k, v in rows.items():
    print(k, v["name"], v["px"], "%+.2f%%" % v["pct"], "bid1", v["bid1"], "x", v["bid1_vol"], "ask1", v["ask1"], "x", v["ask1_vol"])

# 东财涨停/炸板/跌停池
zt_url = "https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date=" + DATE
zb_url = "https://push2ex.eastmoney.com/getTopicZBPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date=" + DATE
dt_url = "https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fund%3Aasc&date=" + DATE


def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=20).read().decode("utf-8", "replace"))
    d = j.get("data") or {}
    return d.get("pool") or []


out = {"fetched": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
for name, u in (("zt", zt_url), ("zb", zb_url), ("dt", dt_url)):
    try:
        out[name] = get(u)
    except Exception as e:
        out[name] = []
        out[name + "_err"] = repr(e)
json.dump(out, open(os.path.join(D, "_hb_c_pools_1100.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
zt, zb, dt = out["zt"], out["zb"], out["dt"]
print("=== 东财池", out["fetched"], "zt", len(zt), "zb", len(zb), "dt", len(dt), "err", out.get("zt_err"), out.get("zb_err"), out.get("dt_err"))
from collections import Counter
print("连板分布", dict(sorted(Counter(x["lbc"] for x in zt).items())))
print("二板加", sum(1 for x in zt if x["lbc"] >= 2), "炸板率", round(len(zb) / (len(zt) + len(zb)), 4) if (zt or zb) else None)
print("zt_top", [(x["n"], x["lbc"], x.get("hybk")) for x in sorted(zt, key=lambda y: -y["lbc"])[:6]])
print("zb_top", [(x["n"], round(x["zdp"], 2), x.get("hybk")) for x in sorted(zb, key=lambda y: y["zdp"])[:8]])
