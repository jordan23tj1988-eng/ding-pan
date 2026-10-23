import csv
from collections import Counter
rows=list(csv.DictReader(open('20261023/zt_pool.csv',encoding='utf-8-sig')))
def h(r,k): return (r[k] or '').strip()[:5]
first=[h(r,'首次封板时间') for r in rows]; last=[h(r,'最后封板时间') for r in rows]
print('first empty',sum(1 for x in first if not x),'last empty',sum(1 for x in last if not x))
print('首封 <13:01',sum(1 for x in first if x and x<'13:01'),'>=13:01',sum(1 for x in first if x and x>='13:01'))
print('末封 <13:01',sum(1 for x in last if x and x<'13:01'),'>=13:01',sum(1 for x in last if x and x>='13:01'))
print('末封 >=14:00',sum(1 for x in last if x and x>='14:00'))
b=Counter(x[:2] for x in first if x); print('首封小时分布',sorted(b.items()))
b2=Counter(x[:2] for x in last if x); print('末封小时分布',sorted(b2.items()))
for r in rows[:5]: print(r['代码'],r['首次封板时间'],r['最后封板时间'],r['炸板次数'])
