# -*- coding: utf-8 -*-
import re, json
F={r:open(f'_学习/{r}判断_20261023.json',encoding='utf-8').read()+open(f'_学习/交易计划_{r}_20261023.json',encoding='utf-8').read() for r in ['auction','lhb','theme','logic','limitup']}
for t in ['2.66','五席','n=11','2026-10-15','2.38','9/24','37.5','0.667','0.35','33.11','379.4','728.5','62.84','0.28','21.9','0.54']:
    hit=[r for r,s in F.items() if t in s]
    print('%-12s'%t,'OK ' if hit else 'MISS',hit)
print('--- lhb 003021 上下文 ---')
s=F['lhb']
i=s.find('003021')
while i>0:
    print('>>',s[max(0,i-260):i+260].replace('\n',' '))
    i=s.find('003021',i+1)
    if i>30000: break
print('--- 602 画像汇总 合计 ---')
d=json.load(open('_学习/子agent增强/_战绩画像汇总_20261023.json',encoding='utf-8'))
print(json.dumps({k:v for k,v in d.items() if k!='五路'},ensure_ascii=False)[:700])
for k,v in d['五路'].items():
    print(k,{kk:vv for kk,vv in v.items() if isinstance(vv,(int,float,str)) and kk!='按日'})
