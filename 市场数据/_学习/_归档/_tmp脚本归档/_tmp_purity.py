import csv,json
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
for D in ['20261021','20261022','20261023']:
    rows=list(csv.DictReader(open(f'_学习/_席位动向/{D}.csv',encoding='utf-8')))
    dd=[r for r in rows if not is_int(r['类型']) and r['代码'][:2] not in ('11','12','90','20')]
    seen=set(); Q=[]
    for r in dd:
        k=(r['代码'],r['席位'])
        if k in seen: continue
        seen.add(k); Q.append(r)
    lhb=[r for r in csv.DictReader(open(f'{D}/lhb.csv',encoding='utf-8-sig')) if not is_int(r['上榜原因'])]
    stock={r['代码'] for r in lhb if r['代码'][:2] not in ('11','12')}
    sn=sum(float(r['净额']) for r in Q if r['代码'] in stock)
    net=sum(float(r['龙虎榜净买额']) for r in lhb if r['代码'][:2] not in ('11','12'))
    print(f'{D} 股票口径: 席位(买五)净额 {sn/1e8:.2f}亿 | 股票级净额 {net/1e8:.2f}亿 | 真实率 {net/sn*100 if sn else 0:.1f}% | 差额 {(sn-net)/1e8:.2f}亿 | 席位笔{len(Q)}')
