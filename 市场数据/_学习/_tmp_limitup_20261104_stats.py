# -*- coding: utf-8 -*-
import sys, json, io, csv, statistics
sys.path.insert(0, r"D:/股票数据/市场数据")
import pandas as pd, numpy as np
B=r"D:/股票数据/市场数据"
df=pd.read_csv(B+"/_学习/_tmp_limitup_gapcache_20261104.csv",encoding="utf-8-sig",dtype={'代码':str})
df['首封']=df['首封'].astype(str)
def fb(v): return '一字≤9:25' if v<='09:25' else '秒板≤9:31' if v<='09:31' else '早盘≤10:00' if v<='10:00' else ('盘中10-14' if v<='14:00' else '尾盘>14')
def lb(v): return '首板' if v<=1 else ('2板' if v==2 else ('3板' if v==3 else '4板+'))
def th(v): return '<3%' if v<3 else ('3-10%' if v<10 else ('10-20%' if v<20 else '≥20%'))
df['cell']=df['连板'].map(lb)+'|'+df['首封'].map(fb)+'|'+df['换手'].map(th)
G=df.dropna(subset=['GAP'])
cells={}
for k,x in G.groupby('cell'):
    e1=x['E1'].dropna(); e2=x['E2'].dropna()
    cells[k]=dict(n=len(x),gate=round(float(((x['GAP']>-3)&(x['GAP']<=1.5)).mean()*100),1),
      gate3=round(float(((x['GAP']>-3)&(x['GAP']<=3)).mean()*100),1),
      med=round(float(x['GAP'].median()),2),
      e1=round(float(e1.mean()),3) if len(e1) else None,
      w1=round(float((e1>0).mean()*100),1) if len(e1) else None,
      e2=round(float(e2.mean()),3) if len(e2) else None,
      w2=round(float((e2>0).mean()*100),1) if len(e2) else None,
      n1=int(len(e1)), n2=int(len(e2)))
out={'cells':cells}
# gap 桶的执1 表现 (闸门上界检验)
def gb(g):
    if g<=-3: return 'A≤-3'
    if g<=-1: return 'B(-3,-1]'
    if g<=0: return 'C(-1,0]'
    if g<=0.5: return 'D(0,0.5]'
    if g<=1.5: return 'E(0.5,1.5]'
    if g<=3: return 'F(1.5,3]'
    return 'G>3'
G2=G.copy(); G2['gb']=G2['GAP'].map(gb)
out['gap桶']={k:dict(n=len(x),e1=round(float(x['E1'].mean()),3),w1=round(float((x['E1']>0).mean()*100),1),
    e2=round(float(x['E2'].mean()),3) if x['E2'].notna().any() else None,
    w2=round(float((x['E2']>0).mean()*100),1) if x['E2'].notna().any() else None) for k,x in G2.groupby('gb')}
# 尾盘族 + 非一字族 分gap桶 (本路主用格)
w=G2[G2['首封']>='14:00']
out['尾盘族gap桶']={k:dict(n=len(x),e1=round(float(x['E1'].mean()),3),w1=round(float((x['E1']>0).mean()*100),1)) for k,x in w.groupby('gb')}
# 昨日池(20261103 48只) 今日实测执1 / gap
zt3=list(csv.DictReader(io.open(B+"/20261103/zt_pool.csv",encoding="utf-8-sig")))
def bars(code):
    p=B+"/_学习/_bars_cache/%s.csv"%code
    import os
    if not os.path.exists(p): return None
    d={}
    for l in io.open(p,encoding="utf-8-sig").read().strip().splitlines()[1:]:
        r=l.split(",")
        if len(r)<5: continue
        try: d[r[0]]=(float(r[1]),float(r[2]),float(r[3]),float(r[4]))
        except: continue
    return d
res=[]; gaps=[]
for r in zt3:
    b=bars(r['代码'])
    if not b or '2026-11-03' not in b or '2026-11-04' not in b: continue
    o3,c3=b['2026-11-03'][0],b['2026-11-03'][3]
    o4,c4=b['2026-11-04'][0],b['2026-11-04'][3]
    res.append((c4/o4-1)*100); gaps.append((o4/c3-1)*100)
out['昨日池48_今日实测']=dict(n=len(res),执1均收=round(statistics.mean(res),2),胜率=round(100*sum(1 for x in res if x>0)/len(res),1),
    gap中位=round(statistics.median(gaps),2),gap_gt3=round(100*sum(1 for g in gaps if g>3)/len(gaps),1),
    gate触发=round(100*sum(1 for g in gaps if -3<g<=1.5)/len(gaps),1))
# 今日候选格子
zt4=list(csv.DictReader(io.open(B+"/20261104/zt_pool.csv",encoding="utf-8-sig")))
qr=json.load(io.open(B+"/_学习/涨停质量荐票_20261104.json",encoding="utf-8-sig"))
qmap={x['代码']:x for x in qr['明细']}
def g(a,b):
    return round(float(a)/float(b)*100,2) if float(b) else None
cands=[]
for r in zt4:
    c=r['代码']; q=qmap.get(c,{})
    t=str(r['首次封板时间']).zfill(6)
    k=lb(int(float(r['连板数'])))+'|'+fb(t[:2]+':'+t[2:4])+'|'+th(float(r['换手率']))
    cl=cells.get(k,{})
    e1=cl.get('e1'); gate=cl.get('gate')
    cands.append(dict(代码=c,名称=r['名称'],连板=int(float(r['连板数'])),首封=t,换手=round(float(r['换手率']),2),
      封单比=g(r['封板资金'],r['流通市值']),市值亿=round(float(r['流通市值'])/1e8,1),行业=r['所属行业'],cell=k,
      格n=cl.get('n'),格gate=gate,格e1=e1,格w1=cl.get('w1'),格e2=cl.get('e2'),格w2=cl.get('w2'),
      可兑现=round(e1*gate/100,3) if (e1 is not None and gate is not None) else None,
      质量分=q.get('质量分'),预测执1=q.get('预测执1均涨'),催化=(q.get('催化') or '')[:60],大方向=q.get('大方向')))
out['今日候选格']=cands
json.dump(out,open(B+"/_学习/_tmp_limitup_20261104_stats.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps({k:out[k] for k in ['gap桶','尾盘族gap桶','昨日池48_今日实测']},ensure_ascii=False,indent=1))
print("候选池 top by 可兑现:")
bad=[c for c in cands if c['可兑现'] is not None and c['格n'] and c['格n']>=25]
for c in sorted(bad,key=lambda x:-x['可兑现'])[:15]:
    print(json.dumps({kk:c[kk] for kk in ['代码','名称','连板','首封','换手','封单比','cell','格n','格gate','格e1','格w1','格e2','可兑现','质量分','预测执1','大方向']},ensure_ascii=False))
