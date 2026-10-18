# -*- coding: utf-8 -*-
"""hb-e(2026-10-16 14:30 尾盘前哨) 计算稿: 只用决断时间戳之前已留档帧(零后视镜)。
决断截止 CUT = 本场 claimed_at/started_at = 2026-10-16 14:30:55
(executions.db id=516addf31d4f4152ab01a66669cb202b, job_id=4deb15fee730=sentiment-intraday-hb-e,
 scheduled_instant 2026-10-16T06:30:00+00:00, claimed_at 14:30:55.439, started_at 14:30:55.808)。
池内可观测 = 20261015 涨停池 36 只; 池外持仓 = null(不补数), 另由 _hb_e_quote.json 决断时点直取。
"""
import json, io, os, statistics as st
from datetime import datetime, timedelta

D = r"D:\股票数据\市场数据\盘中\20261016"
CUT = datetime.strptime("2026-10-16 14:30:55", "%Y-%m-%d %H:%M:%S")
PREV_CUT = datetime.strptime("2026-10-16 13:30:55", "%Y-%m-%d %H:%M:%S")

frames_all = []
for line in io.open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    o = json.loads(line)
    frames_all.append((datetime.strptime(o["ts"], "%Y-%m-%d %H:%M:%S"), o))
frames_all.sort(key=lambda x: x[0])
frames = [(t, o) for t, o in frames_all if t <= CUT]
drop = [t.strftime("%H:%M:%S") for t, o in frames_all if t > CUT]
print("① 新鲜度(源 盘中/20261016/realtime_ticks.jsonl)")
print("   全档 %d 帧 (%s ~ %s); 决断窗内 %d 帧 (%s ~ %s); 剔除(CUT后) %d 帧 %s"
      % (len(frames_all), frames_all[0][0], frames_all[-1][0], len(frames),
         frames[0][0], frames[-1][0], len(drop), drop))
gaps = [(frames[i+1][0]-frames[i][0]).total_seconds() for i in range(len(frames)-1)]
print("   帧距 min/max/mean = %.0f/%.0f/%.2f 秒; 末帧距CUT = %.0f 秒 → 断更 %.2f 分钟 %s"
      % (min(gaps), max(gaps), sum(gaps)/len(gaps), (CUT-frames[-1][0]).total_seconds(),
         (CUT-frames[-1][0]).total_seconds()/60,
         "→ 新鲜, 允许决策" if (CUT-frames[-1][0]).total_seconds() < 600 else "★断更>10分钟 → 只报警禁决策"))
lunch = [(t, o) for t, o in frames if datetime(2026,10,16,11,30) < t < datetime(2026,10,16,13,0)]
print("   午休窗(11:30~13:00)帧数 = %d %s" % (len(lunch), (lunch[0][0].strftime('%H:%M:%S')+"~"+lunch[-1][0].strftime('%H:%M:%S')) if lunch else ""))
if lunch:
    a = {r["code"]: r["latest"] for r in lunch[0][1]["rows"]}
    b = {r["code"]: r["latest"] for r in lunch[-1][1]["rows"]}
    same = sum(1 for c in a if c in b and a[c] == b[c])
    print("     午休窗首末帧逐票价相同 = %d/%d (冻结=%s)" % (same, len(b), same == len(b)))
meta = frames[-1][1]
print("   池: pool_date=%s kind=%s stale=%s n=%d src=%s phase=%s mtime=%s"
      % (meta["pool_date"], meta["pool_kind"], meta["pool_stale"], meta["n"], meta["src"], meta["phase"],
         datetime.fromtimestamp(os.path.getmtime(os.path.join(D, "realtime_ticks.jsonl"))).strftime("%Y-%m-%d %H:%M:%S")))

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

