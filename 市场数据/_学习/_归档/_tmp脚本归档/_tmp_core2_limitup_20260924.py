import os, json, csv, re, statistics
B=r'D:\股票数据\市场数据'
def load(p):
 for e in ('utf-8-sig','utf-8','utf-16','gbk'):
  try:
   with open(p,encoding=e) as f:return json.load(f)
  except: pass

def listdir(rel):
 p=os.path.join(B,rel); print('DIR',rel)
 if os.path.isdir(p):
  for n in sorted(os.listdir(p)):
   if any(x in n for x in ['limitup','涨停','五路','领域','agent','作战','昨日','开盘','日内','ifind','归位','温度','先行']): print(n)
listdir('_agent规格'); listdir('_学习'); listdir('_学习/子agent增强'); listdir('_学习/开盘验证维'); listdir('_学习/日内温度'); listdir('_学习/日内轮动')
for rel in ['_学习/_市场温度表.json','_学习/_情绪先行指标.json','_学习/_涨停质量库.json','_学习/涨停质量荐票_20260924.json','_学习/涨停对链条_20260924.json','_学习/题材归位_20260924.json','_学习/子agent增强/战绩画像_limitup_20260924.json','_学习/子agent增强/认知库_limitup_20260923.json']:
 p=os.path.join(B,rel)
 if not os.path.exists(p):print('MISS',rel);continue
 x=load(p); print('FILE',rel)
 if rel.endswith('战绩画像_limitup_20260924.json'):
  print('合计',x.get('合计'),'按日',x.get('按日',{}).get('20260923'),x.get('按日',{}).get('20260924'))
 if rel.endswith('_情绪先行指标.json'):
  print('D',x.get('20260924')); print('PREV',x.get('20260923'))
 if rel.endswith('_涨停质量库.json'):
  print('TOPKEYS',list(x)[:20]); print('BASE', {k:x.get(k) for k in ['更新','基准执1胜率','基准执1均涨','基准执2胜率','基准执2均涨']})
 if rel.endswith('涨停质量荐票_20260924.json'):
  rows=x.get('明细',[]); print('N',len(rows));
  vals=[r.get('预测执1胜率') for r in rows if isinstance(r.get('预测执1胜率'),(int,float))]; avgs=[r.get('预测执1均涨') for r in rows if isinstance(r.get('预测执1均涨'),(int,float))]
  print('EXEC1 max median mean',max(vals),statistics.median(vals),round(statistics.mean(vals),3),'avgmean',round(statistics.mean(avgs),3))
  print('RULES',sum(bool(r.get('命中规则')) for r in rows), '可执行',sum(r.get('可执行') is True for r in rows))
  for r in rows:
   if r.get('代码') in ['601811','600825','001234','000850','002614','301699']:
    print('CAND', {k:r.get(k) for k in ['代码','名称','质量分','预测执1胜率','预测执1均涨','预测执2胜率','预测执2均涨','命中规则','抓龙率','来源档','可执行']})
 if rel.endswith('涨停对链条_20260924.json'):
  print('TOPICS')
  for t in x.get('题材线',[]): print({k:t.get(k) for k in ['题材','家数','最高连板','早封占比','开板占比','强度画像']})
 if rel.endswith('题材归位_20260924.json'):
  print('counts',x.get('counts'),x.get('档计数'), 'status',x.get('source_status'), 'missing',x.get('missing_fields'))
