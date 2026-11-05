# -*- coding: utf-8 -*-
"""hb-f 14:45 尾盘深场B 取数: 腾讯实时报价(持仓/指数) + 东财涨停/炸板/跌停池 + ticks 广度
用法: python _hb_f_fetch_1445.py [decide|exec]   默认 decide
"""
import json, urllib.request, os, sys, datetime
from collections import Counter

D = r"D:\股票数据\市场数据\盘中\20261105"
DATE = "20261105"
PHASE = sys.argv[1] if len(sys.argv) > 1 else "decide"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

codes = "sh600299,sh600259,sh603906,sz002292,sh000001,sz399001,sz399006,sh000688"
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
out_q = os.path.join(D, "_hb_f_quote_pxexec.json" if PHASE == "exec" else "_hb_f_quote_1445.json")
json.dump({"fetched": NOW, "phase": PHASE, "rows": rows}, open(out_q, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("=== 腾讯", PHASE, NOW, "===")
for k, v in rows.items():
    print(k, v["name"], v["px"], "%+.2f%%" % v["pct"], "hi", v["high"], "lo", v["low"],
          "bid1", v["bid1"], "x", v["bid1_vol"], "ask1", v["ask1"], "x", v["ask1_vol"], v["t"])

if PHASE == "exec":
    sys.exit(0)

zt_url = "https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=400&sort=fbt%3Aasc&date=" + DATE
zb_url = "https://push2ex.eastmoney.com/getTopicZBPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=400&sort=fbt%3Aasc&date=" + DATE
dt_url = "https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=400&sort=fund%3Aasc&date=" + DATE


def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=20).read().decode("utf-8", "replace"))
    d = j.get("data") or {}
    return d.get("pool") or [], d.get("qdate")


out = {"fetched": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
for name, u in (("zt", zt_url), ("zb", zb_url), ("dt", dt_url)):
    try:
        p, qd = get(u)
        out[name] = p
        out[name + "_qdate"] = qd
    except Exception as e:
        out[name] = []
        out[name + "_err"] = repr(e)
json.dump(out, open(os.path.join(D, "_hb_f_pools_1445.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
zt, zb, dt = out["zt"], out["zb"], out["dt"]
print("=== 东财池", out["fetched"], "zt", len(zt), "zb", len(zb), "dt", len(dt), "qdate",
      out.get("zt_qdate"), out.get("zb_qdate"), out.get("dt_qdate"),
      "err", out.get("zt_err"), out.get("zb_err"), out.get("dt_err"))
print("连板分布", dict(sorted(Counter(x["lbc"] for x in zt).items())))
print("二板加", sum(1 for x in zt if x["lbc"] >= 2),
      "炸板率", round(len(zb) / (len(zt) + len(zb)), 4) if (zt or zb) else None)
print("zt_top", [(x["n"], x["lbc"], x.get("hybk"), round(x.get("zdp", 0), 2)) for x in sorted(zt, key=lambda y: -y["lbc"])[:10]])
print("zb_top", [(x["n"], round(x["zdp"], 2), x.get("hybk")) for x in sorted(zb, key=lambda y: y["zdp"])[:12]])
print("hy_cnt", Counter(x.get("hybk") for x in zt).most_common(10))
print("zb_hy", Counter(x.get("hybk") for x in zb).most_common(10))
print("dt_all", [(x["n"], round(x.get("zdp", 0), 2)) for x in dt])
print("午后新封(>=13:00)", sum(1 for x in zt if str(x.get("fbt", "")) >= "130000"))
print("新封明细", [(x["n"], x["lbc"], x.get("hybk"), x.get("fbt")) for x in sorted(zt, key=lambda y: str(y.get("fbt"))) if str(x.get("fbt")) >= "130000"])

# ticks 广度
rows_t = []
with open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") as f:
    for ln in f:
        try:
            rows_t.append(json.loads(ln))
        except Exception:
            pass
last = rows_t[-1]
rr = last["rows"]
pcts = [r["pct"] for r in rr if isinstance(r.get("pct"), (int, float))]
print("=== ticks 末帧", last["ts"], "n", len(rr), "均", round(sum(pcts) / len(pcts), 2),
      "红", sum(1 for p in pcts if p > 0), "绿", sum(1 for p in pcts if p < 0),
      "贴板>=9.6", sum(1 for p in pcts if p >= 9.6), "破-3", sum(1 for p in pcts if p <= -3),
      "破-8", sum(1 for p in pcts if p <= -8))
print("pos in ticks", [r["name"] for r in rr if r["code"] in ("600299", "600259", "603906", "002292")])
