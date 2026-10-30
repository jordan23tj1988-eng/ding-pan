# -*- coding: utf-8 -*-
import sys, io, csv, os
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
zt = {r['代码']: r for r in csv.DictReader(open(B+'20261029/zt_pool.csv', encoding='utf-8-sig'))}
def pos(c):
    f = B + '_学习/_bars_cache/' + c + '.csv'
    if not os.path.isfile(f): return None
    b = pd.read_csv(f); b['date'] = b['date'].astype(str).str.replace('-', ''); b = b.sort_values('date')
    cl = b['close'].astype(float)
    r20 = (cl.iloc[-1]/cl.iloc[-21]-1)*100
    r60 = (cl.iloc[-1]/cl.iloc[-61]-1)*100 if len(cl) > 61 else None
    r250 = (cl.iloc[-1]/cl.iloc[-251]-1)*100 if len(cl) > 251 else None
    return dict(close=round(cl.iloc[-1],2), r20=round(r20,1), r60=round(r60,1) if r60 else None,
                r250=round(r250,1) if r250 else None, dist_hi=round((cl.iloc[-1]/cl.tail(250).max()-1)*100,1))
for c in ['001219','605338','603536','605179','002862']:
    r = zt[c]
    fb = float(r['封板资金'])/float(r['成交额'])*100
    print(c, r['名称'], r['连板数'], '板', '首封', r['首次封板时间'], '炸', r['炸板次数'],
          f'封单/成交{fb:.1f}%', f"换手{r['换手率']:.1f}%", f"流通{float(r['流通市值'])/1e8:.0f}亿", pos(c))
