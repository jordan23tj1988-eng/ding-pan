import csv,json
from collections import defaultdict
D='20261023'
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
rows=list(csv.DictReader(open(f'_学习/_席位动向/{D}.csv',encoding='utf-8')))
dd=[r for r in rows if not is_int(r['类型']) and r['代码'][:2] not in ('11','12','90','20')]
seen=set(); Q=[]
for r in dd:
    k=(r['代码'],r['席位'])
    if k in seen: continue
    seen.add(k); Q.append(r)
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def dg(seat):
    v=pj.get(seat); return v['档'] if v else '未入档'
ctx=json.load(open('_学习/_tmp_ctx1023.json',encoding='utf-8'))
flag=ctx['flag']; src1=ctx['src1']
A_net=sum(float(r['净额']) for r in Q if dg(r['席位'])=='A')
A_net_ok=sum(float(r['净额']) for r in Q if dg(r['席位'])=='A' and flag.get(r['代码'])!='强矛盾' and (src1.get(r['代码']) or 0)>0)
zt={r['代码']:r for r in csv.DictReader(open(f'{D}/zt_pool.csv',encoding='utf-8-sig'))}
def fb(c):
    z=zt.get(c)
    if not z: return 0
    return float(z['封板资金'])/float(z['成交额'])*100
def okz(c):
    z=zt.get(c)
    return bool(z) and fb(c)>=5 and int(z['炸板次数'])<=3 and z['首次封板时间']<='140000'
A_net_ok2=sum(float(r['净额']) for r in Q if dg(r['席位'])=='A' and flag.get(r['代码'])!='强矛盾' and (src1.get(r['代码']) or 0)>0 and okz(r['代码']))
print(f'A档股票口径净额合计 {A_net/1e8:.3f}亿')
print(f'A档可用(非强矛盾∧源1>0) {A_net_ok/1e8:.3f}亿 = {A_net_ok/A_net*100:.1f}%')
print(f'A档可用(+封板三项过) {A_net_ok2/1e8:.3f}亿 = {A_net_ok2/A_net*100:.1f}%')
SA_net=sum(float(r['净额']) for r in Q if dg(r['席位']) in ('S','A'))
print(f'S/A 股票口径净额 {SA_net/1e8:.3f}亿, S/A可用(同上口径2) 计算中')
sa_ok=sum(float(r['净额']) for r in Q if dg(r['席位']) in ('S','A') and flag.get(r['代码'])!='强矛盾' and (src1.get(r['代码']) or 0)>0 and okz(r['代码']))
print(f'S/A可用(+封板三项) {sa_ok/1e8:.3f}亿 = {sa_ok/SA_net*100:.1f}%')
# 单笔最大
mx=max(Q,key=lambda r: float(r['买入金额']))
print('单笔最大买额',mx['代码'],mx['名称'],mx['席位'],float(mx['买入金额'])/1e8)
sa=[r for r in Q if dg(r['席位']) in ('S','A')]
mx2=max(sa,key=lambda r: float(r['买入金额']))
print('S/A单笔最大',mx2['代码'],mx2['名称'],mx2['席位'],float(mx2['买入金额'])/1e8)
# 席位净额 vs 股票级净额（当日榜代码）
lhb=list(csv.DictReader(open(f'{D}/lhb.csv',encoding='utf-8-sig')))
ded=[r for r in lhb if not is_int(r['上榜原因'])]
codes={r['代码'] for r in ded}
seatnet=sum(float(r['净额']) for r in Q if r['代码'] in codes)
stocknet=sum(float(r['龙虎榜净买额']) for r in ded)
print(f'席位(买五)净额合计 {seatnet/1e8:.2f}亿 | 股票级净额合计(值A) {stocknet/1e8:.2f}亿 | 差额 {(seatnet-stocknet)/1e8:.2f}亿')
# 双源分布
ds=json.load(open(f'_学习/龙虎榜双源校验_{D}.json',encoding='utf-8'))
print('双源',json.dumps(ds['metrics'],ensure_ascii=False))
from collections import Counter
print(Counter(r['判定'] for r in ds['全量']))
