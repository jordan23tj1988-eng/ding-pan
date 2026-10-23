import json
d=json.load(open('_学习/总审_20261022.json',encoding='utf-8'))
for k in ['指派清单','线索跟踪']:
    print('='*20,k); print(json.dumps(d[k],ensure_ascii=False,indent=1))
