import json
for r in ['auction','lhb','theme','logic','limitup']:
    d=json.load(open(f'_学习/能力回执_{r}_20261023.json',encoding='utf-8'))
    print('='*22,r)
    print(json.dumps(d,ensure_ascii=False,indent=1)[:2500])
