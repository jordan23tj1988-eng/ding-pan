# -*- coding: utf-8 -*-
import json,csv,os,collections
os.chdir(r"D:/股票数据/市场数据")
D='20261020'
def rd(p):
    with open(p,encoding='utf-8-sig') as f: return list(csv.DictReader(f))
lhb=rd(f'{D}/lhb.csv')
print('lhb rows',len(lhb))
# dedupe by code
bycode={}
for r in lhb:
    c=r['代码']
    if c not in bycode: bycode[c]=r
print('uniq codes',len(bycode))
for c,r in bycode.items():
    r['_reasons']=set()
for r in lhb: bycode[r['代码']]['_reasons'].add(r['上榜原因'])

sd=rd(f'_学习/_席位动向/{D}.csv')
print('seat rows',len(sd))
fen=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def seatinfo(n): return fen.get(n)
# aggregate seats by code
agg=collections.defaultdict(list)
for r in sd:
    agg[r['代码']].append(r)
# dedupe seat rows? same seat may appear multiple times for multiple 上榜原因
print('seat codes',len(agg))

# 双源校验
ds=json.load(open(f'_学习/龙虎榜双源校验_{D}.json',encoding='utf-8'))
print('ds keys',list(ds.keys())[:12])
print('ds summary',json.dumps(ds.get('统计',ds.get('summary')),ensure_ascii=False)[:600])
items=ds.get('全量') or ds.get('明细')
print('ds items',len(items)); print(json.dumps(items[0],ensure_ascii=False)[:800])
