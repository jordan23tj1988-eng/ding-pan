# -*- coding: utf-8 -*-
"""hb-f 14:45 分析: 池帧breadth + 5分钟跌幅/题材簇扫描 + 603370 尾段分时 + 三池结构"""
import json, os, statistics, urllib.request
from datetime import datetime as _dt

D = r"D:\股票数据\市场数据\盘中\20261023"
TICKS = os.path.join(D, "realtime_ticks.jsonl")
CUT = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

frames = []
with open(TICKS, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            frames.append(json.loads(line))
        except Exception:
            pass
fr = [x for x in frames if x["ts"] <= CUT]
print("决断时点 %s | 全帧 %d | 决断前帧 %d | 首 %s | 末 %s | 末帧龄 %.0fs" % (
    CUT, len(frames), len(fr), fr[0]["ts"], fr[-1]["ts"],
    (_dt.strptime(CUT, "%Y-%m-%d %H:%M:%S") - _dt.strptime(fr[-1]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()))
gaps = [(_dt.strptime(fr[i]["ts"], "%Y-%m-%d %H:%M:%S") - _dt.strptime(fr[i-1]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() for i in range(1, len(fr))]
print("帧间隔 中位 %.0fs 最大 %.0fs" % (statistics.median(gaps), max(gaps)))

def stats(f):
    pct = [r["pct"] for r in f["rows"]]
    return {"ts": f["ts"], "n": len(pct), "median": round(statistics.median(pct), 2),
            "mean": round(sum(pct) / len(pct), 2), "up": sum(1 for p in pct if p > 0),
            "dn": sum(1 for p in pct if p < 0), "flat": sum(1 for p in pct if p == 0),
            "zt": sum(1 for p in pct if p >= 9.8), "dt": sum(1 for p in pct if p <= -9.8)}

print("\n=== 昨涨停池(33票) 当前 ===", json.dumps(stats(fr[-1]), ensure_ascii=False))
for tag in ["09:45", "10:33", "11:30", "13:30", "14:00", "14:31"]:
    cand = [f for f in fr if f["ts"][11:16] >= tag]
    if cand:
        print(tag, "→实取", json.dumps(stats(cand[0]), ensure_ascii=False))

pct = sorted(r["pct"] for r in fr[-1]["rows"])
print("分位: min %.2f p25 %.2f p50 %.2f p75 %.2f max %.2f" % (
    pct[0], pct[len(pct)//4], pct[len(pct)//2], pct[3*len(pct)//4], pct[-1]))

# 603370 全日序列表 (每帧)
S = "603370"
seq = [(f["ts"], next((r["latest"], r["pct"], r["high"], r["low"]) for r in f["rows"] if r["code"] == S)) for f in fr]
print("\n=== %s 池帧序列(每10帧抽) ===" % S)
for ts, v in seq[::10]:
    print(ts, v)
print("末帧", seq[-1])
lows = min(v[0] for _, v in seq); highs = max(v[0] for _, v in seq)
print("池帧区间 低 %.2f 高 %.2f" % (lows, highs))

# 5分钟滚动跌幅 (每帧对 >=240s 前帧)
def scan5():
    worst = []
    for i, f in enumerate(fr):
        cur = {r["code"]: r["pct"] for r in f["rows"]}
        ref = None
        for j in range(i - 1, -1, -1):
            dt = (_dt.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") - _dt.strptime(fr[j]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()
            if dt >= 240:
                ref = fr[j]; break
        if ref is None:
            continue
        rp = {r["code"]: r["pct"] for r in ref["rows"]}
        drops = [(c, round(cur[c] - rp[c], 2)) for c in cur if c in rp]
        worst.append((f["ts"], [d for d in drops if d[1] <= -2.0], drops))
    return worst

w = scan5()
print("\n=== 5分钟跌幅 <= -2%% 扫描 (最近40分钟, 全簇) ===")
for ts, hits, _ in w:
    if ts >= "2026-10-23 14:05:00" and hits:
        print(ts, hits)
mx = max((len(h[1]) for h in w), default=0)
print("全窗最大簇", mx)
for ts, hits, _ in w:
    if len(hits) == mx and mx >= 3:
        print("  簇出现", ts, hits)
# 603370 专属最小5分钟变化
d370 = [(ts, dict((c, d) for c, d in drops).get(S)) for ts, hits, drops in w]
tail = [(ts, d) for ts, d in d370 if ts >= "2026-10-23 14:00:00" and d is not None]
print("\n603370 14:00后 5分钟变化 min %.2f @ %s | max %.2f" % (
    min(d for _, d in tail), min(tail, key=lambda x: x[1])[0], max(d for _, d in tail)))
print("603370 最近6个5分钟读数", tail[-6:])

# 603370 分时
def minute(code):
    u = "https://web.ifzq.gtimg.cn/appstock/app/minute/query?code=" + code
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=15).read().decode("utf-8"))
    d = j.get("data") or {}
    if isinstance(d, list):
        d = {}
    d = d.get(code) or {}
    inner = d.get("data") or {}
    m = inner.get("data") if isinstance(inner, dict) else inner
    return (m or []), (d.get("qt") or {})

m, qt = minute("sh"+S)
json.dump({"fetched": CUT, "code": S, "minute": m, "qt": qt}, open(os.path.join(D, "_hb_f_minute_603370.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n=== %s 分时 %d 点 末 %s ===" % (S, len(m), m[-1] if m else None))
print("尾段", m[-12:])
hi = max([float(x.split()[1]) for x in m], default=0); lo = min([float(x.split()[1]) for x in m], default=0)
print("分时高 %.2f 低 %.2f" % (hi, lo))
