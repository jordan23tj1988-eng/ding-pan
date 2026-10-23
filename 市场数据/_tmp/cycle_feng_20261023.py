# -*- coding: utf-8 -*-
import json
t=json.load(open('D:/股票数据/市场数据/_学习/_市场温度表.json',encoding='utf-8'))
days=sorted(k for k in t if str(k).isdigit())
rows=[]
for k in days:
    v=t[k]
    if not isinstance(v.get('涨停数'),int): continue
    z=v['涨停数']+ (v.get('炸板数') or 0)
    if z==0: continue
    rows.append((k, v['涨停数']/z, v.get('温度'), v.get('成交额亿')))
seq=[r for r in rows if r[0]>='20250101']
print('样本日',len(seq))
hit=[i for i,r in enumerate(seq) if r[1]>=0.85 and i+1<len(seq)]
print('封板率>=0.85 次数',len(hit))
for i in hit:
    cur,nx=seq[i],seq[i+1]
    print(' %s 封板率%.3f 温%.1f -> 次日 %s 封板率%.3f 温%.1f 涨停%s'%(cur[0],cur[1],cur[2] or 0,nx[0],nx[1],nx[2] or 0, t[nx[0]]['涨停数']))
import statistics as st
d_temp=[ (seq[i+1][2] or 0)-(seq[i][2] or 0) for i in hit]
d_feng=[ seq[i+1][1]-seq[i][1] for i in hit]
print('次日温度Δ 均 %.2f 中位 %.2f; 回落 %d/%d'%(st.mean(d_temp),st.median(d_temp),len([x for x in d_temp if x<0]),len(d_temp)))
print('次日封板率Δ 均 %.3f 中位 %.3f; 回落 %d/%d'%(st.mean(d_feng),st.median(d_feng),len([x for x in d_feng if x<0]),len(d_feng)))
# 冰点(<25)日 次日
ice=[i for i,r in enumerate(seq) if (r[2] or 99)<25 and i+1<len(seq)]
print('温度<25 次数',len(ice))
g=[ (seq[i+1][2] or 0)-(seq[i][2] or 0) for i in ice]
print('冰点次日温度Δ 均 %.2f 中位 %.2f 上修 %d/%d'%(st.mean(g),st.median(g),len([x for x in g if x>0]),len(g)))
