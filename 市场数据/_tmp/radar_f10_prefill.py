# -*- coding: utf-8 -*-
"""并行预填f10 checkpoint: 复刻main的候选筛选,对cands+fermented[:12]批量f10_concepts"""
import json,time,importlib.util
import requests
spec=importlib.util.spec_from_file_location('radar','中报预增雷达.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d='20260716'
CKPT='/tmp/radar_ckpt_'+d+'.json'
ck=json.load(open(CKPT))
codes=json.load(open('_tmp/radar_codes.json'))
zt5=m.zt_codes_lastN(d,5)
# 复刻筛选: r20<15 且 无近5日涨停 且 r250<100 → cand; 其余fermented
cands=[];ferm=[]
for c in codes:
    ent=ck['bars'].get(c)
    if not isinstance(ent,dict) or ent.get('r20') is None: continue
    r20=ent['r20']; r250=(ent.get('pos') or {}).get('r250') if isinstance(ent.get('pos'),dict) else None
    # pos结构未知,保守:全部预填(f10对所有池子都可能要)
    cands.append((c,r20))
# 目标=尚无f10的
todo=[c for c,_ in cands if c not in ck['f10']]
print('f10待填',len(todo))
sess=requests.Session()
from concurrent.futures import ThreadPoolExecutor
t0=time.time(); done=0
def one(c):
    try: return c,list(m.f10_concepts(c,sess))
    except Exception: return c,[None,None]
with ThreadPoolExecutor(max_workers=10) as ex:
    for c,v in ex.map(one,todo[:400]):
        ck['f10'][c]=v; done+=1
        if time.time()-t0>28: break
json.dump(ck,open(CKPT,'w'),ensure_ascii=False)
print('本轮f10',done,'累计',len(ck['f10']))
