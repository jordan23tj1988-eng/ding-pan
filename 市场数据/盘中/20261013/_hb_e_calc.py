# -*- coding: utf-8 -*-
import json, os, statistics as st
from datetime import datetime, timedelta

D = r"D:\股票数据\市场数据\盘中\20261013"
CUT = datetime(2026,10,13,14,30,0)

frames=[]
with open(os.path.join(D,"realtime_ticks.jsonl"),encoding="utf-8") as f:
    for line in f:
        line=line.strip()
        if not line: continue
        o=json.loads(line)
        ts=datetime.strptime(o["ts"],"%Y-%m-%d %H:%M:%S")
        frames.append((ts,o))
frames.sort(key=lambda x:x[0])
allts=[t for t,_ in frames]
legal=[(t,o) for t,o in frames if t<=CUT]
post=[t for t,o in frames if t>CUT]
print("总帧数",len(frames),"首帧",allts[0],"末帧",allts[-1])
print("合法帧(<=14:30:00)",len(legal),"末合法帧",legal[-1][0])
print("被剔除帧(>14:30:00)",[str(t) for t in post])
# 相邻间隔
gaps=[(allts[i]-allts[i-1]).total_seconds() for i in range(1,len(allts))]
print("相邻间隔 min/max",min(gaps),max(gaps))
lg=[(legal[i][0]-legal[i-1][0]).total_seconds() for i in range(1,len(legal))]
print("合法窗相邻间隔 min/max",min(lg),max(lg))

last=legal[-1]
o=last[1]
rows={r["code"]:r for r in o["rows"]}
print("pool",o.get("pool_date"),o.get("pool_kind"),o.get("pool_stale"),"n",o.get("n"),"实际行",len(o["rows"]))

# 断面
pcts=[r["pct"] for r in o["rows"]]
red=sum(1 for p in pcts if p>0); green=sum(1 for p in pcts if p<0); flat=sum(1 for p in pcts if p==0)
def is_zt(r):
    c=r["code"]; lim = 19.9 if (c.startswith("30") or c.startswith("68")) else 9.9
    return r["pct"]>=lim
def is_dt(r):
    c=r["code"]; lim = -19.9 if (c.startswith("30") or c.startswith("68")) else -9.9
    return r["pct"]<=lim
zt=[(r["code"],r["name"],r["pct"]) for r in o["rows"] if is_zt(r)]
dt=[(r["code"],r["name"],r["pct"]) for r in o["rows"] if is_dt(r)]
print("中位",round(st.median(pcts),2),"均值",round(sum(pcts)/len(pcts),3),"最低",min(pcts),"最高",max(pcts))
print("红/绿/平",red,green,flat,"封板",len(zt),"跌停",len(dt))
print("封板名单",[(c,n,p) for c,n,p in zt])
print("跌停名单",[(c,n,p) for c,n,p in dt])

# 时点快照(用于变化率/演化)
def snap(tt):
    best=None
    for t,oo in legal:
        if t<=tt: best=(t,oo)
        else: break
    return best
for label,tt in [("11:00",datetime(2026,10,13,11,0,0)),("13:30",datetime(2026,10,13,13,30,0)),("13:00",datetime(2026,10,13,13,0,0)),("14:00",datetime(2026,10,13,14,0,0)),("14:25",datetime(2026,10,13,14,25,0))]:
    b=snap(tt)
    if not b: continue
    t,oo=b
    ps=[r["pct"] for r in oo["rows"]]
    z=sum(1 for r in oo["rows"] if is_zt(r)); dd=sum(1 for r in oo["rows"] if is_dt(r))
    print(f"[{label}] 用帧{t} 中位{round(st.median(ps),2)} 均值{round(sum(ps)/len(ps),3)} 红{sum(1 for p in ps if p>0)}/绿{sum(1 for p in ps if p<0)}/平{sum(1 for p in ps if p==0)} 封板{z} 跌停{dd}")

# 变化率: 各票 5/10/20 分钟 pct 变化
def diff_median(mins):
    tt=last[0]-timedelta(minutes=mins)
    b=snap(tt)
    if not b: return None,None
    prev={r["code"]:r["pct"] for r in b[1]["rows"]}
    ds=[(c,round(rows[c]["pct"]-prev[c],2)) for c in rows if c in prev]
    return round(st.median([d for _,d in ds]),2), ds
for m in (1,2,5,10,20,30):
    med,ds=diff_median(m)
    if ds is None: continue
    print(f"{m}分钟变化中位 {med} | <=-2pp {sum(1 for _,d in ds if d<=-2)} | <=-3pp {sum(1 for _,d in ds if d<=-3)} | >=+2pp {sum(1 for _,d in ds if d>=2)}")
    if m==5:
        print("   5分钟最弱5:",sorted(ds,key=lambda x:x[1])[:6])
        print("   5分钟最强5:",sorted(ds,key=lambda x:x[1])[-6:])
    if m==2:
        print("   2分钟≤-3pp明细:",[ (c,d) for c,d in ds if d<=-3])
    if m==20:
        print("   20分钟≤-3pp明细:",[ (c,d) for c,d in ds if d<=-3])

# 题材批量跳水扫描: 任意相邻帧(<=2min) 内 >=3 只 -3pp
print("=== 题材批量跳水扫描(相邻帧间隔内 ≥3只 ≤-3pp) ===")
hits=[]
for i in range(1,len(legal)):
    t0,o0=legal[i-1]; t1,o1=legal[i]
    if (t1-t0).total_seconds()>130: continue
    prev={r["code"]:r["pct"] for r in o0["rows"]}
    grp=[(r["code"],r["name"],round(r["pct"]-prev[r["code"]],2)) for r in o1["rows"] if r["code"] in prev and r["pct"]-prev[r["code"]]<=-3]
    if len(grp)>=3: hits.append((t0,t1,grp))
print("全窗命中窗口数",len(hits))
for t0,t1,grp in hits:
    print("  ",t0,"->",t1,grp)
# 末40分钟
hits40=[h for h in hits if h[1]>=CUT-timedelta(minutes=40)]
print("末40分钟(13:50~14:30)命中",len(hits40))
# 末5分钟单帧最大跌
d1,_=diff_median(1)
ds5=diff_median(1)[1]
print("末1分钟(14:29:51 vs 14:28:51)最大跌幅:",sorted(ds5,key=lambda x:x[1])[:5])

# 持仓票 000011
print("=== 000011 在池? ===", "000011" in rows)
hit=0
for t,oo in legal:
    for r in oo["rows"]:
        if r["code"]=="000011": hit+=1
print("合法窗内 000011 命中",hit)
