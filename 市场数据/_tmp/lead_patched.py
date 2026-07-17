# -*- coding: utf-8 -*-
"""坑18替代路: 腾讯qt批量quote重建spot同构DataFrame, monkeypatch akshare后重跑情绪先行指标"""
import sys,os,json,urllib.request
import pandas as pd
def tencent_spot(codes):
    rows=[]
    for i in range(0,len(codes),60):
        chunk=codes[i:i+60]
        q=','.join([('sh' if c[0] in '69' else 'bj' if c[:2] in ('92','43','83','87') or c[0]=='4' or c[0]=='8' else 'sz')+c for c in chunk])
        req=urllib.request.Request('http://qt.gtimg.cn/q='+q,headers={'User-Agent':'Mozilla/5.0'})
        txt=urllib.request.urlopen(req,timeout=10).read().decode('gbk',errors='ignore')
        for line in txt.strip().split(';'):
            if '~' not in line: continue
            f=line.split('~')
            try:
                rows.append({'代码':f[2],'名称':f[1],'最新价':float(f[3]),'昨收':float(f[4]),'今开':float(f[5]),'涨跌幅':float(f[32])})
            except Exception: pass
    return pd.DataFrame(rows)
# 昨日zt代码
z=pd.read_csv('20260715/zt_pool.csv',dtype={'代码':str})
codes=[c.zfill(6) for c in z['代码']]
SP=tencent_spot(codes)
print('腾讯quote取到',len(SP),'/',len(codes))
class FakeAK:
    @staticmethod
    def stock_zh_a_spot_em(): return SP.copy()
import importlib.util
spec=importlib.util.spec_from_file_location('lead','情绪先行指标.py')
m=importlib.util.module_from_spec(spec)
import akshare
sys.modules['akshare']=akshare
m.__dict__['__name__']='lead'
spec.loader.exec_module(m)
# monkeypatch: 替换premium_spot内部import的akshare
akshare.stock_zh_a_spot_em=FakeAK.stock_zh_a_spot_em
ths=m.load_ths() if hasattr(m,'load_ths') else None
t=m.load_out()
if ths is not None: m.run_day('20260716',ths,t,with_spot=True)
else:
    import inspect; print([x for x in dir(m) if not x.startswith('_')][:30])
m.save_out(t)
r=t.get('20260716',{})
print('溢价:',json.dumps(r.get('昨日涨停溢价'),ensure_ascii=False))
