import os, json, csv, re, statistics
B = r'D:\股票数据\市场数据'
D='20260924'
patterns = ['领域手册_limitup','五路子agent规格','昨日复盘_limitup','作战包_limitup','质量训练','开盘验证维','日内温度','日内轮动','ifind查','情绪先行指标','市场温度表','题材归位','涨停质量荐票','涨停对链条','涨停甜点','认知库_limitup','战绩画像_limitup']
found=[]
for root, dirs, files in os.walk(B):
    dirs[:] = [x for x in dirs if x not in {'.git','node_modules','__pycache__'}]
    for fn in files:
        if any(p in fn for p in patterns): found.append(os.path.relpath(os.path.join(root,fn),B))
print('FOUND')
for x in sorted(found): print(x)

def load(p):
    for enc in ('utf-8-sig','utf-8','utf-16','gbk'):
        try:
            with open(p,encoding=enc) as f: return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError): pass
    return None

def show_json(rel):
    p=os.path.join(B,rel)
    if not os.path.exists(p): print('MISS',rel); return
    x=load(p); print('JSON',rel,'type',type(x).__name__)
    if isinstance(x,dict): print('KEYS',list(x)[:30])
    if isinstance(x,list): print('LEN',len(x),'HEAD',x[:2])

for rel in [
 '20260924/summary.json','_学习/_市场温度表.json','_学习/_情绪先行指标.json',
 '_学习/子agent增强/战绩画像_limitup_20260924.json','_学习/子agent增强/认知库_limitup_20260923.json',
 '_学习/涨停质量荐票_20260924.json','_学习/涨停对链条_20260924.json',
 '_学习/题材归位_20260924.json','_学习/_运行状态/limitup_20260924.json',
 '_学习/_模拟盘/limitup/状态.json']:
    show_json(rel)

for rel in ['20260924/zt_pool.csv','20260924/dt_pool.csv','20260924/zb_pool.csv','20260924/strong_pool.csv']:
 p=os.path.join(B,rel)
 if not os.path.exists(p): print('MISSCSV',rel); continue
 with open(p,encoding='utf-8-sig',newline='') as f:
  rows=list(csv.DictReader(f))
 print('CSV',rel,'N',len(rows),'FIELDS',list(rows[0]) if rows else [])
 if rel.endswith('zt_pool.csv'):
  for r in rows:
   if str(r.get('连板数','')).strip() in {'5','4','3','2'}:
    print('ZT', {k:r.get(k) for k in ['代码','名称','连板数','首次封板时间','炸板次数','封板资金','涨停统计','流通市值','换手率','最新价']})

# compact quality file rows and source/baseline
p=os.path.join(B,'_学习/涨停质量荐票_20260924.json')
if os.path.exists(p):
 x=load(p)
 if isinstance(x,dict):
  for k in x:
   v=x[k]
   if isinstance(v,(str,int,float)) or k in ('更新','基准','统计','全池','荐票'):
    print('QTOP',k,repr(v)[:800])
  for k in ('rows','明细','data','票池','荐票'):
   if isinstance(x.get(k),list):
    print('QLIST',k,len(x[k]))
    for r in x[k][:8]: print('QROW', {a:r.get(a) for a in ['代码','名称','质量分','预测执1胜率','预测执1均涨','预测执2胜率','命中规则','抓龙率','来源档','可执行'] if isinstance(r,dict)})
