import csv,json,os
from statistics import mean
D='20261023'
q=json.load(open('_学习/_龙虎榜质量库.json',encoding='utf-8'))['因子']
def bk(f,b): return q[f]['桶'].get(b)
def bucket(f,x):
    if f=='净买占比':
        if x<=0: return '≤0净卖'
        if x<5: return '0-5%'
        if x<10: return '5-10%'
        if x<20: return '10-20%'
        return '>20%'
    if f=='换手率':
        if x<3: return '<3%锁仓'
        if x<15: return '3-15%'
        if x<30: return '15-30%'
        return '>30%高换手'
    if f=='流通市值':
        if x<30: return '<30亿'
        if x<100: return '30-100亿'
        if x<300: return '100-300亿'
        return '>300亿'
    if f=='股价':
        if x<5: return '<5元'
        if x<20: return '5-20元'
        return '>20元'
    if f=='位置60日':
        if x<30: return '低位<30%'
        if x<70: return '中位30-70%'
        return '高位>70%'
    if f=='多空比':
        if x<1: return '<1空头'
        if x<2: return '1-2'
        if x<3: return '2-3'
        return '≥3'
def bars(c):
    p=f'_学习/_bars_cache/{c}.csv'
    if not os.path.exists(p): return []
    out=[]
    for line in open(p,encoding='utf-8'):
        ps=line.strip().split(',')
        if len(ps)<5 or ps[0]=='date': continue
        try: out.append((ps[0],float(ps[1]),float(ps[2]),float(ps[3]),float(ps[4])))
        except: pass
    return out
def pos60(c):
    b=bars(c)
    if len(b)<61: return None
    w=b[-61:-1]  # 前60日（不含今日）
    hi=max(x[2] for x in w); lo=min(x[3] for x in w)
    close=b[-1][4]
    if hi==lo: return None
    return (close-lo)/(hi-lo)*100
lhb={r['代码']:r for r in csv.DictReader(open(f'{D}/lhb.csv',encoding='utf-8-sig')) if not any(k in r['上榜原因'] for k in ['连续','累计','严重异常'])}
zt={r['代码']:r for r in csv.DictReader(open(f'{D}/zt_pool.csv',encoding='utf-8-sig'))}
ctx=json.load(open('_学习/_tmp_ctx1023.json',encoding='utf-8'))
def score(c):
    z=zt.get(c); l=lhb.get(c)
    if not z or not l: return None
    npr=float(l['净买额占总成交比']); hs=float(z['换手率']); mc=float(z['流通市值'])/1e8; px=float(l['收盘价'])
    b1=float(l['龙虎榜买入额']); s1=float(l['龙虎榜卖出额']); ratio=b1/s1 if s1 else 99
    p60=pos60(c)
    rows=[('净买占比',npr,bucket('净买占比',npr)),('换手率',hs,bucket('换手率',hs)),('流通市值',mc,bucket('流通市值',mc)),('股价',px,bucket('股价',px)),('多空比',ratio,bucket('多空比',ratio))]
    if p60 is not None: rows.append(('位置60日',p60,bucket('位置60日',p60)))
    sal="; ".join(x["档"]+x["席位"][:10]+" 净%.3f亿n=%d"%(x["净"]/1e8,x["n"]) for x in ctx["sa"].get(c,[]))
    print("### %s %s | 双源=%s 源1=%s 源2=%s | S/A=%s"%(c,z["名称"],ctx["flag"].get(c),ctx["src1"].get(c),ctx["src2"].get(c),sal))
    print(f"    连板{z['连板数']} 统计{z['涨停统计']} 封单比{float(z['封板资金'])/float(z['成交额'])*100:.2f}% 炸{z['炸板次数']} 首封{z['首次封板时间']} 解读={l['解读']}")
    tot=0;cnt=0
    for f,v,b in rows:
        s=bk(f,b)
        print(f"    {f}={v:.2f} → {b}: n={s['n']} 胜{s['执1胜率']}% 均{s['执1均涨']}% (基准48.0/+0.37)")
        tot+=s['执1均涨']; cnt+=1
    print(f"    六因子均涨均值 {tot/cnt:.2f}% (简单平均，非模型分)")
for c in ['300296','603721','002354','301660','600215','600303','003021','001216','002724','688787','301313','002343']:
    score(c); print()
