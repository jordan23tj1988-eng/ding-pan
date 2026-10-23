import json,sys
r=sys.argv[1]
d=json.load(open(f'_学习/{r}判断_20261023.json',encoding='utf-8'))
print(json.dumps(d,ensure_ascii=False,indent=1))
