# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def jload(p):
    return json.loads(open(B+p, encoding='utf-8-sig').read())

print('#'*30, '能力预加载')
print(json.dumps(jload('_学习/能力预加载_20261029.json'), ensure_ascii=False, indent=1)[:6000])

print('#'*30, '总审_20261028 keys')
z = jload('_学习/总审_20261028.json')
print(type(z), list(z.keys()) if isinstance(z, dict) else len(z))
