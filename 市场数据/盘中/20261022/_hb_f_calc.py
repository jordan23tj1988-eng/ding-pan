# -*- coding: utf-8 -*-
"""hb-f 14:45 深场B 池帧切片: 002242 尾盘 tick 序列 + 5分钟滚动跌幅 + 末日帧宽度"""
import json, os, datetime

D = r"D:\股票数据\市场数据\盘中\20261022"
F = os.path.join(D, "realtime_ticks.jsonl")
frames = []
for line in open(F, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        frames.append(json.loads(line))
    except Exception:
        pass
print("总帧数", len(frames), "首帧", frames[0]["ts"], "末帧", frames[-1]["ts"], "末帧n", frames[-1].get("n"),
      "pool_date", frames[-1].get("pool_date"), "pool_stale", frames[-1].get("pool_stale"));

# 帧间隔
gaps = []
for a, b in zip(frames, frames[1:]):
    ta = datetime.datetime.strptime(a["ts"], "%Y-%m-%d %H:%M:%S")
    tb = datetime.datetime.strptime(b["ts"], "%Y-%m-%d %H:%M:%S")
    gaps.append(((tb - ta).total_seconds(), a["ts"], b["ts"]))
gaps.sort(reverse=True)
print("最大间隔", gaps[:3])

def series(code, start="14:30:00"):
    out = []
    for fr in frames:
        if fr["ts"][11:] < start:
            continue
        for r in fr.get("rows", []):
            if r["code"] == code:
                out.append((fr["ts"], r["latest"], r.get("pct"), r.get("high"), r.get("low")))
    return out

for code in ("002242",):
    s = series(code)
    print("\n=== %s 池帧序列 14:30起 (%d 帧) ===" % (code, len(s)))
    for t, px, pct, hi, lo in s:
        print(t, px, "%+.2f%%" % (pct or 0), "hi", hi, "lo", lo)
    if s:
        # 5分钟滚动跌幅: 每帧 vs 300秒内最早帧
        print("\n--- 5分钟滚动(最早帧基准) ---")
        for i, (t, px, *_ ) in enumerate(s):
            ti = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
            base = None
            for t2, px2, *_ in s[:i + 1]:
                t2d = datetime.datetime.strptime(t2, "%Y-%m-%d %H:%M:%S")
                if (ti - t2d).total_seconds() <= 300:
                    base = (t2, px2)
                    break
            if base:
                print(t, px, "base", base[0], base[1], "chg %+.2f%%" % ((px / base[1] - 1) * 100))

# 末日帧宽度
last = frames[-1]
rows = last.get("rows", [])
pcts = sorted([r["pct"] for r in rows if r.get("pct") is not None])
n = len(pcts)
med = pcts[n // 2] if n % 2 else (pcts[n // 2 - 1] + pcts[n // 2]) / 2
print("\n=== 末日帧 池内(%d) %s 中位 %.2f 均值 %.2f 涨%d 跌%d 平%d ≥+9%% %d ≤-9%% %d ==="
      % (n, last["ts"], med, sum(pcts) / n, sum(1 for p in pcts if p > 0), sum(1 for p in pcts if p < 0),
         sum(1 for p in pcts if p == 0), sum(1 for p in pcts if p >= 9), sum(1 for p in pcts if p <= -9)))
