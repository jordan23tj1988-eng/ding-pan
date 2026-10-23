import json
d=json.load(open('_学习/总审_20261022.json',encoding='utf-8'))
print('KEYS:',list(d.keys()))
for k in ['schema_version','日期','来源']:
    print(k,'=',json.dumps(d[k],ensure_ascii=False)[:300])
print('--- 五路裁决 ---'); print(json.dumps(d['五路裁决'],ensure_ascii=False,indent=1)[:3000])
print('--- 总裁决 ---'); print(json.dumps(d['总裁决'],ensure_ascii=False,indent=1)[:3000])
