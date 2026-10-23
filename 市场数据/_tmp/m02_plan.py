import json
for r in ['auction','lhb','theme','logic','limitup']:
    p=f'_学习/交易计划_{r}_20261023.json'
    d=json.load(open(p,encoding='utf-8'))
    print('='*25,r)
    print(json.dumps(d,ensure_ascii=False,indent=1))
