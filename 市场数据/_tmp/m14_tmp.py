import json
t=json.load(open('_学习/_市场温度表.json',encoding='utf-8'))
print(type(t), list(t.keys())[:8] if isinstance(t,dict) else len(t))
rows = t if isinstance(t,list) else t.get('日序列') or t.get('明细') or t
if isinstance(rows,list):
    for r in rows[-4:]: print(json.dumps(r,ensure_ascii=False))
elif isinstance(rows,dict):
    for k in ['20261019','20261020','20261021','20261022','20261023']:
        if k in rows: print(k, json.dumps(rows[k],ensure_ascii=False)[:500])
