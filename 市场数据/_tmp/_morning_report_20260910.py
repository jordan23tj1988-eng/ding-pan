import json, gzip, os, csv
from collections import Counter
base=r'D:/股票数据/市场数据/_学习'
d='20260910'; prev='20260908'

def load(p):
    with open(p,encoding='utf-8-sig') as f:return json.load(f)
print('PREV',prev)
for p in [f'{base}/auction判断_{prev}.json',f'{base}/推演_{prev}.json',f'{base}/五路判断_{prev}/auction.json']:
    print('FILE',os.path.basename(p),os.path.exists(p))
    if os.path.exists(p):
      x=load(p); print(json.dumps(x,ensure_ascii=False)[:12000])
# snapshot
p=f'{base}/竞价快照存档/{d}.csv.gz'
with gzip.open(p,'rt',encoding='utf-8-sig',newline='') as f:
 rows=list(csv.DictReader(f))
print('ROWS',len(rows)); print('FIELDS',list(rows[0]) if rows else [])
def num(r,k):
 try:return float(str(r.get(k,'')).replace(',',''))
 except:return None
# identify columns
for k in ['高开幅度','成交额','竞价额排名','名称','代码']:
 print('COL',k, k in (rows[0] if rows else {}))
vals=[num(r,'高开幅度') for r in rows]; vals=[v for v in vals if v is not None]
print('DISTRIBUTION', 'ge5',sum(v>=5 for v in vals),'0to5',sum(0<=v<5 for v in vals),'le0',sum(v<0 for v in vals),'eq0',sum(v==0 for v in vals))
# one-word proxy: current open equals limit? inspect columns
for r in rows[:2]: print('SAMPLE',r)
# top5
rr=sorted([r for r in rows if num(r,'成交额') is not None],key=lambda r:num(r,'成交额'),reverse=True)[:5]
print('TOP5',json.dumps([{k:r.get(k) for k in ['代码','名称','今开','昨收','高开幅度','成交额','竞价额排名']} for r in rr],ensure_ascii=False))
