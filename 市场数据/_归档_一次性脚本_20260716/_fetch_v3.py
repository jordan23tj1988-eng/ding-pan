# -*- coding: utf-8 -*-
"""_fetch_v3.py 分批增量拉6列K线(带截止时间,反复跑直到 剩余0)"""
import os,glob,time,datetime,sys
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); CDIR=os.path.join(BASE,"_学习","_bars_cache")
import 涨停质量训练 as Q
P=Q._factor_table(); codes=sorted(P['代码'].unique())
def needs(c):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return True
    try: return 'volume' not in open(f,encoding='utf-8').readline()
    except Exception: return True
todo=[c for c in codes if needs(c)]
print(f"剩余{len(todo)}/{len(codes)}",flush=True)
if todo:
    import akshare as ak
    from concurrent.futures import ThreadPoolExecutor
    DEADLINE=time.time()+float(sys.argv[1]) if len(sys.argv)>1 else time.time()+38
    def one(c):
        if time.time()>DEADLINE: return
        try:
            pre="sh" if c[0] in "69" else ("bj" if c[0] in "48" else "sz")
            b=ak.stock_zh_a_daily(symbol=pre+c,start_date="20260101",end_date=datetime.date.today().strftime("%Y%m%d"))
            b[["date","open","high","low","close","volume"]].to_csv(os.path.join(CDIR,c+".csv"),index=False)
        except Exception as e: open(os.path.join(CDIR,c+".err"),"w").write(str(e)[:80])
    with ThreadPoolExecutor(max_workers=24) as ex: list(ex.map(one,todo))
    print("本轮后剩余:",sum(1 for c in codes if needs(c)),flush=True)
