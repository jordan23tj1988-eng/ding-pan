# -*- coding: utf-8 -*-
import io,csv,json,os,statistics
B=r"D:/股票数据/市场数据"
def bars(code):
    p=B+"/_学习/_bars_cache/%s.csv"%code
    if not os.path.exists(p): return None
    d={}
    for l in io.open(p,encoding="utf-8-sig").read().strip().splitlines()[1:]:
        r=l.split(",")
        if len(r)<5: continue
        d[r[0]]=(float(r[1]),float(r[2]),float(r[3]),float(r[4]))
    return d
def pool(d): return list(csv.DictReader(io.open(B+"/%s/zt_pool.csv"%d,encoding="utf-8-sig")))
# 1103 昨日池执1 (1102池 -> 1103)
z2=pool("20261102"); e=[];miss=0
for r in z2:
    b=bars(r['代码'])
    if not b or '2026-11-03' not in b: miss+=1; continue
    o,h,l,c=b['2026-11-03']; e.append((c/o-1)*100)
print("1102池 n=%d miss=%d 1103执1均=%.2f%% 胜率=%.1f%%"%(len(z2),miss,statistics.mean(e),100*sum(1 for x in e if x>0)/len(e)))
# 今日 昨日池执1 (1103池 -> 1104)
z3=pool("20261103"); e=[];miss=0
for r in z3:
    b=bars(r['代码'])
    if not b or '2026-11-04' not in b: miss+=1; continue
    o,h,l,c=b['2026-11-04']; e.append((c/o-1)*100)
print("1103池 n=%d miss=%d 1104执1均=%.2f%% 胜率=%.1f%%"%(len(z3),miss,statistics.mean(e),100*sum(1 for x in e if x>0)/len(e)))
# 1103 首封分布
from collections import Counter
def bk(t):
    h=int(str(t).zfill(6)[:4])
    return '一字<=9:25' if h<=925 else '秒板<=9:31' if h<=931 else '早盘<=10:00' if h<=1000 else ('盘中10-14' if h<=1400 else '尾盘>14')
c=Counter(bk(r['首次封板时间']) for r in z3)
print("1103首封",dict(c),"一字+秒板占比=%.1f%%"%(100*(c['一字<=9:25']+c['秒板<=9:31'])/len(z3)))
# 002992 / 688809 明细
z4={r['代码']:r for r in pool("20261104")}
for k in ('002992','688809','002980','002652'):
    r=z4.get(k)
    if r: print(k,r['名称'],'连板',r['连板数'],'首封',r['首次封板时间'],'封板亿',round(float(r['封板资金'])/1e8,3),'换手',r['换手率'],'封单比',round(float(r['封板资金'])/float(r['流通市值'])*100,2),'市值亿',round(float(r['流通市值'])/1e8,1))
# 温度表里是否有一进二率历史
t=json.load(open(B+"/_学习/_市场温度表.json",encoding="utf-8"))
k4=t.get('20261104') or {}
print("温度表键",list(k4.keys())[:20] if isinstance(k4,dict) else type(k4))
