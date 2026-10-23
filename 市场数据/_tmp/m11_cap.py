import json
print('#### 能力预加载'); d=json.load(open('_学习/能力预加载_20261023.json',encoding='utf-8'))
print(json.dumps(d,ensure_ascii=False,indent=1)[:4000])
print('#### 战绩画像汇总'); 
try:
    d=json.load(open('_学习/子agent增强/_战绩画像汇总_20261023.json',encoding='utf-8'))
    print(json.dumps(d,ensure_ascii=False,indent=1)[:3500])
except Exception as e: print('ERR',e)
