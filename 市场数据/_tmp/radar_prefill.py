# -*- coding: utf-8 -*-
"""并行预填雷达checkpoint的bars(用模块自身load_bars/r20_of/pos_of,代理session)"""
import json,sys,time,importlib.util
import requests
spec=importlib.util.spec_from_file_location('radar','中报预增雷达.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d='20260716'
import os
if os.path.isfile('_tmp/radar_codes.json'):
    codes_cached=__import__('json').load(open('_tmp/radar_codes.json'))
else:
    codes_cached=None
import akshare as ak
df=None
if codes_cached is None:
    df=ak.stock_yjyg_em(date='20260630')
if df is not None:
    df=df[df['预测指标'].astype(str).str.contains('净利润')]
    df=df[~df['预测指标'].astype(str).str.contains('扣除')]
    df=df[df['预告类型'].isin(['预增','扭亏'])]
    df=df[df['公告日期'].astype(str).str[:10]<='2026-07-16']
    df=df.drop_duplicates(subset=['股票代码'],keep='first')
CKPT='/tmp/radar_ckpt_'+d+'.json'
try: ck=json.load(open(CKPT))
except Exception: ck={'bars':{},'f10':{}}
if codes_cached is not None:
    codes=codes_cached
else:
    codes=[str(r['股票代码']).zfill(6) for _,r in df.iterrows() if not m.bad_name(str(r['股票简称']).strip())]
    __import__('json').dump(codes,open('_tmp/radar_codes.json','w'))
todo=[c for c in codes if not isinstance(ck['bars'].get(c),dict)]
print('候选',len(codes),'待填',len(todo))
sess=requests.Session()
from concurrent.futures import ThreadPoolExecutor
t0=time.time(); done=0
def one(c):
    try:
        bars=m.load_bars(c,d,sess)
        r20=m.r20_of(bars) if bars and len(bars)>=21 else None
        return c,{'r20':r20,'pos':m.pos_of(bars)}
    except Exception:
        return c,{'r20':None,'pos':None}
batch=todo[:400]
with ThreadPoolExecutor(max_workers=12) as ex:
    for c,ent in ex.map(one,batch):
        ck['bars'][c]=ent; done+=1
        if time.time()-t0>30: break
json.dump(ck,open(CKPT,'w'),ensure_ascii=False)
print('本轮填',done,'累计',len(ck['bars']))