print("\n② 决断时点(%s)池截面" % frames[-1][0])
vals = [last[c]["pct"] for c in last]
print("   n=%d 中位=%.2f 均值=%.3f 最低=%.2f 最高=%.2f 红=%d 绿=%d 平=%d" % (
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
print("   封板=%d %s" % (len(feng), [(c, last[c]["name"]) for c in feng]))
print("   炸板=%d %s" % (len(zha), [(c, last[c]["name"], x) for c, x in
                                 ((c, "高%.2f→现%.2f" % (last[c]["high"], last[c]["latest"])) for c in zha)]))
print("   跌停=%d %s" % (len(dt), [(c, last[c]["name"]) for c in dt]))

print("\n③ 变化速率(相对前N分钟, 决断窗内)")
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

print("\n④ 题材批量跳水扫描(≥3只 2分钟内 每只-3%)")
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
    print("[%s] 最大达阈只数=%d 明细=%s" % (lab, mx, details))

print("\n⑤ 在持/在册票 — 池内可观测者轨迹")
for code, label in (("600668", "尖峰集团"), ("605189", "富春染织")):
    tr = [(t, [x for x in o["rows"] if x["code"] == code][0]) for t, o in frames
          if any(x["code"] == code for x in o["rows"])]
    if not tr:
        print("%s %s: 不在观测池" % (code, label))
        continue
    lo = min(tr, key=lambda x: x[1]["latest"]); hi = max(tr, key=lambda x: x[1]["latest"])
    r = tr[-1][1]
    print("%s %s: 全窗 %d 帧; 末帧 %s latest=%.2f pct=%+.2f%% 开=%.2f 高=%.2f 低=%.2f 前收=%.2f 涨停=%.2f"
          % (code, label, len(tr), tr[-1][0].strftime("%H:%M:%S"), r["latest"], r["pct"], r["open"], r["high"], r["low"], r["preClose"], ztpx(r)[0]))
    print("   窗内 低 %s=%.2f / 高 %s=%.2f" % (lo[0].strftime("%H:%M"), lo[1]["latest"], hi[0].strftime("%H:%M"), hi[1]["latest"]))
    st13 = snap(PREV_CUT)
    if st13:
        r13 = [x for x in st13[1]["rows"] if x["code"] == code]
        if r13:
            print("   13:30场(%s)读数 pct=%+.2f → 本场位移 %+.2f pp" % (st13[0].strftime("%H:%M:%S"), r13[0]["pct"], r["pct"]-r13[0]["pct"]))
    print("   午后(>=13:00)采样:", [(t.strftime("%H:%M"), x["pct"]) for t, x in tr if t >= datetime(2026,10,16,13,0)][::5])
print("   池外持仓(不可观测, 一律 null, 不补数): 000011 深物业A / 002860 星帅尔 / 000601 韶能股份 / 603968 醋化股份 / 000823 超声电子")

print("\n⑥ watch 9 只(承 10/16 hb-d 13:30 场)本场核对")
for code, name, cond in (("300111","向日葵","续封 且 炸板≤3 且 末封≤14:00 → 升级重估"),
                         ("603230","内蒙新华","续封 且 炸板≤2 且 末封≤14:00 → 升级重估"),
                         ("002815","崇达技术","开盘可成交(非一字) 且 PCB线宽≥0 且 2板≥1只 → 送总审重估"),
                         ("001318","阳光乳业","续封(4板) 且 食品饮料线宽≥3 且 A档催化 → 送总审重估"),
                         ("301282","金禄电子","PCB方向≥1只带公告级业绩涨停 且 未高开走弱 → 重估"),
                         ("002134","天津普林","出具自身产能/订单公告原件 且 炸板≤1 → 重估"),
                         ("605058","澳弘电子","该票执1均收>0 且 G4闸门内观察位均值>0 → 登记回执"),
                         ("600812","华北制药","医药线过G4闸门≥3只 且 执1均收>0 → 升级为可执行宽度范本"),
                         ("002945","华林证券","券商线≥1只公告级业绩 且 该票执1均收>0 → 重估")):
    r = last.get(code)
    if not r:
        print("  %s %s: 不在池 → null" % (code, name)); continue
    z, lim = ztpx(r)
    st13 = snap(PREV_CUT)
    prev = None
    if st13:
        q = [x for x in st13[1]["rows"] if x["code"] == code]
        prev = q[0]["pct"] if q else None
    print("  %s %-6s 末读数 %.2f(%+.2f%%) 涨停价%.2f 封板=%s 13:30→本场位移=%s | confirm: %s"
          % (code, name, r["latest"], r["pct"], z, r["latest"] >= z-0.001,
             ("%+.2fpp" % (r["pct"]-prev)) if prev is not None else "null", cond))

print("\n⑦ 末合法帧全池明细(pct降序)")
for c in sorted(last, key=lambda c: -last[c]["pct"]):
    r = last[c]; z, _ = ztpx(r)
    tag = "封板" if r["latest"] >= z-0.001 else ("炸板" if r["high"] >= z-0.001 else "")
    print("  %s %-8s %+7.2f%% latest=%.2f high=%.2f low=%.2f %s" % (c, r["name"], r["pct"], r["latest"], r["high"], r["low"], tag))
