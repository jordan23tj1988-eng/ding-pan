# -*- coding: utf-8 -*-
"""hb-d 午后延续段判定: 只用 <=13:30 留档 tick。只读分析。"""
import json, os, datetime as dt, glob

ROOT = r"D:\股票数据\市场数据"
TODAY = "20260921"
D = os.path.join(ROOT, "盘中", TODAY)
NOW = dt.datetime(2026, 9, 21, 13, 30, 0)

rows = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
rows = [r for r in rows if dt.datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S") <= NOW]
print("留档 tick(<=13:30) 条数=%d 首=%s 末=%s" % (len(rows), rows[0]["ts"], rows[-1]["ts"]))

def snap(r):
    return {x["code"]: x for x in r["rows"]}

last = snap(rows[-1])
prev_map = {r["ts"]: snap(r) for r in rows}

# 1) 池内概况(13:30 时点)
pcts = [v["pct"] for v in last.values()]
up = len([p for p in pcts if p > 0]); dn = len([p for p in pcts if p < 0])
zt = [v for v in last.values() if v["pct"] >= 9.8]
print("\n[池内概况@13:30] n=%d 涨=%d 跌=%d 中位=%.2f%% 均值=%.2f%%" % (len(pcts), up, dn, sorted(pcts)[len(pcts)//2], sum(pcts)/len(pcts)))
print("  涨停(>=9.8%%)=%d %s" % (len(zt), [(v["code"], v["name"], v["pct"]) for v in zt]))
print("  跌幅前5:", [(v["name"], v["pct"]) for v in sorted(last.values(), key=lambda x: x["pct"])[:5]])

# 2) 午后段(13:00 首 tick -> 13:30 末) 变化
af = [r for r in rows if dt.datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S").hour >= 13]
if af:
    a0, a1 = snap(af[0]), snap(af[-1])
    print("\n[午后段 %s -> %s]" % (af[0]["ts"], af[-1]["ts"]))
    d = sorted(((a1[c]["pct"] - a0[c]["pct"], a0[c]["name"]) for c in a0 if c in a1), reverse=True)
    print("  池内 pct 变化: 改善前3=%s 恶化前5=%s" % (d[:3], d[-5:]))
    print("  均值 pct: %.2f%% -> %.2f%% (Δ%+.2f)" % (sum(x["pct"] for x in a0.values())/len(a0), sum(x["pct"] for x in a1.values())/len(a1), sum(x["pct"] for x in a1.values())/len(a1)-sum(x["pct"] for x in a0.values())/len(a0)))

# 3) 2分钟窗口批量跳水(>=3只 跌>=3%) 全时段扫描
print("\n[2分钟窗口批量跳水扫描(池内)]")
hits = []
for i in range(len(rows)-2):
    t0 = dt.datetime.strptime(rows[i]["ts"], "%Y-%m-%d %H:%M:%S")
    for j in range(i+1, len(rows)):
        t1 = dt.datetime.strptime(rows[j]["ts"], "%Y-%m-%d %H:%M:%S")
        if (t1-t0).total_seconds() > 120: break
        s0, s1 = snap(rows[i]), snap(rows[j])
        n = len([c for c in s0 if c in s1 and (s1[c]["pct"]-s0[c]["pct"]) <= -3.0])
        if n >= 3: hits.append((rows[i]["ts"], rows[j]["ts"], n))
print("  命中=%d" % len(hits), hits[:6])

# 4) 单票 2 分钟急跌 >=3%
print("\n[单票2分钟急跌>=3%]")
fast = []
for i in range(len(rows)-1):
    t0 = dt.datetime.strptime(rows[i]["ts"], "%Y-%m-%d %H:%M:%S")
    for j in range(i+1, len(rows)):
        t1 = dt.datetime.strptime(rows[j]["ts"], "%Y-%m-%d %H:%M:%S")
        if (t1-t0).total_seconds() > 120: break
        s0, s1 = snap(rows[i]), snap(rows[j])
        for c in s0:
            if c in s1 and (s1[c]["pct"]-s0[c]["pct"]) <= -3.0:
                fast.append((rows[i]["ts"], s1[c]["name"], round(s1[c]["pct"]-s0[c]["pct"], 2)))
print("  n=%d" % len(fast), fast[-8:])

# 5) 冲高回落(相对当日最高回撤>=5%)
print("\n[当日高点回撤>=5%]")
for v in sorted(last.values(), key=lambda x: (x["latest"]-x["high"])/x["high"]):
    dd = (v["latest"]-v["high"])/v["high"]*100
    if dd <= -5:
        print("  %s %-8s high=%.2f latest=%.2f 回撤=%+.2f%% pct=%+.2f%%" % (v["code"], v["name"], v["high"], v["latest"], dd, v["pct"]))

# 6) 其他真源新鲜度
print("\n[真源新鲜度]")
for p in ["盘中作战判定流水", os.path.join(ROOT, "_学习", "_模拟盘", "盘中作战", "判断流水.jsonl")]:
    pass
jf = os.path.join(ROOT, "_学习", "_模拟盘", "盘中作战", "判断流水.jsonl")
print("  判断流水.jsonl: %s" % dt.datetime.fromtimestamp(os.path.getmtime(jf)))
ls = [l for l in open(jf, encoding="utf-8") if l.strip()]
print("  末行: %s" % ls[-1][:300])
print("  今日(20260921)行数=%d" % len([l for l in ls if "2026-09-21" in l[:40] or "20260921" in l[:60]]))
