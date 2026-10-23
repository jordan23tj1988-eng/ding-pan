import json
x=json.load(open('_学习/_情绪先行指标.json',encoding='utf-8'))
k='20261023' if '20261023' in x else list(x.keys())[-1]
print('情绪 key',k); print(json.dumps(x[k],ensure_ascii=False,indent=1)[:1800])
g=json.load(open('_学习/题材归位_20261023.json',encoding='utf-8'))
print('归位 keys',list(g.keys())[:10])
from collections import Counter
m = g.get('映射') or g.get('明细')
print('映射类型',type(m), len(m) if hasattr(m,'__len__') else '')
if isinstance(m,list):
    print(json.dumps(m[0],ensure_ascii=False)[:400])
    c=Counter([i.get('大方向') for i in m]); print(c.most_common(12))
    print('来源档',Counter([i.get('来源档') or i.get('档') for i in m]))
elif isinstance(m,dict):
    v=list(m.values())[0]; print(json.dumps(v,ensure_ascii=False)[:400])
    c=Counter([i.get('大方向') for i in m.values()]); print(c.most_common(12))
d=json.load(open('_学习/龙虎榜双源校验_20261023.json',encoding='utf-8'))
print('双源 keys',[kk for kk in d.keys()][:15])
for kk in d:
    if kk in ('status','日期','摘要','统计','metrics'): print(kk,json.dumps(d[kk],ensure_ascii=False)[:600])
