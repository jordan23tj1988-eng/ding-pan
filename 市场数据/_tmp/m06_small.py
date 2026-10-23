import json
def show(p,keys=None):
    d=json.load(open(p,encoding='utf-8'))
    print('='*25,p)
    print(json.dumps(d,ensure_ascii=False,indent=1)[:6000])
for p in ['_学习/fact_20261023.json','_学习/风险日历_20261023.json','_学习/能力进化快照_20261023.json','_学习/待深挖清单_20261023.json','_学习/预判结算_20261022.json']:
    show(p)
