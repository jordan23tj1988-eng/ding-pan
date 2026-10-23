import json,os
for r in ['auction','lhb','theme','logic','limitup']:
    p=f'_学习/{r}判断_20261023.json'
    d=json.load(open(p,encoding='utf-8'))
    print('='*20,r,os.path.getsize(p))
    def walk(o,pre=''):
        if isinstance(o,dict):
            for k,v in o.items():
                t=type(v).__name__
                if isinstance(v,(dict,list)):
                    print(f'{pre}{k}: {t}[{len(v)}]')
                    if isinstance(v,dict) and len(pre)<4: walk(v,pre+'  ')
                else:
                    s=str(v)
                    print(f'{pre}{k}: {t} = {s[:110]}')
    walk(d)
