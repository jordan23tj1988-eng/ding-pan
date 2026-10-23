import csv,json
D='20261022'
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
rows=list(csv.DictReader(open(f'_学习/_席位动向/{D}.csv',encoding='utf-8')))
dd=[r for r in rows if not is_int(r['类型']) and r['代码'][:2] not in ('11','12','90','20')]
seen=set(); Q=[]
for r in dd:
    k=(r['代码'],r['席位'])
    if k in seen: continue
    seen.add(k); Q.append(r)
lhb=list(csv.DictReader(open(f'{D}/lhb.csv',encoding='utf-8-sig')))
ded=[r for r in lhb if not is_int(r['上榜原因'])]
codes={r['代码'] for r in ded}
seatnet=sum(float(r['净额']) for r in Q if r['代码'] in codes)
stocknet=sum(float(r['龙虎榜净买额']) for r in ded)
print(f'20261022 席位净额 {seatnet/1e8:.2f}亿 股票级(值A) {stocknet/1e8:.2f}亿 差额 {(seatnet-stocknet)/1e8:.2f}亿 真实率 {stocknet/seatnet*100 if seatnet else 0:.1f}%')
