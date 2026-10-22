# -*- coding: utf-8 -*-
"""hb-d 13:30 段: 池帧新鲜度 + 004242 逐帧 + 题材批量跳水扫描"""
import json, statistics, datetime

TICKS = r"D:\股票数据\市场数据\盘中\20261022\realtime_ticks.jsonl"
fr = [json.loads(l) for l in open(TICKS, encoding="utf-8") if l.strip()]
ts = [f["ts"] for f in fr]
print("帧数", len(fr), "窗口", ts[0], "~", ts[-1])

# 间隔
def P(s): return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
gaps = [(P(ts[i+1]) - P(ts[i])).total_seconds() for i in range(len(ts)-1)]
mx = max(gaps); mi = gaps.index(mx)
print("最大间隔 %.0fs @ %s -> %s" % (mx, ts[mi], ts[mi+1]))
# 下午帧 (>=13:00)
pm = [f for f in fr if P(f["ts"]).hour >= 13]
print("下午帧数", len(pm), pm[0]["ts"], "~", pm[-1]["ts"])

r = lambda f: {x["code"]: x for x in f["rows"]}
last = r(fr[-1])

# 002242 逐帧
s = [(f["ts"], r(f).get("002242", {})) for f in fr]
s = [(t, v) for t, v in s if v]
print("\n=== 002242 九阳股份 逐帧(11:00后) ===")
for t, v in s:
    if P(t).hour >= 11:
        print(t, v["latest"], "%+.2f%%" % v["pct"], "hi", v["high"], "lo", v["low"])
pm_lows = [(t, v["low"], v["latest"]) for t, v in s if P(t).hour >= 13]
print("下午最低价(帧内 low 字段):", min(x[1] for x in pm_lows) if pm_lows else None)
print("下午最低 latest:", min(x[2] for x in pm_lows) if pm_lows else None)
# 5分钟跌幅>=2%
print("\n=== 002242 5分钟跌幅检查(下午) ===")
px = [(t, v["latest"]) for t, v in s if P(t).hour >= 13]
for i in range(len(px)):
    for j in range(i+1, len(px)):
        dt = (P(px[j][0]) - P(px[i][0])).total_seconds()
        if dt > 360: break
        chg = (px[j][1] / px[i][1] - 1) * 100
        if chg <= -2:
            print("  DROP", px[i], "->", px[j], "%.2f%%" % chg)

# 池内统计
def stats(f):
    v = [x["pct"] for x in f["rows"]]
    return dict(med=round(statistics.median(v), 2), mean=round(statistics.mean(v), 2),
                up=sum(1 for p in v if p > 0), dn=sum(1 for p in v if p < 0),
                flat=sum(1 for p in v if p == 0),
                ge9=sum(1 for p in v if p >= 9), le9=sum(1 for p in v if p <= -9),
                ge5=sum(1 for p in v if p >= 5), le5=sum(1 for p in v if p <= -5))
print("\n=== 池内(末帧) ===", stats(fr[-1]))
print("=== 池内(11:03 附近) ===")
for f in fr:
    if f["ts"].startswith("2026-10-22 11:03"):
        print(f["ts"], stats(f))
print("=== 池内(13:00 首帧) ===", pm[0]["ts"], stats(pm[0]))

# 题材批量跳水: 相邻 <=3 帧内 跌幅>=3pp 的票数
print("\n=== 批量跳水扫描(下午, 窗口<=4帧, 单票跌幅>=3pp) ===")
codes = list(last.keys())
best = []
for i in range(len(pm)):
    for j in range(i+1, min(i+5, len(pm))):
        a, b = r(pm[i]), r(pm[j])
        dive = []
        for c in codes:
            if c in a and c in b and a[c]["pct"] - b[c]["pct"] >= 3:
                dive.append((c, b[c]["name"], round(a[c]["pct"], 2), round(b[c]["pct"], 2)))
        if len(dive) >= 2:
            best.append((len(dive), pm[i]["ts"], pm[j]["ts"], dive))
best.sort(key=lambda x: -x[0])
for b in best[:6]:
    print(b[0], b[1], "->", b[2], b[3])
if not best:
    print("  无 >=2 只簇")

# 下午跌幅最大10只
print("\n=== 下午以来跌幅最大 10 只(13:00首帧->末帧) ===")
a, b = r(pm[0]), r(pm[-1])
ch = sorted(((round(a[c]["pct"] - b[c]["pct"], 2), c, b[c]["name"], a[c]["pct"], b[c]["pct"])
             for c in codes if c in a and c in b), reverse=True)[:10]
for x in ch:
    print("  跌%.2fpp %s %s %+.2f -> %+.2f" % x)
