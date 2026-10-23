# -*- coding: utf-8 -*-
"""hb-e 14:30 分析: 池帧breadth + 5分钟跌幅/题材簇扫描 + 603370分时尾段 + 涨停结构对比"""
import json, os, statistics
from datetime import datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
TICKS = os.path.join(D, "realtime_ticks.jsonl")

frames = []
with open(TICKS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            j = json.loads(line)
        except Exception:
            continue
        frames.append(j)
print("帧数 %d  首 %s  末 %s" % (len(frames), frames[0]["ts"], frames[-1]["ts"]))

# 只取决断时点(14:31:15)之前的帧
cut = "2026-10-23 14:31:15"
fr = [x for x in frames if x["ts"] <= cut]
print("决断前帧 %d，末帧 %s，末帧龄(秒) %.0f" % (
    len(fr), fr[-1]["ts"],
    (datetime.strptime(cut, "%Y-%m-%d %H:%M:%S") - datetime.strptime(fr[-1]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()))

def stats(f):
    rows = f["rows"]
    pct = [r["pct"] for r in rows]
    return {"ts": f["ts"], "n": len(rows), "median": round(statistics.median(pct), 2),
            "mean": round(sum(pct) / len(pct), 2), "up": sum(1 for p in pct if p > 0),
            "dn": sum(1 for p in pct if p < 0), "flat": sum(1 for p in pct if p == 0),
            "zt": sum(1 for p in pct if p >= 9.8), "dt": sum(1 for p in pct if p <= -9.8)}

last = stats(fr[-1])
print("\n=== 昨涨停池(33票) 当前 ===", json.dumps(last, ensure_ascii=False))
# 历史对比帧: 13:30 / 10:33 / 09:45 附近
for tag in ["09:45", "10:33", "13:30", "14:00"]:
    cand = [f for f in fr if f["ts"][11:16] >= tag]
    if cand:
        print(tag, "→实取", json.dumps(stats(cand[0]), ensure_ascii=False))

# 分位分布
pct = sorted(r["pct"] for r in fr[-1]["rows"])
print("分位: min %.2f p25 %.2f p50 %.2f p75 %.2f max %.2f" % (
    pct[0], pct[len(pct) // 4], pct[len(pct) // 2], pct[3 * len(pct) // 4], pct[-1]))

# 5分钟(≥240s 前帧)跌幅扫描 + 题材簇
by_ts = {f["ts"]: f for f in fr}
tslist = [f["ts"] for f in fr]
worst = []
for i, f in enumerate(fr):
    cur = {r["code"]: r["pct"] for r in f["rows"]}
    # 找 ≥240 秒前最近帧
    ref = None
    for j in range(i - 1, -1, -1):
        dt = (datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") - datetime.strptime(fr[j]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()
        if dt >= 240:
            ref = {r["code"]: r["pct"] for r in fr[j]["rows"]}
            break
    if not ref:
        continue
    diffs = {c: cur[c] - ref[c] for c in cur if c in ref}
    worst.append((f["ts"], min(diffs.items(), key=lambda kv: kv[1]), sorted(diffs.items(), key=lambda kv: kv[1])[:3]))
if worst:
    mn = min(worst, key=lambda x: x[1][1])
    print("\n全窗最大5分钟跌幅: %s %s" % (mn[0], mn[1]))
    print("最近30分钟最差5分钟跌:", [ (t, c) for t, c, _ in worst[-30:] ][:3])
    print("最近(14:25后)最差3只:", min(worst[-10:], key=lambda x: x[1][1]))

# 603370 分时
mj = json.load(open(os.path.join(D, "_hb_e_minute_603370.json"), encoding="utf-8"))
mt = mj["minute"]
print("\n=== 603370 分时 %d 点 末 %s ===" % (len(mt), mt[-1]))
if mt:
    seg = mt[-40:]
    print("尾段40点:", [x.split()[0] + " " + x.split()[1] for x in seg if len(x.split()) >= 2][::4])
    px = [(x.split()[0], float(x.split()[1])) for x in mt if len(x.split()) >= 2]
    print("分时最高 %.2f @%s  最低 %.2f @%s" % (max(px, key=lambda y: y[1])[1], max(px, key=lambda y: y[1])[0],
                                            min(px, key=lambda y: y[1])[1], min(px, key=lambda y: y[1])[0]))
    # 14:00后 5分钟跌幅
    tail = [(t, p) for t, p in px if t >= "1400"]
    drops = []
    for i in range(len(tail)):
        for j in range(i):
            drops.append((tail[i][0], (tail[i][1] - tail[j][1]) / tail[j][1] * 100))
    print("14:00后最大回撤幅度 %.2f%%" % min(d_ for _, d_ in drops))

# 涨停池结构: 板位分布 + 行业TOP
pools = json.load(open(os.path.join(D, "_hb_e_pools_1430.json"), encoding="utf-8"))
zt = pools["zt"]
from collections import Counter
lbc = Counter(p.get("lbc", 0) for p in zt)
hy = Counter((p.get("hybk") or "?") for p in zt)
print("\n=== 涨停 %d: 板位 %s ===" % (len(zt), dict(sorted(lbc.items()))))
print("行业TOP8:", hy.most_common(8))
print("跌幅前列(昨涨停池):", sorted(fr[-1]["rows"], key=lambda r: r["pct"])[:6])
print("涨幅前列(昨涨停池):", [(r["code"], r["name"], r["pct"]) for r in sorted(fr[-1]["rows"], key=lambda r: -r["pct"])[:6]])
print("跌停 tc:", pools["tc"], "明细%d/%d" % (pools["dt_len_fbt"], pools["dt_len_fund"]))
