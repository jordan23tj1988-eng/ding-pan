import gzip,csv,json,collections,os
p='D:/股票数据/市场数据/_学习/竞价快照存档/20260911.csv.gz'
with gzip.open(p,'rt',encoding='utf-8-sig',newline='') as f:
 rows=list(csv.DictReader(f))
print('ROWS',len(rows)); print('FIELDS',list(rows[0]))
def num(r,k):
 try:return float(str(r.get(k,'')).replace(',',''))
 except:return None
# inspect values
for k in ['高开幅度','成交额','今开','昨收','最新价']:
 vals=[num(r,k) for r in rows]; vals=[x for x in vals if x is not None]
 print(k,'n',len(vals),'min',min(vals) if vals else None,'max',max(vals) if vals else None)
vals=[num(r,'高开幅度') for r in rows]
print('GAP', 'ge5',sum(x is not None and x>=5 for x in vals),'0to5',sum(x is not None and 0<=x<5 for x in vals),'lt0',sum(x is not None and x<0 for x in vals),'zero',sum(x==0 for x in vals if x is not None))
# likely one-word: latest? open=limit? identify names/columns
# top5 amount
rr=sorted([r for r in rows if num(r,'成交额') is not None],key=lambda r:num(r,'成交额'),reverse=True)[:5]
for r in rr: print('TOP',r.get('代码'),r.get('名称'),r.get('高开幅度'),r.get('成交额'),r.get('竞价额排名'))
# high open exact 10 and latest/open relation
print('HIGH10',sum(x is not None and x>=9.95 for x in vals))
# inspect rows with exact high open and top candidates
for r in [r for r in rows if (num(r,'高开幅度') or -999)>=9.95][:30]: print('H10ROW',r)
