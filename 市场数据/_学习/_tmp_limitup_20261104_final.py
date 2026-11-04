# -*- coding: utf-8 -*-
import sys, json, io, csv, statistics, os
sys.path.insert(0, r"D:/股票数据/市场数据")
import pandas as pd, numpy as np
B=r"D:/股票数据/市场数据"
S=json.load(io.open(B+"/_学习/_tmp_limitup_20261104_stats.json",encoding="utf-8"))
cells=S['cells']; cands={c['代码']:c for c in S['今日候选格']}
out={}
for c in ['002652','002827','301583','605577','000096','920298','002992','002980','688809','002058','000679','600892']:
    out[c]=cands.get(c)
print("== key cands ==")
for c,v in out.items(): print(json.dumps(v,ensure_ascii=False))
zt3=list(csv.DictReader(io.open(B+"/20261103/zt_pool.csv",encoding="utf-8-sig")))
zt4=list(csv.DictReader(io.open(B+"/20261104/zt_pool.csv",encoding="utf-8-sig")))
dt4=list(csv.DictReader(io.open(B+"/20261104/dt_pool.csv",encoding="utf-8-sig")))
zb4=list(csv.DictReader(io.open(B+"/20261104/zb_pool.csv",encoding="utf-8-sig")))
def bars(code):
    p=B+"/_学习/_bars_cache/%s.csv"%code
    if not os.path.exists(p): return None
    d={}
    for l in io.open(p,encoding="utf-8-sig").read().strip().splitlines()[1:]:
        r=l.split(",")
        if len(r)<5: continue
        try: d[r[0]]=(float(r[1]),float(r[2]),float(r[3]),float(r[4]))
        except: continue
    return d
TAG='羊阳扬洋佯'
tag3=[r for r in zt3 if any(ch in r['名称'] for ch in TAG)]
tag4=[r for r in zt4 if any(ch in r['名称'] for ch in TAG)]
red=0; lst=[]
for r in tag3:
    b=bars(r['代码'])
    if not b or '2026-11-03' not in b or '2026-11-04' not in b: continue
    c3=b['2026-11-03'][3]; c4=b['2026-11-04'][3]
    chg=(c4/c3-1)*100
    lst.append((r['代码'],r['名称'],round(chg,2)))
    if chg>0: red+=1
print("== 羊字辈11/03 ==",len(tag3),"翻红",red,lst)
out['羊字辈']=dict(n=len(tag3),翻红=red,明细=lst,今日涨停tag=[(r['代码'],r['名称']) for r in tag4])
# 昨日3板以上是否跌停
hi3=[r for r in zt3 if int(float(r['连板数']))>=3]
dt4codes={r['代码'] for r in dt4}
out['昨日3板以上']=[(r['代码'],r['名称'],r['连板数'],'跌停' if r['代码'] in dt4codes else '未跌停') for r in hi3]
print("== 昨日3板+ ==",out['昨日3板以上'])
# 今日结构
def fdb(r): return float(r['封板资金'])/float(r['流通市值'])*100
def bk(t):
    t=str(t).zfill(6); h=int(t[:4])
    return '一字≤9:25' if h<=925 else '秒板≤9:31' if h<=931 else '早盘≤10:00' if h<=1000 else ('盘中10-14' if h<=1400 else '尾盘>14')
from collections import Counter
out['首封分布']=dict(Counter(bk(r['首次封板时间']) for r in zt4))
out['一字严格']=sum(1 for r in zt4 if int(str(r['首次封板时间']).zfill(6)[:4])<=925 and int(float(r['炸板次数']))==0)
out['封单比中位']=round(statistics.median(fdb(r) for r in zt4),3)
out['封单比均']=round(statistics.mean(fdb(r) for r in zt4),3)
out['封板总额亿']=round(sum(float(r['封板资金']) for r in zt4)/1e8,2)
out['换手桶']=dict(Counter('≥20%' if float(r['换手率'])>=20 else '10-20%' if float(r['换手率'])>=10 else '3-10%' if float(r['换手率'])>=3 else '<3%' for r in zt4))
out['市值≥100亿']=[(r['代码'],r['名称'],round(float(r['流通市值'])/1e8,0)) for r in zt4 if float(r['流通市值'])/1e8>=100]
out['炸板率']=round(100*len(zb4)/(len(zt4)+len(zb4)),2)
out['跌停行业']=dict(Counter(r['所属行业'] for r in dt4))
out['跌停≥100亿']=[(r['代码'],r['名称'],round(float(r['流通市值'])/1e8,0)) for r in dt4 if float(r['流通市值'])/1e8>=100]
out['炸板≥100亿']=[(r['代码'],r['名称'],round(float(r['流通市值'])/1e8,0)) for r in zb4 if float(r['流通市值'])/1e8>=100]
# 全池预测分布
qr=json.load(io.open(B+"/_学习/涨停质量荐票_20261104.json",encoding="utf-8-sig"))
rows=qr['明细']
p1=[x['预测执1均涨'] for x in rows]; p2=[x['预测执2均涨'] for x in rows]
out['全池']=dict(n=len(rows),执1均涨中位=round(statistics.median(p1),2),执1均涨max=round(max(p1),2),执1均涨min=round(min(p1),2),
  执1预测正数=sum(1 for x in p1 if x>0),执2均涨中位=round(statistics.median(p2),2),执2预测正数=sum(1 for x in p2 if x>0),
  质量分max=max(x['质量分'] for x in rows),质量分中位=statistics.median([x['质量分'] for x in rows]))
print("== 今日结构 ==",json.dumps({k:out[k] for k in ['首封分布','一字严格','封单比中位','封单比均','封板总额亿','换手桶','炸板率','跌停行业','全池']},ensure_ascii=False))
print("≥100亿",out['市值≥100亿']); print("跌停≥100亿",out['跌停≥100亿']); print("炸板≥100亿",out['炸板≥100亿'])
json.dump(out,open(B+"/_学习/_tmp_limitup_20261104_final.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
