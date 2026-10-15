# -*- coding: utf-8 -*-
"""hb-e(2026-10-15 14:30 尾盘前哨) 计算稿: 只用决断时间戳之前已留档帧(零后视镜)。"""
import json, io, os, statistics as st
from datetime import datetime, timedelta

D = r"D:\股票数据\市场数据\盘中\20261015"
CUT = None  # 由 last 帧决定; 下面打印

frames = []
for line in io.open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    o = json.loads(line)
    ts = datetime.strptime(o["ts"], "%Y-%m-%d %H:%M:%S")
    frames.append((ts, o))
frames.sort(key=lambda x: x[0])
print("文件内总帧=%d 首帧=%s 末帧=%s" % (len(frames), frames[0][0], frames[-1][0]))
gaps = [(frames[i+1][0]-frames[i][0]).total_seconds() for i in range(len(frames)-1)]
print("相邻间隔 最小/最大/均值 = %.0f/%.0f/%.2f 秒" % (min(gaps), max(gaps), sum(gaps)/len(gaps)))
now = datetime.strptime("2026-10-15 14:34:30", "%Y-%m-%d %H:%M:%S")
print("末帧滞后相对决断时点 = %.0f 秒" % (now - frames[-1][0]).total_seconds())

meta = frames[-1][1]
print("池: pool_date=%s pool_kind=%s pool_stale=%s n=%d src=%s phase=%s" % (
    meta["pool_date"], meta["pool_kind"], meta["pool_stale"], meta["n"], meta["src"], meta["phase"]))

last = {r["code"]: r for r in frames[-1][1]["rows"]}

def ztpx(r):
    pc = r["preClose"]
    lim = 0.20 if str(r["code"]).startswith(("30", "68")) else 0.10
    return round(pc * (1 + lim), 2), lim

def snap(tt):
    b = None
    for t, o in frames:
        if t <= tt:
            b = (t, o)
        else:
            break
    return b

def pcts(frame):
    return {r["code"]: r["pct"] for r in frame["rows"]}

print("\n===== 末合法帧截面 =====")
vals = [last[c]["pct"] for c in last]
print("n=%d 中位=%.2f 均值=%.3f 最低=%.2f 最高=%.2f 红=%d 绿=%d 平=%d" % (
    len(last), st.median(vals), sum(vals)/len(vals), min(vals), max(vals),
    sum(1 for v in vals if v > 0), sum(1 for v in vals if v < 0), sum(1 for v in vals if v == 0)))
feng, zha, dt = [], [], []
for c, r in last.items():
    z, lim = ztpx(r)
    if r["latest"] >= z - 0.001:
        feng.append(c)
    elif r["high"] >= z - 0.001:
        zha.append(c)
    if lim == 0.10 and r["latest"] <= round(r["preClose"]*0.9, 2) + 0.001:
        dt.append(c)
print("封板=%d %s" % (len(feng), [(c, last[c]["name"]) for c in feng]))
print("炸板=%d %s" % (len(zha), [(c, last[c]["name"]) for c in zha]))
print("跌停=%d %s" % (len(dt), [(c, last[c]["name"]) for c in dt]))

print("\n===== 变化速率(相对前N分钟) =====")
def diffs(m):
    base = snap(frames[-1][0] - timedelta(minutes=m))
    pv = pcts(base[1])
    return sorted(((c, round(last[c]["pct"] - pv[c], 2)) for c in last if c in pv), key=lambda x: x[1])
for m in (1, 2, 5, 10, 20, 30, 40, 60):
    ds = diffs(m)
    print("%2d分钟: 中位 %+.2f  <=-3pp %d  <=-2pp %d  >=+2pp %d | 最弱 %s | 最强 %s" % (
        m, st.median([d for _, d in ds]),
        sum(1 for _, d in ds if d <= -3), sum(1 for _, d in ds if d <= -2), sum(1 for _, d in ds if d >= 2),
        [(c, d, last[c]["name"]) for c, d in ds[:3]], [(c, d, last[c]["name"]) for c, d in ds[-2:]]))

print("\n===== 题材批量跳水扫描(>=3只 2分钟内 -3%) =====")
hitmax = 0
for wm, lab in ((60, "末60分钟"), (40, "末40分钟"), (15, "末15分钟"), (5, "末5分钟"), (2, "末2分钟")):
    start = frames[-1][0] - timedelta(minutes=wm)
    sub = [(t, o) for t, o in frames if t >= start]
    mx, details = 0, None
    for i, (t1, o1) in enumerate(sub):
        p1 = pcts(o1)
        for t2, o2 in sub[i+1:]:
            if (t2-t1).total_seconds() > 120.4:
                break
            if (t2-t1).total_seconds() < 30:
                continue
            p2 = pcts(o2)
            mem = [(c, round(p1[c], 2), round(p2[c], 2), round(p2[c]-p1[c], 2)) for c in p1 if c in p2 and p2[c]-p1[c] <= -3]
            if len(mem) > mx:
                mx, details = len(mem), (t1.strftime("%H:%M:%S"), t2.strftime("%H:%M:%S"), mem)
    if lab in ("末15分钟", "末5分钟", "末2分钟"):
        print("[%s] 最大达阈只数=%d 明细=%s" % (lab, mx, details))
    if mx > hitmax:
        hitmax = mx

print("\n===== 持仓(本系统决断记录)轨迹 =====")
for code, label in (("000011", "深物业A"), ("600693", "东百集团"), ("605577", "龙版传媒")):
    tr = [(t, [x for x in o["rows"] if x["code"] == code][0]) for t, o in frames
          if any(x["code"] == code for x in o["rows"])]
    if not tr:
        print("%s %s 不在观测池(pool=1014 zt_pool 36只, 该票∉池) → 持仓照会改用腾讯直取(_hb_e_quote.json)" % (code, label))
        continue
    lo = min(tr, key=lambda x: x[1]["latest"]); hi = max(tr, key=lambda x: x[1]["latest"])
    r = tr[-1][1]
    print("%s %s: 末帧 %s latest=%.2f pct=%+.2f%% 开=%.2f 高=%.2f 低=%.2f 前收=%.2f 涨停=%.2f" % (
        code, label, tr[-1][0].strftime("%H:%M:%S"), r["latest"], r["pct"], r["open"], r["high"], r["low"], r["preClose"], ztpx(r)[0]))
    print("   窗内 低 %s=%.2f / 高 %s=%.2f" % (lo[0].strftime("%H:%M"), lo[1]["latest"], hi[0].strftime("%H:%M"), hi[1]["latest"]))
    print("   午后(>=13:00):", [(t.strftime("%H:%M"), x["pct"]) for t, x in tr if t >= datetime(2026,10,15,13,0)][::5])

print("\n===== 末合法帧全池明细(pct降序) =====")
for c in sorted(last, key=lambda c: -last[c]["pct"]):
    r = last[c]; z, _ = ztpx(r)
    tag = "封板" if r["latest"] >= z-0.001 else ("炸板" if r["high"] >= z-0.001 else "")
    print("  %s %-8s %+7.2f%% latest=%.2f high=%.2f low=%.2f %s" % (c, r["name"], r["pct"], r["latest"], r["high"], r["low"], tag))
