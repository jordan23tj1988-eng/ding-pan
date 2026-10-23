import json
d=json.load(open('_学习/子agent增强/_战绩画像汇总_20261023.json',encoding='utf-8'))
print('top keys',list(d.keys()))
for k,v in d.items():
    if k!='五路': print(k,json.dumps(v,ensure_ascii=False)[:600])
for k,v in d.get('五路',{}).items():
    print('--',k,[kk for kk in v.keys()])
    for kk in v:
        if kk not in ('按日',): print('   ',kk,'=',json.dumps(v[kk],ensure_ascii=False)[:200])
