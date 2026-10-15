# -*- coding: utf-8 -*-
"""hb-e(2026-10-14 14:30) 计算稿: 只用 ts<=14:30:00 帧"""
import json, io, os, statistics as st
from datetime import datetime, timedelta

D = r"D:\股票数据\市场数据\盘中\20261014"
CUT = datetime(2026, 10, 14, 14, 30, 0)

frames = []
total = 0
for line in io.open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8"):
    line = line.strip()
    if not line: continue
    total += 1
    o = json.loads(line)
    ts = datetime.strptime(o["ts"], "%Y-%m-%d %H:%M:%S")
    if ts <= CUT: frames.append((ts, o))
frames.sort(key=lambda x: x[0])
print("文件内总帧=%d, 合法帧(<=14:30:00)=%d" % (total, len(frames)))
print("首帧=%s 末合法帧=%s" % (frames[0][0], frames[-1][0]))
gaps = [(frames[i+1][0]-frames[i][0]).total_seconds() for i in range(len(frames)-1)]
print("相邻间隔 最小/最大/均值 = %.0f/%.0f/%.2f 秒" % (min(gaps), max(gaps), sum(gaps)/len(gaps)))
print("文件尾帧(剔除)=%s" % json.loads([l for l in io.open(os.path.join(D,'realtime_ticks.jsonl'),encoding='utf-8') if l.strip()][-1])["ts"])

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
        if t <= tt: b = (t, o)
        else: break
    return b

def pcts(frame):
    return {r["code"]: r["pct"] for r in frame["rows"]}

def diffs(m):
    base = snap(frames[-1][0] - timedelta(minutes=m))
    pv = pcts(base[1])
    return sorted(((c, round(last[c]["pct"] - pv[c], 2)) for c in last), key=lambda x: x[1])

print("\n===== 末合法帧截面 =====")
vals = [last[c]["pct"] for c in last]
print("n=%d 中位=%.2f 均值=%.3f 最低=%.2f 最高=%.2f 红=%d 绿=%d 平=%d" % (
    len(last), st.median(vals), sum(vals)/len(vals), min(vals), max(vals),
    sum(1 for v in vals if v > 0), sum(1 for v in vals if v < 0), sum(1 for v in vals if v == 0)))
feng, zha, dt = [], [], []
for c, r in last.items():
    z, lim = ztpx(r)
    if r["latest"] >= z - 0.001: feng.append(c)
    elif r["high"] >= z - 0.001: zha.append(c)
    if lim == 0.10 and r["latest"] <= round(r["preClose"]*0.9, 2) + 0.001: dt.append(c)
print("封板(按涨停价口径)=%d %s" % (len(feng), feng))
print("炸板(high触板 latest未封)=%d %s" % (len(zha), zha))
print("跌停=%d %s" % (len(dt), dt))

print("\n===== 变化速率 =====")
for m in (1, 2, 5, 10, 20, 30, 40, 60):
    ds = diffs(m)
    print("%2d分钟: 中位 %+.2f  ≤-3pp %d  ≤-2pp %d  ≥+2pp %d | 最弱 %s | 最强 %s" % (
        m, st.median([d for _, d in ds]),
        sum(1 for _, d in ds if d <= -3), sum(1 for _, d in ds if d <= -2), sum(1 for _, d in ds if d >= 2),
        [(c, d, last[c]["name"]) for c, d in ds[:4]], [(c, d, last[c]["name"]) for c, d in ds[-3:]]))

print("\n===== 题材批量跳水扫描 =====")
def scan(pairs_mode, tstart, label):
    hits = []
    for i, (t1, o1) in enumerate(frames):
        p1 = pcts(o1)
        for j in range(i+1, len(frames)):
            t2, o2 = frames[j]
            if (t2 - t1).total_seconds() > 120.4: break
            if (t2 - t1).total_seconds() < 30: continue
            p2 = pcts(o2)
            mem = [(c, p1[c], p2[c], round(p2[c]-p1[c], 2)) for c in p1 if c in p2 and p2[c]-p1[c] <= -3]
            if len(mem) >= 3: hits.append((t1.strftime("%H:%M:%S"), t2.strftime("%H:%M:%S"), mem))
    print("[%s] 达阈批次数=%d" % (label, len(hits)))
    for h in hits[:8]:
        print("   ", h[0], "->", h[1], [(m[0], m[1], m[2], m[3]) for m in h[2]])
    return hits

allh = scan(None, None, "全窗 全部<=120s帧对")
adj = []
for i in range(len(frames)-1):
    t1, o1 = frames[i]; t2, o2 = frames[i+1]
    if (t2-t1).total_seconds() > 65: continue
    p1, p2 = pcts(o1), pcts(o2)
    mem = [(c, p1[c], p2[c], round(p2[c]-p1[c], 2)) for c in p1 if c in p2 and p2[c]-p1[c] <= -3]
    if len(mem) >= 3: adj.append((t1.strftime("%H:%M:%S"), t2.strftime("%H:%M:%S"), mem))
