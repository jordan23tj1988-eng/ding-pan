import os, json, csv, glob
base = r'D:/股票数据/市场数据'
files = [
'20260910/zt_pool.csv','20260910/zb_pool.csv','20260910/dt_pool.csv','20260910/strong_pool.csv','20260910/summary.json',
'_学习/_市场温度表.json','_学习/_情绪先行指标.json','_学习/fact_20260910.json','_学习/涨停质量荐票_20260910.json','_学习/_涨停质量库.json','_学习/_涨停质量反思.jsonl','_学习/_质量荐票结算.jsonl','_学习/_荐票逐票结算.jsonl','_学习/子agent增强/战绩画像_limitup_20260910.json','_学习/题材归位_20260910.json','_学习/涨停对链条_20260910.json','_学习/_模拟盘/limitup/状态.json','_agent规格/12_涨停复盘agent.md']
for rel in files:
    p=os.path.join(base, rel)
    print('\n###', rel, 'EXISTS', os.path.exists(p), 'SIZE', os.path.getsize(p) if os.path.exists(p) else '-')
    if not os.path.exists(p): continue
    try:
        if rel.endswith('.csv'):
            with open(p, encoding='utf-8-sig', newline='') as f:
                r=csv.DictReader(f); rows=list(r)
            print('CSV rows',len(rows),'fields',r.fieldnames)
            for x in rows[:8]: print(x)
        elif rel.endswith('.jsonl'):
            with open(p,encoding='utf-8-sig') as f:
                lines=[x.strip() for x in f if x.strip()]
            print('JSONL lines',len(lines))
            for x in lines[-3:]:
                try: print(json.dumps(json.loads(x),ensure_ascii=False)[:4000])
                except: print(x[:1000])
        elif rel.endswith('.json'):
            for enc in ['utf-8-sig','utf-16','gbk']:
                try:
                    with open(p,encoding=enc) as f: obj=json.load(f)
                    break
                except Exception as e: obj=None
            if isinstance(obj,dict):
                print('keys', list(obj.keys()))
                print(json.dumps(obj,ensure_ascii=False,indent=2)[:12000])
            else: print('not dict or failed')
        else:
            with open(p,encoding='utf-8-sig',errors='replace') as f: txt=f.read()
            print(txt[:12000])
    except Exception as e: print('ERROR',repr(e))
print('\n### history files')
for pattern in ['_学习/涨停复盘存档/*','_学习/子agent增强/认知库_limitup_*.json','_学习/昨日复盘_limitup_*.json','_学习/_总审_20260909.json','_学习/总审_20260909.json','_学习/limitup判断_*.json','_学习/limitup_body_*.html','_学习/交易计划_limitup_*.json']:
    paths=glob.glob(os.path.join(base,pattern)); print(pattern, len(paths), [os.path.basename(x) for x in sorted(paths)[-10:]])
