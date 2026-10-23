# -*- coding: utf-8 -*-
import re
F={r:open(f'_学习/{r}判断_20261023.json',encoding='utf-8').read()+open(f'_学习/交易计划_{r}_20261023.json',encoding='utf-8').read() for r in ['auction','lhb','theme','logic','limitup']}
toks=['0.89','75.7','09:36','6有6','宽度37','53.02','9.8','29.2','46.2','0.285','35.7','0.862','9.40','46.0','0.02','五席','V型日全档','124','12池日','一字|未炸','0.660','4.07']
for t in toks:
    hit=[r for r,s in F.items() if t in s]
    print('%-10s'%t, 'OK ' if hit else 'MISS', hit)
print('==== theme 时间/封单 段落 ====')
for m in re.finditer(r'(13:00|09:36|封单率|中位)', F['theme']):
    print('...',F['theme'][max(0,m.start()-200):m.start()+220].replace('\n',' '))
    break
print('---- 全量 13:00/09:36 上下文 ----')
seen=set()
for m in re.finditer(r'13[:：]00|09[:：]36|封单率中位|早封', F['theme']):
    st=max(0,m.start()-160); key=st//300
    if key in seen: continue
    seen.add(key)
    print('>>',F['theme'][st:m.start()+200].replace('\n',' '))
