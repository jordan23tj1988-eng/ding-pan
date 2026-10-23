import os,json,csv,re,statistics
from pathlib import Path
from collections import Counter
B=Path(r'D:\股票数据\市场数据'); D='20260924'
def txt(p):
 b=Path(p).read_bytes()
 for e in ('utf-8-sig','utf-8','utf-16','gbk'):
  try:
   s=b.decode(e)
   if e=='utf-16' and '\x00' in s[:200]: continue
   return s
  except: pass
 return b.decode('utf-8','replace')
def js(p):
 try:return json.loads(txt(p))
 except Exception as e:return {'ERR':str(e)}
def rel(p):
 try:return str(Path(p).relative_to(B))
 except:return str(p)
def find(regex): return sorted([p for p in B.rglob('*') if p.is_file() and re.search(regex,p.name,re.I)],key=lambda p:str(p))
def compact(v):
 if isinstance(v,dict): return {k:compact(x) for k,x in v.items() if k in ('日期','date','路','来源','生成日','更新','样本','窗口','合计','基准','温度','温度档','涨停','炸板','跌停','封板率','炸板率','最高连板','连板梯队','结论','档位','置信度','执行胜率','执行均收','全场均收','胜率','均收','交易日数','按日','状态','持仓','positions','cash','funds','buys','sells','notes','标的','来源档','强度画像','链条','主线','荐票','判断','可证伪条件','独立盲区声明')}
 if isinstance(v,list): return [compact(x) for x in v[:10]]
 return v

print('## CSV')
for name in ['zt_pool.csv','dt_pool.csv','zb_pool.csv','strong_pool.csv']:
 p=B/D/name
 rows=list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
 print(name,'rows',len(rows),'fields',list(rows[0]) if rows else [])
 if rows:
  print('sample',rows[:2])
  for key in ['连板数','炸板次数','首次封板时间','封板资金','流通市值','涨停统计','名称','代码','行业']:
   if key in rows[0]:
    vals=[r.get(key,'') for r in rows]
    print(key,'count',sum(bool(x) for x in vals),'unique_sample',list(dict.fromkeys(vals))[:12])
  if '连板数' in rows[0]: print('连板分布',Counter(r.get('连板数','') for r in rows))
  if '炸板次数' in rows[0]: print('炸板>0',sum((r.get('炸板次数') or '0') not in ('','0','0.0') for r in rows))

print('\n## target files')
for regex in ['涨停质量荐票','训练','作战包_limitup_20260924','认知库_limitup','昨日复盘_limitup','领域手册_limitup','开盘验证维_20260924','日内温度_20260924','日内轮动_20260924','涨停对链条_20260924','题材归位_20260924','甜点_20260924']:
 ps=find(regex)
 print(regex,[rel(p) for p in ps[-15:]])
 for p in ps:
  if D in p.name and p.suffix in ('.json','.md'):
   x=js(p) if p.suffix=='.json' else txt(p)
   print(' ',rel(p), 'JSON',compact(x) if isinstance(x,(dict,list)) else x[:800])

print('\n## key jsons')
for p in [B/'_学习/_情绪先行指标.json',B/'_学习/_涨停质量库.json',B/'_学习/_模拟盘/limitup/状态.json']:
 x=js(p); print(rel(p));
 if p.name=='_情绪先行指标.json': print('D',compact(x.get(D)),'prev',compact(x.get('20260923')))
 elif p.name=='_涨停质量库.json': print('base',x.get('基准'),'rules',x.get('规则榜'),'env',x.get('环境规则'),'dims', {k: x.get('分板胜率',{}).get(k) for k in ['一维','连板x封单','连板x温度']})
 else: print(compact(x))

print('\n## latest cognition/handbook/work')
for prefix in ['认知库_limitup_','昨日复盘_limitup_','作战包_limitup_','领域手册_limitup_']:
 ps=find('^'+prefix)
 print(prefix,[rel(p) for p in ps[-10:]])
 if ps:
  p=ps[-1]; print('LATEST',rel(p));
  if p.suffix=='.json': print(compact(js(p)))
  else: print(txt(p)[:5000])

print('\n## temperature html')
p=B/'_学习/市场温度卡_20260924.html'; s=txt(p); print('len',len(s));
for term in ['温度','炸板','涨停','跌停','最高','连板','封板率']:
 print(term, re.sub('<[^>]+>',' ',s[max(0,s.find(term)-120):s.find(term)+500])[:620] if term in s else 'MISS')

print('\n## ifind')
for p in find('ifind查.*\\.py|ifind.*\\.py'): print(rel(p))
