# -*- coding: utf-8 -*-
import sys,importlib.util,os
spec=importlib.util.spec_from_file_location("z","涨停质量训练.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
F=m._load_factors()
last=F.groupby('代码')['日'].max().to_dict()
codes=list(F['代码'].unique())
def needs(c):
    f=os.path.join(m.CDIR,c+".csv")
    if not os.path.isfile(f): return True
    try:
        import pandas as pd
        b=pd.read_csv(f); dates=b['date'].astype(str).str.replace('-','')
        return int((dates>str(last[c])).sum())<2
    except Exception: return True
todo=[c for c in codes if needs(c)]
n=int(sys.argv[1]) if len(sys.argv)>1 else 130
batch=todo[:n]
print(f"待拉{len(todo)},本批{len(batch)}")
if batch: m._fetch(batch,{c:'99999999' for c in batch})  # 强制视为需拉
print("批完成,剩余",len(todo)-len(batch))
