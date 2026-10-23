import json
for r in ['auction','lhb','theme','logic','limitup']:
    d=json.load(open(f'_学习/交易计划_{r}_20261023.json',encoding='utf-8'))
    print('='*20,r,'keys',list(d.keys()))
    print('档位/仓位:',json.dumps({k:v for k,v in d.items() if isinstance(v,str) and len(v)<80},ensure_ascii=False))
    for b in d.get('buys',[]):
        print(json.dumps(b,ensure_ascii=False))
    print('SELLS:',json.dumps(d.get('sells'),ensure_ascii=False)[:600])
    print('NOTES:',json.dumps(d.get('notes'),ensure_ascii=False)[:900])
