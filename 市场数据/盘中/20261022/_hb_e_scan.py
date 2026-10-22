# -*- coding: utf-8 -*-
"""hb-e 池帧分析: 002242 新低/5分钟跌幅 + 题材批量跳水扫描 + 池内宽度(仅用 14:31 前已落盘帧)"""
import json, datetime

D = r"D:\股票数据\市场数据\盘中\20261022"
F = D + r"\realtime_ticks.jsonl"
CUT = None  # 决断时点: 取所有已落盘帧

frames = []
for l in open(F, encoding="utf-8"):
    l = l.strip()
    if not l:
        continue
    d = json.loads(l)
    frames.append(d)

print("总帧数", len(frames), "窗口", frames[0]["ts"], "~", frames[-1]["ts"], "n", frames[-1]["n"],
      "pool_date", frames[-1]["pool_date"], "stale", frames[-1]["pool_stale"])

def t(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

# 最大间隔
mx = (0, None)
for a, b in zip(frames, frames[1:]):
    gap = (t(b["ts"]) - t(a["ts"])).total_seconds()
    if gap > mx[0]:
        mx = (gap, a["ts"] + "→" + b["ts"])
print("最大间隔 %ds %s; 末帧龄 %.0fs" % (mx[0], mx[1], (datetime.datetime.now() - t(frames[-1]["ts"])).total_seconds()))

rows_by_ts = [(f["ts"], {r["code"]: r for r in f["rows"]}) for f in frames]

# --- 002242 轨迹 ---
print("\n=== 002242 轨迹(尾段) ===")
tr = [(ts, m.get("002242")) for ts, m in rows_by_ts]
tr = [(ts, r) for ts, r in tr if r]
for ts, r in tr[-25:]:
    print(ts, r["latest"], "%+.2f%%" % r["pct"])
px = [r["latest"] for _, r in tr]
print("池帧内 002242 min=%.2f max=%.2f 末=%.2f 首=%.2f" % (min(px), max(px), px[-1], px[0]))
lo = min(px)
print("创新低时点:", [ts for ts, r in tr if r["latest"] == lo])

# 5分钟跌幅(滚动 5 分钟窗口内最大跌幅)
print("\n=== 002242 5分钟滚动最大跌幅(尾段 60 帧) ===")
worst = []
for i in range(len(tr)):
    ts_i, r_i = tr[i]
    # 找 5 分钟内最早帧
    j = i
    while j > 0 and (t(ts_i) - t(tr[j - 1][0])).total_seconds() <= 300:
        j -= 1
    hi = max(x[1]["latest"] for x in tr[j:i + 1])
    drop = (r_i["latest"] / hi - 1) * 100
    worst.append((drop, ts_i, hi, r_i["latest"]))
worst.sort()
for w in worst[:5]:
    print("5min跌幅 %.2f%% @%s (窗口高 %.2f → %.2f)" % w)
# 下午段最大
aft = [w for w in worst if w[1] >= "2026-10-22 13:00:00"]
aft.sort()
print("下午段最大5分钟跌幅:")
for w in aft[:3]:
    print("  %.2f%% @%s (%.2f→%.2f)" % w)

# --- 题材批量跳水: 相邻 ≤4 帧窗口内单票跌≥3pp 的簇 ---
print("\n=== 题材批量跳水扫描(13:00 后, 窗口≤4帧) ===")
sel = [(ts, m) for ts, m in rows_by_ts if ts >= "2026-10-22 13:00:00"]
best = []
for i, (ts_i, m_i) in enumerate(sel):
    j = max(0, i - 3)
    for code in m_i:
        p0 = sel[j][1].get(code, {}).get("pct")
        p1 = m_i[code].get("pct")
        if p0 is None or p1 is None:
            continue
        if p0 - p1 >= 3.0:
            best.append((ts_i, code, m_i[code]["name"], p0, p1))
from collections import defaultdict
c = defaultdict(list)
seen = set()
for ts_i, code, name, p0, p1 in best:
    if (ts_i, code) in seen:
        continue
    seen.add((ts_i, code))
    c[ts_i].append((code, name, p0, p1))
top = sorted(c.items(), key=lambda kv: -len(kv[1]))[:6]
for ts_i, lst in top:
    print(ts_i, "簇大小", len(lst), lst[:8])

# --- 池内宽度(末帧 vs 13:33 帧) ---
def stat(m):
    v = [r["pct"] for r in m.values()]
    v.sort()
    n = len(v)
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    return {"n": n, "median": round(med, 2), "mean": round(sum(v) / n, 2),
            "up": sum(1 for x in v if x > 0), "down": sum(1 for x in v if x < 0),
            "ge9": sum(1 for x in v if x >= 9), "le_9": sum(1 for x in v if x <= -9)}
print("\n=== 池内宽度 ===")
last = rows_by_ts[-1][1]
print("末帧", rows_by_ts[-1][0], stat(last))
# 找 13:33 附近帧
ref = [x for x in rows_by_ts if x[0] <= "2026-10-22 13:33:10"][-1]
print("13:33基准", ref[0], stat(ref[1]))
ref11 = [x for x in rows_by_ts if x[0] <= "2026-10-22 11:05:00"][-1]
print("11:05基准", ref11[0], stat(ref11[1]))

# 持仓票在池内?
for c_ in ("002242", "002639", "002076", "001239"):
    r = last.get(c_)
    print(c_, (r["name"], r["latest"], r["pct"], "hi", r["high"], "lo", r["low"]) if r else "不在池内50票")
