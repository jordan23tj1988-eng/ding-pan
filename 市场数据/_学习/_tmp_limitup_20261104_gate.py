# -*- coding: utf-8 -*-
import sys, json, io
sys.path.insert(0, r"D:/股票数据/市场数据")
import 涨停质量训练 as M
import pandas as pd

df=pd.read_csv(r"D:/股票数据/市场数据/_学习/_tmp_limitup_gapcache_20261104.csv",encoding="utf-8-sig",dtype={'代码':str})
df['首封']=df['首封'].astype(str)
def fb(v):
    return '一字≤9:25' if v<='09:25' else '秒板≤9:31' if v<='09:31' else '早盘≤10:00' if v<='10:00' else ('盘中10-14' if v<='14:00' else '尾盘>14')
def lb(v): return '首板' if v<=1 else ('2板' if v==2 else ('3板' if v==3 else '4板+'))
def th(v): return '<3%' if v<3 else ('3-10%' if v<10 else ('10-20%' if v<20 else '≥20%'))
df['cell']=df['连板'].map(lb)+'|'+df['首封'].map(fb)+'|'+df['换手'].map(th)
g=df.dropna(subset=['GAP']).groupby('cell').agg(n=('GAP','size'),
    gate=('GAP',lambda s:( (s>-3)&(s<=1.5) ).mean()*100),
    gate3=('GAP',lambda s:((s>-3)&(s<=3)).mean()*100),
    med=('GAP','median'))
print("cells",len(g))
print(g.sort_values('n',ascending=False).head(8).to_string())

def bars(code):
    b=M._bars(code)
    return b
def quote(code, d):
    b=bars(code)
    if b is None: return None
    idx=b.index[b['date']==d]
    if not len(idx): return None
    i=idx[0]
    r=b.loc[i]
    prev=b.loc[i-1] if i>0 else None
    nxt=b.loc[i+1] if i+1<len(b) else None
    return dict(d=d,o=float(r['open']),h=float(r['high']),l=float(r['low']),c=float(r['close']),
                prev_c=float(prev['close']) if prev is not None else None,
                next_o=float(nxt['open']) if nxt is not None else None,
                next_c=float(nxt['close']) if nxt is not None else None,
                oneword=(float(r['high'])==float(r['low'])))

out={}
# Set A: 20261102 top5 -> fill on 20261103
A=[('002827','高争民爆'),('600261','阳光照明'),('001230','劲旅环境'),('002275','桂林三金'),('600259','中稀有色')]
rows=[]
for code,name in A:
    q1102=quote(code,'20261102'); q1103=quote(code,'20261103')
    gap=(q1103['o']/q1102['c']-1)*100
    e1=(q1103['c']/q1103['o']-1)*100
    fill = (-3 < gap <= 1.5) and not q1103['oneword']
    rows.append(dict(代码=code,名称=name,gap1103=round(gap,2),一字=q1103['oneword'],
        闸门内=bool(-3<gap<=1.5),成交=bool(fill),执1=round(e1,2),
        首封=None,连板=None,换手=None,cell=None,celln=None,cellgate=None))
out['A_20261102_top5_1103执行']=rows
# Set B: 20261103 总裁决 4 单 -> fill on 20261104
B=[('600261','阳光照明',1.5,-3,3),('002652','扬子新材',1.5,-3,1.5),('603906','龙蟠科技',1.0,-3,3),('002292','奥飞娱乐',0.5,-10,-3)]
rows=[]
for code,name,w,lo,hi in B:
    q1103=quote(code,'20261103'); q1104=quote(code,'20261104')
    gap=(q1104['o']/q1103['c']-1)*100
    e1=(q1104['c']/q1104['o']-1)*100
    fill=(lo < gap <= hi) and not q1104['oneword']
    rows.append(dict(代码=code,名称=name,权重=w,闸门=[lo,hi],gap1104=round(gap,2),一字=q1104['oneword'],
        闸门内=bool(lo<gap<=hi),成交=bool(fill),执1=round(e1,2),
        close1104=q1104['c'],open1104=q1104['o']))
out['B_20261103_总裁决4单_1104执行']=rows
json.dump(out,open(r"D:/股票数据/市场数据/_学习/_tmp_limitup_20261104_gate.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
