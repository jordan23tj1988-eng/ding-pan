import csv, statistics as st
rows=list(csv.DictReader(open('20261023/zt_pool.csv',encoding='utf-8-sig')))
print('n',len(rows))
def f(x):
    try: return float(x)
    except: return 0.0
zb=[int(f(r['炸板次数'])) for r in rows]
print('炸板合计',sum(zb),'炸板>0只数',sum(1 for x in zb if x>0))
fa=[f(r['封板资金'])/f(r['成交额']) for r in rows if f(r['成交额'])>0]
ff=[f(r['封板资金'])/f(r['流通市值']) for r in rows if f(r['流通市值'])>0]
print('封单/成交 median %.4f  mean %.4f'%(st.median(fa),st.mean(fa)))
print('封单/流通 median %.4f  mean %.4f'%(st.median(ff),st.mean(ff)))
def tm(s):
    s=s.strip()
    return s[:5] if s else ''
early=sum(1 for r in rows if tm(r['首次封板时间']) and tm(r['首次封板时间'])<='09:36')
b10=sum(1 for r in rows if tm(r['首次封板时间']) and tm(r['首次封板时间'])<='10:00')
late=sum(1 for r in rows if tm(r['首次封板时间']) and tm(r['首次封板时间'])>='13:01')
print('首封<=09:36',early,'<=10:00',b10,'>=13:01',late)
lb=[int(f(r['连板数'])) for r in rows]
from collections import Counter
print('连板分布',Counter(lb))
print('封板率 %.4f'%(82/(82+12)))
print('成交额合计亿 %.1f'%(sum(f(r['成交额']) for r in rows)/1e8))
