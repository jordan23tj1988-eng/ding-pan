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
last_t,last=frames[-1]
rows={r["code"]:r for r in last["rows"]}
def is_zt(r):
    c=r["code"]; lim=19.9 if (c.startswith("30") or c.startswith("68")) else 9.9
    return r["pct"]>=lim

# 封板演化: 首末次封板时间
first={}; lastz={}; cnt_by_ts=[]
for t,o in frames:
    z=[r["code"] for r in o["rows"] if is_zt(r)]
    cnt_by_ts.append((t,len(z)))
    for c in z:
        first.setdefault(c,t); lastz[c]=t
print("=== 封板演化(每5分钟采样) ===")
seen=set()
for t,c in cnt_by_ts:
    k=t.strftime("%H:%M")
    if k[-1] in "05" and k not in seen:
        seen.add(k); print(t.strftime("%H:%M:%S"),c)
print("最终封板数",cnt_by_ts[-1][1],"峰值",max(c for _,c in cnt_by_ts),"@",max(cnt_by_ts,key=lambda x:x[1])[0])
print("=== 各封板票 首封/末封 ===")
for c,t0 in sorted(first.items(),key=lambda x:x[1]):
    print(f"  {c} {rows[c]['name']} 首封{t0.strftime('%H:%M:%S')} 末封{lastz[c].strftime('%H:%M:%S')} 现pct={rows[c]['pct']}")

print("=== 14:29:51 未封高股(>=3%) ===")
for r in sorted(last["rows"],key=lambda r:-r["pct"]):
    if r["pct"]>=3 and not is_zt(r):
        print(f"  {r['code']} {r['name']} pct={r['pct']} open={r['open']} high={r['high']} low={r['low']} preClose={r['preClose']}")

print("=== 深度回撤(< -3%) ===")
for r in sorted(last["rows"],key=lambda r:r["pct"]):
    if r["pct"]<=-3: print(f"  {r['code']} {r['name']} pct={r['pct']} open={r['open']} high={r['high']}")

print("=== watch 关键票轨迹 ===")
watch=["002264","300829","301052","688004","603500","603096","605287","600825","600812","603032","002591","002692","605136","000892","601811","603230","002242","001330","600693","600851","605577"]
def at(code,tt):
    best=None
    for t,o in frames:
        if t<=tt:
            for r in o["rows"]:
                if r["code"]==code: best=(t,r["pct"],r["latest"])
        else: break
    return best
for c in watch:
    if c not in rows: continue
    r=rows[c]
    a9=at(c,datetime(2026,10,13,10,0,0)); a11=at(c,datetime(2026,10,13,11,0,0))
    a13=at(c,datetime(2026,10,13,13,30,0)); a14=at(c,datetime(2026,10,13,14,0,0))
    print(f"  {c} {r['name']}: 09:31={r['open']}@(gap{(r['open']/r['preClose']-1)*100:+.2f}%) 10:00={a9[1] if a9 else None} 11:00={a11[1] if a11 else None} 13:30={a13[1] if a13 else None} 14:00={a14[1] if a14 else None} 14:29:51={r['pct']} 末价{r['latest']} high{r['high']} low{r['low']}")

# 出版/传媒线宽度(封板家数)
line={"出版传媒":["600831","603096","002343","605577","600825","601811","603230","301052","603533","002692","300006","601595","000892"],
      "医药":["600812","300006"]}
print("=== 题材线封板宽度@14:29:51 ===")
for name,codes in line.items():
    z=[c for c in codes if c in rows and is_zt(rows[c])]
    red=[c for c in codes if c in rows and rows[c]["pct"]>0]
    print(f"  {name}: 封板{len(z)}{z} 红盘{len(red)}/{len(codes)}")
