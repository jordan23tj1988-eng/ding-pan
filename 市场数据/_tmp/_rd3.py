# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
z = json.loads(open(B+'_学习/总审_20261028.json', encoding='utf-8-sig').read())
print('--- 指派清单 ---')
print(json.dumps(z.get('指派清单'), ensure_ascii=False, indent=1))
print('--- 能力承接 ---')
print(json.dumps(z.get('能力承接'), ensure_ascii=False, indent=1)[:3000])
print('--- 五路裁决(logic部分) ---')
print(json.dumps(z.get('五路裁决'), ensure_ascii=False, indent=1)[:4000])
