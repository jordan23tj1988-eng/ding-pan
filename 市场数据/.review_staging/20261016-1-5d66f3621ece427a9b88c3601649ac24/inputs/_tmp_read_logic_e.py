# -*- coding: utf-8 -*-
import json, io, sys, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/_学习/'
R = 'D:/股票数据/市场数据/'
def rd(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

print("===== zt_pool_20261016 =====")
rows = list(csv.DictReader(open(R+'20261016/zt_pool.csv', encoding='utf-8-sig')))
print("cols:", list(rows[0].keys()))
print("count:", len(rows))
for r in rows:
    print("|".join(str(r.get(c,'')) for c in ['\ufeff序号','代码','名称','连板数','首次封板时间','最后封板时间','炸板次数','换手率','成交额','封板资金','流通市值']))
