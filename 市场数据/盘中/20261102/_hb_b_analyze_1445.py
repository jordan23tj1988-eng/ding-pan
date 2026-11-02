# -*- coding: utf-8 -*-
"""深场B 14:45 读数：池内广度/时序、2分钟跳水窗、持仓与关键票轨迹。只读，不改任何生产件。"""
import json, os
from datetime import datetime

D = r"D:\股票数据\市场数据"
F = os.path.join(D, "盘中", "20261102", "realtime_ticks.jsonl")
frames = []
for line in open(F, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("phase") == "continuous" and d.get("rows"):
        frames.append(d)
print("FRAMES", len(frames), "FIRST", frames[0]["ts"], "LAST", frames[-1]["ts"])

def p2t(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

# 间隔
mx = 0
for a, b in zip(frames, frames[1:]):
    g = (p2t(b["ts"]) - p2t(a["ts"])).total_seconds()
    mx = max(mx, g)
print("MAX_GAP_SEC", mx)

last = frames[-1]
rows = last["rows"]
print("POOL_DATE", last["pool_date"], "N", last["n"], "STALE", last["pool_stale"], "SRC", last["src"])
red = sum(1 for r in rows if r.get("pct", 0) > 0)
green = sum(1 for r in rows if r.get("pct", 0) < 0)
flat = sum(1 for r in rows if r.get("pct", 0) == 0)
up97 = sum(1 for r in rows if r.get("pct", 0) >= 9.7)
dn3 = sum(1 for r in rows if r.get("pct", 0) <= -3)
avg = sum(r.get("pct", 0) for r in rows) / len(rows)
print("LAST_BREADTH red=%d green=%d flat=%d up>=9.7=%d dn<=-3=%d avg=%.2f" % (red, green, flat, up97, dn3, avg))

def snap(hhmm):
    for fr in frames:
        if fr["ts"][11:16] == hhmm:
            rs = fr["rows"]
            a = sum(r.get("pct", 0) for r in rs) / len(rs)
            return dict(ts=fr["ts"], avg=round(a, 2),
                        red=sum(1 for r in rs if r.get("pct", 0) > 0),
                        green=sum(1 for r in rs if r.get("pct", 0) < 0),
                        dn3=sum(1 for r in rs if r.get("pct", 0) <= -3),
                        up97=sum(1 for r in rs if r.get("pct", 0) >= 9.7))
    return None

print("SNAPS", json.dumps({k: snap(k) for k in ("09:31", "10:30", "11:00", "13:00", "13:32", "14:00", "14:30", "14:36", "14:46")}, ensure_ascii=False))

# 2分钟跳水窗（相邻两帧≈120s）
def window_drops(start="14:30"):
    out = []
    for i in range(len(frames) - 2):
        f0, f2 = frames[i], frames[i + 2]
        if f0["ts"][11:16] < start:
            continue
        m0 = {r["code"]: r.get("pct", 0) for r in f0["rows"]}
        hits = []
        for r in f2["rows"]:
            c = r["code"]
            if c in m0 and r.get("pct", 0) - m0[c] <= -3:
                hits.append((c, r.get("name"), round(m0[c], 2), round(r.get("pct", 0), 2)))
        out.append(dict(t2=f2["ts"], n_hit=len(hits), hits=hits[:6]))
    return out

wd = window_drops("14:30")
print("DROP_WINDOWS_1430 total", len(wd), "max_hit", max((w["n_hit"] for w in wd), default=0))
for w in wd:
    if w["n_hit"] >= 2:
        print("DROP_WIN", json.dumps(w, ensure_ascii=False))
# 单票最大回撤
worst = None
m0 = {r["code"]: r for r in frames[0]["rows"]}
mm = {r["code"]: r for r in frames[-1]["rows"]}
tr = {}
for fr in frames:
    for r in fr["rows"]:
        t = tr.setdefault(r["code"], [])
        t.append((fr["ts"], r.get("pct", 0)))
# 自 14:30 起最大跌幅票
base = None
for fr in frames:
    if fr["ts"][11:16] == "14:30":
        base = {r["code"]: r.get("pct", 0) for r in fr["rows"]}
        break
if base:
    diffs = sorted(((mm[c].get("pct", 0) - base.get(c, 0), c, mm[c].get("name")) for c in mm if c in base), key=lambda x: x[0])[:5]
    print("SINCE_1430_WORST", json.dumps(diffs, ensure_ascii=False))

# 重点票轨迹
KEYS = ("603037", "603533", "601188", "002365", "001287", "001219", "000995", "301132", "601083", "301520")
for c in KEYS:
    series = [(ts[11:16], p) for ts, p in tr.get(c, []) if ts[11:16] in ("09:31", "10:30", "11:00", "13:00", "13:32", "14:30", "14:36", "14:46")]
    now = mm.get(c)
    if now is None:
        print("KEY", c, "NOT_IN_POOL", "series", series)
        continue
    print("KEY", c, now.get("name"),
          "now=%s pct=%.2f open=%s high=%s low=%s amt=%s" % (
              now.get("latest"), now.get("pct", 0), now.get("open"), now.get("high"),
              now.get("low"), now.get("amount")), "series", series)
