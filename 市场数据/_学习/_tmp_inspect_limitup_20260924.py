import os, json, csv, re, glob, statistics
from pathlib import Path
BASE = Path(r'D:\股票数据\市场数据')
D='20260924'

def load_text(p):
    b=Path(p).read_bytes()
    for enc in ('utf-8-sig','utf-8','utf-16','gbk'):
        try:
            s=b.decode(enc)
            if enc=='utf-16' and '\x00' in s[:200]:
                continue
            return s,enc
        except Exception:
            pass
    return b.decode('utf-8','replace'),'replace'

def load_json(p):
    s,e=load_text(p)
    try:return json.loads(s),e
    except Exception as x:return {'__parse_error__':str(x),'__text_head__':s[:300]},e

def find_names(pattern):
    out=[]
    for p in BASE.rglob('*'):
        if p.is_file() and re.search(pattern,p.name,re.I): out.append(p)
    return sorted(out, key=lambda p:str(p))

def show_json(label,p,depth=2):
    x,e=load_json(p)
    print(f'\n### {label}: {p.relative_to(BASE)} enc={e} type={type(x).__name__}')
    if isinstance(x,dict):
        print('keys=',list(x.keys())[:80])
        items=list(x.items())
        if len(items)>20:
            items=[(k,x[k]) for k in ['20260924','20260923','20260922','20260824'] if k in x]
        for k,v in items:
            if k.startswith('__'): continue
            if isinstance(v,(str,int,float,bool)) or v is None: print(f'{k}={v!r}')
            elif isinstance(v,list): print(f'{k}=list(len={len(v)}) sample={v[:2]!r}')
            elif isinstance(v,dict): print(f'{k}=dict(keys={list(v)[:20]}) sample={v!r}')
    elif isinstance(x,list): print('len=',len(x),'sample=',x[:2])

print('BASE',BASE)
# exact likely inputs
for rel in [
 '20260924/summary.json','_学习/总审_20260923.json','_学习/子agent增强/战绩画像_limitup_20260924.json',
 '_学习/_涨停质量库.json','_学习/_情绪先行指标.json','_学习/_模拟盘/limitup/状态.json',
]:
 p=BASE/rel
 if p.exists(): show_json(rel,p)
 else: print('\nMISSING',rel)

# latest files by prefix and date
for prefix in ['认知库_limitup_','昨日复盘_limitup_','作战包_limitup_','战绩画像_limitup_']:
 arr=sorted((p for p in (BASE/'_学习/子agent增强').glob(prefix+'*.json') if p.is_file()),key=lambda p:p.name)
 print('\n###',prefix,'files=',[p.name for p in arr[-8:]])
 if arr: show_json('latest '+prefix,arr[-1])

# all target-day related artifacts
patterns=['涨停质量荐票','质量训练','开盘验证维','日内温度','日内轮动','市场温度卡','涨停对链条','题材归位','甜点','训练']
print('\n### matching artifacts')
for pat in patterns:
 arr=find_names(pat)
 day=[p for p in arr if D in p.name or D in str(p)]
 print(pat, [str(p.relative_to(BASE)) for p in day[-20:]])

# CSV stats
for rel in ['20260924/zt_pool.csv','20260924/dt_pool.csv','20260924/zb_pool.csv','20260924/strong_pool.csv']:
 p=BASE/rel
 if not p.exists(): continue
 print('\n### CSV',rel)
 with p.open('r',encoding='utf-8-sig',newline='') as f:
  rows=list(csv.DictReader(f))
 print('rows',len(rows),'fields',list(rows[0]) if rows else [])
 for r in rows[:3]: print(r)
 if '连板数' in (rows[0] if rows else {}):
  from collections import Counter
  print('连板分布',Counter(r.get('连板数','') for r in rows))
 if '炸板次数' in (rows[0] if rows else {}):
  vals=[]
  for r in rows:
   try: vals.append(float(r.get('炸板次数') or 0))
   except: pass
  print('炸板次数>0',sum(v>0 for v in vals),'max',max(vals) if vals else None)

# HTML headings/snippets
for p in [BASE/'_学习/市场温度卡_20260924.html']:
 if p.exists():
  s,e=load_text(p); print('\n### HTML',p.relative_to(BASE),'enc',e,'len',len(s))
  print('headings',re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>',s,re.S)[:30])
  for term in ['温度','炸板','涨停','跌停','连板','封板率']:
   ix=s.find(term)
   print(term, re.sub('<[^>]+>',' ',s[max(0,ix-180):ix+500])[:700] if ix>=0 else 'NOT FOUND')

# find ifind scripts and relevant route scripts
print('\n### ifind candidates')
for p in find_names(r'ifind查|ifind.*\.py'):
 print(p.relative_to(BASE))
print('\n### verification candidates')
for p in find_names(r'limitup_verify|验证|校验body|judgment'):
 if p.suffix=='.py': print(p.relative_to(BASE))
