import os,json,statistics,csv
B=r'D:\股票数据\市场数据'
def load(rel):
 p=os.path.join(B,rel)
 for e in ('utf-8-sig','utf-8','utf-16','gbk'):
  try:
   with open(p,encoding=e) as f:return json.load(f)
  except:pass
for rel in ['_学习/_涨停质量库.json','_学习/涨停质量荐票_20260924.json','_学习/题材归位_20260924.json']:
 x=load(rel); print('FILE',rel)
 if rel.endswith('_涨停质量库.json'):
  for k in ['更新','窗口','样本','基准','活跃因子','环境规则','分板胜率']:
   print(k,repr(x.get(k))[:3000])
 if rel.endswith('涨停质量荐票_20260924.json'):
  rows=x['明细'];
  for r in rows[:12]: print({k:r.get(k) for k in ['代码','名称','质量分','预测执1胜率','预测执1均涨','预测执2胜率','预测执2均涨','抓龙率','来源档','命中规则']})
 if rel.endswith('题材归位_20260924.json'):
  print('keys',list(x)); print('first mapping',list(x.get('映射',{}).items())[:5]); print('source',x.get('来源明细'))
# zb detail
p=os.path.join(B,'20260924/zb_pool.csv')
with open(p,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
print('ZB')
for r in rows: print({k:r.get(k) for k in ['代码','名称','涨跌幅','最新价','成交额','流通市值','换手率','涨速','首次封板时间','炸板次数','所属行业']})
