import csv, statistics as st
rows=list(csv.DictReader(open('20261023/zt_pool.csv',encoding='utf-8-sig')))
def f(x):
    try: return float(x)
    except: return 0.0
def t(r): return (r['首次封板时间'] or '').strip()[:4]
def tt(r): return (r['首次封板时间'] or '').strip()[:5]
V={
 'first<=09:36': [r for r in rows if tt(r) and tt(r)<='09:36'],
 'first<=09:36 & zb0': [r for r in rows if tt(r) and tt(r)<='09:36' and int(f(r['炸板次数']))==0],
 'first==09:25': [r for r in rows if tt(r)=='09:25'],
 'first<=09:30': [r for r in rows if tt(r) and tt(r)<='09:30'],
 'first<=09:26': [r for r in rows if tt(r) and tt(r)<='09:26'],
 'first<=09:36 & lb1': [r for r in rows if tt(r) and tt(r)<='09:36' and int(f(r['连板数']))==1],
 '20cm & first<=09:36': [r for r in rows if tt(r) and tt(r)<='09:36' and (r['代码'][:2] in ('30','68'))],
}
for k,v in V.items(): print(k,len(v))
# 封单率 median variants
def med(lst): return st.median(lst) if lst else None
ff=[f(r['封板资金'])/f(r['流通市值']) for r in rows]
fa=[f(r['封板资金'])/f(r['成交额']) for r in rows]
no_yz=[r for r in rows if tt(r)!='09:25']
print('封单/流通 median all %.4f ; 非一字 %.4f'%(med(ff), med([f(r['封板资金'])/f(r['流通市值']) for r in no_yz])))
print('封单/成交 median all %.4f ; 非一字 %.4f'%(med(fa), med([f(r['封板资金'])/f(r['成交额']) for r in no_yz])))
