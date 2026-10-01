# -*- coding: utf-8 -*-
"""深场B 14:45 场次分析 — 仅用 ts <= 2026-09-29 14:45:00 的留档 tick(零后视镜)。"""
import json, csv, os, statistics as st

BASE = r"D:\股票数据\市场数据"
D = os.path.join(BASE, "盘中", "20260929")
TICKS = os.path.join(D, "realtime_ticks.jsonl")
POOL = os.path.join(BASE, "20260928", "zt_pool.csv")
CUT = "2026-09-29 14:45:00"

# 池
pool = {}
with open(POOL, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        pool[r["代码"]] = {"name": r["名称"], "ind": r["所属行业"], "lb": int(r["连板数"]),
                           "zb_cnt": int(r["炸板次数"]), "zt_stat": r["涨停统计"]}

def lim_pct(code, name):
    if name.upper().startswith("ST") or "ST" in name.upper():
        return 5.0
    if code.startswith("30") or code.startswith("68"):
        return 20.0
    if code.startswith("4") or code.startswith("8"):
        return 30.0
    return 10.0

frames = []
maxgap = (0, None)
prev = None
for line in open(TICKS, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    if d["ts"] > CUT:
        break
    frames.append(d)
    if prev:
        from datetime import datetime
        g = (datetime.strptime(d["ts"], "%Y-%m-%d %H:%M:%S") - datetime.strptime(prev, "%Y-%m-%d %H:%M:%S")).total_seconds()
        if g > maxgap[0]:
            maxgap = (g, prev + " -> " + d["ts"])
    prev = d["ts"]

print("帧数=%d  首=%s 末=%s  最大间隔=%.0fs @ %s" % (len(frames), frames[0]["ts"], frames[-1]["ts"], maxgap[0], maxgap[1]))
print("pool_stale=%s pool_date=%s" % (frames[-1]["pool_stale"], frames[-1]["pool_date"]))

def stats(fr):
    rows = {r["code"]: r for r in fr["rows"]}
    pcts, feng, chu, zha, dt, red = [], [], [], [], [], 0
    for code, r in rows.items():
        p = pool.get(code)
        if not p:
            continue
        lp = round(r["preClose"] * (1 + lim_pct(code, p["name"]) / 100), 2)
        dn = round(r["preClose"] * (1 - lim_pct(code, p["name"]) / 100), 2)
        pcts.append(r["pct"])
        if r["pct"] > 0:
            red += 1
        if r["latest"] >= lp - 0.005:
            feng.append(code)
        elif r["high"] >= lp - 0.005:
            chu.append(code)
            zha.append(code)
        if r["latest"] <= dn + 0.005:
            dt.append(code)
    return {"n": len(pcts), "med": round(st.median(pcts), 2), "mean": round(sum(pcts) / len(pcts), 2),
            "red": red, "ge5": sum(1 for x in pcts if x >= 5), "le5": sum(1 for x in pcts if x <= -5),
            "feng": len(feng), "chu": len(feng) + len(chu), "zha": len(zha), "dt": len(dt),
            "feng_list": feng, "zha_list": zha, "dt_list": dt, "rows": rows, "pcts": pcts}

def find(ts):
    cand = [f for f in frames if f["ts"] <= ts]
    return cand[-1] if cand else None

timeline = ["2026-09-29 09:59:59", "2026-09-29 10:59:59", "2026-09-29 11:29:59",
            "2026-09-29 13:00:59", "2026-09-29 13:29:59", "2026-09-29 13:59:59",
            "2026-09-29 14:14:59", "2026-09-29 14:29:59", "2026-09-29 14:44:59"]
print("\n=== 时间轴 ===")
for ts in timeline:
    f = find(ts)
    if f:
        s = stats(f)
        print("%s | 中位%6.2f 均值%6.2f 红%2d/33 ≥5%%%2d ≤-5%%%d 封%2d 触%2d 炸未回封%d 跌停%d 炸板率%.1f%%" %
              (f["ts"], s["med"], s["mean"], s["red"], s["ge5"], s["le5"], s["feng"], s["chu"], s["zha"], s["dt"],
               (s["zha"] / s["chu"] * 100) if s["chu"] else 0))

last = find("2026-09-29 14:44:59")
S = stats(last)
print("\n=== 锁定末帧 %s ===" % last["ts"])
print({k: v for k, v in S.items() if k not in ("rows", "pcts", "feng_list", "zha_list", "dt_list")})
print("封板名单:", [(c, pool[c]["name"], pool[c]["lb"], pool[c]["ind"]) for c in S["feng_list"]])
print("炸板未回封:", [(c, pool[c]["name"]) for c in S["zha_list"]])
print("跌停:", [(c, pool[c]["name"], pool[c]["lb"]) for c in S["dt_list"]])

# 尾窗 14:15:00 → 14:45:00
a = find("2026-09-29 14:15:00"); b = last
ra, rb = {r["code"]: r for r in a["rows"]}, {r["code"]: r for r in b["rows"]}
print("\n=== 尾盘窗口 %s → %s ===" % (a["ts"], b["ts"]))
disp = []
for c in pool:
    if c in ra and c in rb:
        disp.append((rb[c]["pct"] - ra[c]["pct"], c, pool[c]["name"], ra[c]["pct"], rb[c]["pct"], pool[c]["ind"], pool[c]["lb"]))
disp.sort()
print("逐票变化 中位=%.2fpp" % st.median([x[0] for x in disp]))
for x in disp[:8] + disp[-8:]:
    print("  %+.2fpp %s %s %.2f→%.2f [%s/%d板]" % x)
print("跌>0.5pp 只数=%d" % sum(1 for x in disp if x[0] < -0.5))
from collections import Counter
print("跌>0.5pp 行业分布:", Counter(x[5] for x in disp if x[0] < -0.5))

# 行业聚合
print("\n=== 行业聚合(锁定末帧, n>=2) ===")
ind = {}
for c in pool:
    if c in rb:
        ind.setdefault(pool[c]["ind"], []).append(rb[c]["pct"])
for k, v in sorted(ind.items(), key=lambda x: -sum(x[1]) / len(x[1])):
    if len(v) >= 2:
        print("  %s n=%d 均值%+.2f" % (k, len(v), sum(v) / len(v)))

# 连板梯队
print("\n=== 连板梯队(按昨日连板数) ===")
lad = {}
for c in pool:
    if c in rb:
        lad.setdefault(pool[c]["lb"], []).append((c, pool[c]["name"], rb[c]["pct"], c in S["feng_list"]))
for k in sorted(lad, reverse=True):
    v = lad[k]
    print("  %d板 x%d 均值%+.2f 封%d: %s" % (k, len(v), sum(x[2] for x in v) / len(v), sum(1 for x in v if x[3]),
          [(x[0], x[1], x[2]) for x in v]))

# 2分钟跌≥3pp 事件 (全窗 + 14:00后)
print("\n=== 2分钟急跌≥3pp 事件 ===")
seq = [f for f in frames]
ev = []
for i in range(len(seq)):
    for j in range(i + 1, len(seq)):
        from datetime import datetime
        t1 = datetime.strptime(seq[i]["ts"], "%Y-%m-%d %H:%M:%S"); t2 = datetime.strptime(seq[j]["ts"], "%Y-%m-%d %H:%M:%S")
        if (t2 - t1).total_seconds() > 180:
            break
        r1 = {r["code"]: r for r in seq[i]["rows"]}; r2 = {r["code"]: r for r in seq[j]["rows"]}
        for c in pool:
            if c in r1 and c in r2 and r1[c]["pct"] - r2[c]["pct"] >= 3:
                ev.append((seq[i]["ts"], seq[j]["ts"], c, pool[c]["name"], r1[c]["pct"], r2[c]["pct"]))
for e in ev:
    print("  ", e)
print("事件数=%d" % len(ev))

# 观察票窗内轨迹
print("\n=== 观察票 ===")
for c in ["600540", "301190", "002912", "603396", "601579"]:
    p = pool.get(c)
    seq_p = []
    for f in frames:
        for r in f["rows"]:
            if r["code"] == c:
                seq_p.append((f["ts"][-8:], r["pct"], r["latest"]))
    if not p:
        print("  %s 非本池(20260928 zt_pool 33只) → 窗内无合法留档价, 不写价" % c)
        continue
    if seq_p:
        print("  %s %s [%s/%d板] 首%s(%+.2f) 末%s(%+.2f) 极值%s↔%s" % (
            c, p["name"], p["ind"], p["lb"], seq_p[0][0], seq_p[0][1], seq_p[-1][0], seq_p[-1][1],
            min(seq_p, key=lambda x: x[1]), max(seq_p, key=lambda x: x[1])))
        lim = [x for x in seq_p if abs(x[1] - (20.0 if c.startswith("30") else 10.0)) < 0.05]
        if lim:
            print("      首次触涨停价于 %s" % lim[0][0])
