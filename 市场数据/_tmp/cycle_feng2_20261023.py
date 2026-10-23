# -*- coding: utf-8 -*-
import json, statistics as st
t=json.load(open('D:/股票数据/市场数据/_学习/_市场温度表.json',encoding='utf-8'))
days=sorted(k for k in t if str(k).isdigit())
seq=[]
for k in days:
    v=t[k]
    if not isinstance(v.get('涨停数'),int): continue
    z=v['涨停数']+(v.get('炸板数') or 0)
    if z==0: continue
    seq.append((k, v['涨停数']/z, v.get('温度'), v.get('涨停数')))
hit=[i for i,r in enumerate(seq) if r[1]>=0.85 and i+1<len(seq)]
ok=[i for i in hit if isinstance(seq[i][2],(int,float)) and isinstance(seq[i+1][2],(int,float)) and seq[i][2]>0 and seq[i+1][2]>0]
print('封板率>=0.85 n=%d, 温度可比 n=%d'%(len(hit),len(ok)))
dt=[seq[i+1][2]-seq[i][2] for i in ok]
df=[seq[i+1][1]-seq[i][1] for i in hit]
print('温度Δ 均%.2f 中位%.2f 回落%d/%d=%.1f%%'%(st.mean(dt),st.median(dt),len([x for x in dt if x<0]),len(dt),100*len([x for x in dt if x<0])/len(dt)))
print('封板率Δ 均%.3f 中位%.3f 回落%d/%d'%(st.mean(df),st.median(df),len([x for x in df if x<0]),len(df)))
# 涨停次日
dz=[seq[i+1][3]-seq[i][3] for i in hit]
print('涨停Δ 均%.1f 中位%.1f 减少%d/%d'%(st.mean(dz),st.median(dz),len([x for x in dz if x<0]),len(dz)))
print('明细温度Δ',[round(x,1) for x in dt])
