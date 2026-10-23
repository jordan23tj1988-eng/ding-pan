import csv, statistics as st, os
def load(d):
    p=f'{d}/zt_pool.csv'
    if not os.path.exists(p): return None
    return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def f(x):
    try: return float(x)
    except: return 0.0
def ts(s):
    s=(s or '').strip().replace(':','')
    try: return int(s)
    except: return None
for d in ['20261021','20261022','20261023']:
    rows=load(d)
    if rows is None: print(d,'NO FILE'); continue
    n=len(rows)
    zb=[int(f(r['炸板次数'])) for r in rows]
    ff=[f(r['封板资金'])/f(r['流通市值']) for r in rows if f(r['流通市值'])>0]
    fa=[f(r['封板资金'])/f(r['成交额']) for r in rows if f(r['成交额'])>0]
    first=[ts(r['首次封板时间']) for r in rows]
    yz=sum(1 for t in first if t and t<=92600)
    early=sum(1 for t in first if t and t<=93600)
    l1300=sum(1 for t in first if t and t>=130000)
    print(d,'n=%d 炸合计=%d 炸>0=%d 一字=%d 首封<=09:36=%d 首封>=13:00=%d 封单/流通中位=%.4f 均值=%.4f 封单/成交中位=%.4f'%(n,sum(zb),sum(1 for x in zb if x>0),yz,early,l1300,st.median(ff),st.mean(ff),st.median(fa)))
