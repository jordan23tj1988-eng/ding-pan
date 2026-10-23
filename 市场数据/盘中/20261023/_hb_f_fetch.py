# -*- coding: utf-8 -*-
"""hb-f 14:45 尾盘深场B 取数: 腾讯实时(持仓+观察+指数) + 东财 ZT/ZB/DT 三池(date=20261023)"""
import json, urllib.request, os, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
DATE = "20261023"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

H = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}
codes = ",".join([
    "sh603370",              # 在持
    "sz002242", "sz002639",  # 今日已清出（口径样本）
    "sz002724", "sh603278",  # 6板高位双钉
    "sz002696", "sz002520", "sh600202", "sh601091", "sz002388",
    "sz002076", "sz001239", "sh601999", "sz000059", "sz001368",
    "sz002913", "sz002811", "sz002578", "sh600293", "sz003021",
    "sh000001", "sz399001", "sz399006",
])
url = "https://qt.gtimg.cn/q=" + codes
raw = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=20).read().decode("gbk", "replace")
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
    rows[key] = {"code": f[2], "name": f[1], "px": float(f[3]) if f[3] else None,
                 "pre": float(f[4]) if f[4] else None, "open": float(f[5]) if f[5] else None,
                 "pct": float(f[32]) if f[32] else None, "high": float(f[33]) if f[33] else None,
                 "low": float(f[34]) if f[34] else None,
                 "amt_wan": float(f[37]) if f[37] else None,
                 "vol_shou": float(f[36]) if f[36] else None,
                 "bid1": f[9], "ask1": f[19], "t": f[30],
                 "limit_up": f[47] if len(f) > 47 and f[47] else None,
                 "limit_dn": f[48] if len(f) > 48 and f[48] else None}
json.dump({"fetched": NOW, "rows": rows}, open(os.path.join(D, "_hb_f_quote_1445.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("=== 腾讯实时", NOW, "===")
for k, v in rows.items():
    print(k, v["name"], v["px"], "%+.2f%%" % (v["pct"] or 0), "hi", v["high"], "lo", v["low"],
          "pre", v["pre"], "zt", v["limit_up"], "dt", v["limit_dn"], "t", v["t"])


def pool(kind, extra_q, sort):
    u = ("https://push2ex.eastmoney.com/getTopic%s?ut=7eea3edcaed734bea9cbfc24409ed989"
         "&dpt=wz.ztzt&Pageindex=0&pagesize=400&sort=%s&date=%s%s" % (kind, sort, DATE, extra_q))
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=20).read().decode("utf-8"))
    d = j.get("data") or {}
    return d.get("pool") or [], (d.get("tc"), j.get("rc"))

zt, m1 = pool("ZTPool", "", "fbt%3Aasc")
zb, m2 = pool("ZBPool", "", "fbt%3Aasc")
dt_fbt, m3 = pool("DTPool", "", "fbt%3Aasc")
dt_zdp, m4 = pool("DTPool", "", "zdp%3Aasc")
dt_fund, m5 = pool("DTPool", "", "fund%3Aasc")
tp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
out = {"fetched": tp, "date": DATE, "zt": zt, "zb": zb, "dt": dt_fund or dt_zdp or dt_fbt,
       "dt_sources": {"fbt": [len(dt_fbt), m3], "zdp": [len(dt_zdp), m4], "fund": [len(dt_fund), m5]},
       "meta": {"zt": m1, "zb": m2}}
json.dump(out, open(os.path.join(D, "_hb_f_pools_1445.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n=== 三池", tp, "===")
print("涨停 tc=%s pool=%d | 炸板 tc=%s pool=%d | 跌停 fbt tc=%s/pool=%d, zdp tc=%s/pool=%d, fund tc=%s/pool=%d"
      % (m1[0], len(zt), m2[0], len(zb), m3[0], len(dt_fbt), m4[0], len(dt_zdp), m5[0], len(dt_fund)))
lb = {}
for p in zt:
    lb[p.get("lbc", 0)] = lb.get(p.get("lbc", 0), 0) + 1
print("连板分布", dict(sorted(lb.items())))
from collections import Counter
print("涨停行业Top", Counter([p.get("hybk") for p in zt]).most_common(8))
print("涨停:", [(p.get("c"), p.get("n"), p.get("lbc")) for p in zt])
print("炸板:", [(p.get("c"), p.get("n"), p.get("zbc")) for p in zb])
print("跌停:", [(p.get("c"), p.get("n")) for p in (dt_fund or dt_zdp or dt_fbt)])
if zt or zb:
    print("炸板率 = %d/(%d+%d) = %.4f" % (len(zb), len(zt), len(zb), len(zb) / (len(zt) + len(zb))))
