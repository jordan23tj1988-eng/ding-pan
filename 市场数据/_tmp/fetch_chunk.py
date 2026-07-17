# -*- coding: utf-8 -*-
"""分块增量fetch(沙箱42s墙): 用训练模块自身needs逻辑,todo存json,每次跑一批,跑完删todo。"""
import sys,os,json,importlib.util
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("qt","涨停质量训练.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
import pandas as pd
TODO='_tmp/fetch_todo.json'
if not os.path.isfile(TODO):
    P=pd.read_pickle('_学习/_P_stage.pkl')
    last=P.groupby('代码')['日'].max().to_dict()
    # 今日新涨停也纳入
    import csv
    for row in csv.DictReader(open('20260716/zt_pool.csv',encoding='utf-8-sig')):
        last[row['代码'].zfill(6)]='20260716'
    # 模拟盘持仓+昨日五路荐票/池代码
    extra=set()
    for r in ['auction','lhb','theme','logic','limitup','master']:
        try:
            st=json.load(open(f'_学习/_模拟盘/{r}/状态.json',encoding='utf-8'))
            for h in st.get('持仓',[]) or []: extra.add(str(h.get('code') or h.get('代码')).zfill(6))
        except Exception: pass
    for f in ['席位荐票_20260715.json','题材荐票_20260715.json','逻辑荐票_20260715.json','涨停质量荐票_20260715.json','竞价池发出_20260715.json']:
        try:
            j=json.load(open('_学习/'+f,encoding='utf-8')); s=json.dumps(j)
            import re
            for c in re.findall(r'"(\d{6})"',s): extra.add(c)
        except Exception: pass
    for c in extra: last.setdefault(c,'20260715')
    codes=sorted(last)
    def needs(c):
        f=os.path.join(m.CDIR,c+'.csv')
        if not os.path.isfile(f): return True
        try:
            head=open(f,encoding='utf-8').readline()
            if 'volume' not in head: return True
            b=pd.read_csv(f); dates=b['date'].astype(str).str.replace('-','')
            return int((dates>str(last[c])).sum())<2
        except Exception: return True
    todo=[c for c in codes if needs(c)]
    json.dump(todo,open(TODO,'w')); print('todo总数',len(todo))
todo=json.load(open(TODO))
batch=todo[:180]; rest=todo[180:]
if batch:
    m._fetch(batch,{c:"20260716" for c in batch})
    json.dump(rest,open(TODO,'w'))
print('done batch',len(batch),'rest',len(rest))