print("[对照 相邻60s帧对] 达阈批次数=%d 明细=%s" % (len(adj), adj))
# 末40分钟 / 末5分钟 / 末2分钟
for wm, lab in ((40, "末40分钟"), (5, "末5分钟"), (2, "末2分钟")):
    start = frames[-1][0] - timedelta(minutes=wm)
    sub = [(t, o) for t, o in frames if t >= start]
    mx = 0
    for i, (t1, o1) in enumerate(sub):
        p1 = pcts(o1)
        for t2, o2 in sub[i+1:]:
            if (t2-t1).total_seconds() > 120.4: break
            if (t2-t1).total_seconds() < 30: continue
            p2 = pcts(o2)
            n = sum(1 for c in p1 if c in p2 and p2[c]-p1[c] <= -3)
            mx = max(mx, n)
    print("[%s 全部<=120s帧对] 最大达阈只数=%d" % (lab, mx))
# 单帧最大跌幅
mu = sorted(((round(last[c]["pct"] - pcts(frames[-2][1])[c], 2), c, last[c]["name"]) for c in last), key=lambda x: x[0])
print("末帧 vs 前一帧 最弱:", mu[:4])

print("\n===== 持仓(本系统决断记录)照会 =====")
for code, name, shares, cost in (("600693", "东百集团", 4000, 12.4124), ("605577", "龙版传媒", 2200, 17.6576)):
    if code not in last:
        print(code, "不在观测池")
        continue
    r = last[code]; z, lim = ztpx(r)
    tr = [(t, [x for x in o["rows"] if x["code"] == code][0]) for t, o in frames]
    lo = min(tr, key=lambda x: x[1]["latest"]); hi = max(tr, key=lambda x: x[1]["latest"])
    touch = [t.strftime("%H:%M:%S") for t, x in tr if x["high"] >= z - 0.001]
    print("\n%s %s %d股 成本%.4f" % (code, name, shares, cost))
    print("  末合法帧 %s: latest=%.2f pct=%+.2f%% vs成本 %+.2f%% vs开盘 %+.2f%% 浮盈 %+.2f元 | high=%.2f low=%.2f preClose=%.2f 涨停价=%.2f" % (
        frames[-1][0].strftime("%H:%M:%S"), r["latest"], r["pct"], (r["latest"]/cost-1)*100,
        (r["latest"]/r["open"]-1)*100, (r["latest"]-cost)*shares, r["high"], r["low"], r["preClose"], z))
    print("  窗内最低 %s=%.2f(%+.2f%%) / 最高 %s=%.2f(%+.2f%%) | 触涨停价时点=%s" % (
        lo[0].strftime("%H:%M:%S"), lo[1]["latest"], lo[1]["pct"], hi[0].strftime("%H:%M:%S"), hi[1]["latest"], hi[1]["pct"],
        touch if touch else "无"))
    print("  轨迹(每15分钟):", [(t.strftime("%H:%M"), x["pct"]) for t, x in tr[::15]])
    print("  午后段(>=13:00):", [(t.strftime("%H:%M"), x["pct"]) for t, x in tr if t >= datetime(2026,10,14,13,0)])

print("\n===== 封板数演化 =====")
ts_list = [t for t, o in frames]
for k in range(0, len(frames), 30):
    t, o = frames[k]
    nf = sum(1 for r in o["rows"] if r["latest"] >= ztpx(r)[0]-0.001)
    nd = sum(1 for r in o["rows"] if ztpx(r)[1] == 0.10 and r["latest"] <= round(r["preClose"]*0.9, 2)+0.001)
    print("  %s 封板=%d 跌停=%d 中位=%+.2f" % (t.strftime("%H:%M:%S"), nf, nd, st.median([r["pct"] for r in o["rows"]])))

print("\n===== 末合法帧全池明细(pct降序) =====")
for c in sorted(last, key=lambda c: -last[c]["pct"]):
    r = last[c]; z, _ = ztpx(r)
    tag = "封板" if r["latest"] >= z-0.001 else ("炸板" if r["high"] >= z-0.001 else "")
    print("  %s %-8s %+7.2f%% latest=%.2f high=%.2f low=%.2f %s" % (c, r["name"], r["pct"], r["latest"], r["high"], r["low"], tag))

print("\n===== 关注线照会(出版/传媒/冰雪/AI漫剧/PCB/高标) =====")
lines = {
    "出版传媒": ["600831","603096","002343","605577","601811","603230","301052","600825","002181","300364"],
    "冰雪经济": ["601188","301010","600593","603099","002878","000715","600853","000558","600719"],
    "AI漫剧": ["002343","301052"],
    "石油/其他": [],
}
for ln, codes in lines.items():
    got = [(c, last[c]["pct"], last[c]["latest"], "封" if last[c]["latest"] >= ztpx(last[c])[0]-0.001 else "") for c in codes if c in last]
    print(" %s: %s" % (ln, got))
print(" 池内 唯一跌停/深跌:", [(c, last[c]["pct"], last[c]["name"]) for c in last if last[c]["pct"] <= -5])
print("\n=== 昨日(20261013)池内高位票(3板+)今日 ===")
print(" (见 20261013 zt_pool 连板数, 本脚本只列池内 pct 最低/最高各 6 只已在上)")

print("\n=== 000011 可观测性 ===")
print(" 000011 in pool?", "000011" in last, "| 窗内命中次数:",
      sum(1 for t, o in frames if any(r["code"] == "000011" for r in o["rows"])))
