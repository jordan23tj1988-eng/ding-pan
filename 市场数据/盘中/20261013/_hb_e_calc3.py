# -*- coding: utf-8 -*-
import json, os, statistics as st
from datetime import datetime, timedelta
D=r"D:\股票数据\市场数据\盘中\20261013"
CUT=datetime(2026,10,13,14,30,0)
frames=[]
for line in open(os.path.join(D,"realtime_ticks.jsonl"),encoding="utf-8"):
    line=line.strip()
    if not line: continue
    o=json.loads(line); ts=datetime.strptime(o["ts"],"%Y-%m-%d %H:%M:%S")
    if ts<=CUT: frames.append((ts,o))
frames.sort(key=lambda x:x[0])
rows={r["code"]:r for r in frames[-1][1]["rows"]}
def snap(tt):
    b=None
    for t,o in frames:
        if t<=tt: b=o
        else: break
    return b
def diffs(m):
    pv={r["code"]:r["pct"] for r in snap(frames[-1][0]-timedelta(minutes=m))["rows"]}
    return sorted(((c,round(rows[c]["pct"]-pv[c],2)) for c in rows),key=lambda x:x[1])
for m in (5,10,20,30,40,60):
    ds=diffs(m)
    print(f"--- {m}分钟 --- 中位{round(st.median([d for _,d in ds]),2)} ≤-3pp{sum(1 for _,d in ds if d<=-3)} ≤-2pp{sum(1 for _,d in ds if d<=-2)} ≥+2pp{sum(1 for _,d in ds if d>=2)}")
    print("   最弱:",[(c,d,rows[c]['name']) for c,d in ds[:5]])
    print("   最强:",[(c,d,rows[c]['name']) for c,d in ds[-4:]])
# 60分钟(13:29:41)对照
print("=== 与13:29:41(hb-d末帧)对照: 走弱/走强 top ===")
o=h=snap(datetime(2026,10,13,13,29,41))
pv={r["code"]:r["pct"] for r in h["rows"]}
ds=sorted(((c,round(rows[c]["pct"]-pv[c],2)) for c in rows),key=lambda x:x[1])
print("60分钟最弱:",[(c,d,rows[c]['name']) for c,d in ds[:8]])
print("60分钟最强:",[(c,d,rows[c]['name']) for c,d in ds[-5:]])
print("=== 002242 九阳股份 全天轨迹 ===")
for t,o in frames[::15]:
    for r in o["rows"]:
        if r["code"]=="002242": print("  ",t.strftime("%H:%M"),r["pct"],r["latest"])
print("=== 605287 德才股份 关键点 ===")
for t,o in frames[::30]:
    for r in o["rows"]:
        if r["code"]=="605287": print("  ",t.strftime("%H:%M"),r["pct"])
print("=== 688004 博汇科技 14:00后 ===")
for t,o in frames:
    if t>=datetime(2026,10,13,14,0,0):
        for r in o["rows"]:
            if r["code"]=="688004": print("  ",t.strftime("%H:%M:%S"),r["pct"],r["latest"],"high",r["high"])
