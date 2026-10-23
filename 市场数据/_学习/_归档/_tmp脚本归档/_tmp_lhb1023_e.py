import csv,json
D='20261023'
zt={r['代码']:r for r in csv.DictReader(open(f'{D}/zt_pool.csv',encoding='utf-8-sig'))}
lhb=list(csv.DictReader(open(f'{D}/lhb.csv',encoding='utf-8-sig')))
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
lh={}
for r in lhb:
    if is_int(r['上榜原因']): continue
    lh.setdefault(r['代码'],r)
codes=['300296','603721','002354','301660','600215','603028','920091','688787','003021','001216','002343','301313','600303','002724']
def f(x):
    try: return float(x)
    except: return float('nan')
for c in codes:
    z=zt.get(c); l=lh.get(c)
    if not z: print(c,'不在涨停池'); continue
    fb=f(z['封板资金'])/f(z['成交额'])*100
    np_=f(l['净买额占总成交比']) if l else float('nan')
    print(f"{c} {z['名称']} 涨{f(z['涨跌幅']):.2f}% 连板{z['连板数']} 统计{z['涨停统计']} 换手{f(z['换手率']):.2f}% 流通{f(z['流通市值'])/1e8:.1f}亿 成交{f(z['成交额'])/1e8:.2f}亿 封单{f(z['封板资金'])/1e8:.2f}亿 封单比{fb:.2f}% 炸{z['炸板次数']} 首封{z['首次封板时间']} 末封{z['最后封板时间']} 行业{z['所属行业']} | 源1={f(l['龙虎榜净买额'])/1e8 if l else 'NA'} 净买占比={np_:.2f} 解读={l['解读'] if l else ''}")
