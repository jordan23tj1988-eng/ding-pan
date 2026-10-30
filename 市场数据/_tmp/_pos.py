# -*- coding: utf-8 -*-
import sys, io, json, csv, os
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
zt = {r['代码']: r for r in csv.DictReader(open(B+'20261029/zt_pool.csv', encoding='utf-8-sig'))}
def pos(c):
    f = B + '_学习/_bars_cache/' + c + '.csv'
    if not os.path.isfile(f): return None
    b = pd.read_csv(f); b['date'] = b['date'].astype(str).str.replace('-', '')
    b = b.sort_values('date')
    last = b.iloc[-1]
    cl = b['close'].astype(float)
    r20 = (cl.iloc[-1]/cl.iloc[-21]-1)*100 if len(cl) > 21 else None
    r60 = (cl.iloc[-1]/cl.iloc[-61]-1)*100 if len(cl) > 61 else None
    r250 = (cl.iloc[-1]/cl.iloc[-251]-1)*100 if len(cl) > 251 else None
    hi = cl.tail(250).max()
    return dict(date=last['date'], close=float(last['close']), r20=round(r20,2) if r20 is not None else None,
                r60=round(r60,2) if r60 is not None else None, r250=round(r250,2) if r250 is not None else None,
                dist_hi=round((cl.iloc[-1]/hi-1)*100,2), n=len(cl))
for c in ['600592','603703','600118','301079','603131','002526','601956']:
    print(c, zt[c]['名称'], '最新价', zt[c]['最新价'], pos(c))
