# -*- coding: utf-8 -*-
import json,csv,os,collections
os.chdir(r"D:/股票数据/市场数据")
D='20261020'
def rd(p):
    with open(p,encoding='utf-8-sig') as f: return list(csv.DictReader(f))
lhb=rd(f'{D}/lhb.csv')
bycode={}
for r in lhb:
    c=r['代码']
    if c not in bycode: bycode[c]=dict(r,_reasons=[])
    bycode[c]['_reasons'].append(r['上榜原因'])
sd=rd(f'_学习/_席位动向/{D}.csv')
fen=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
ds=json.load(open(f'_学习/龙虎榜双源校验_{D}.json',encoding='utf-8'))
dsi={x['代码']:x for x in ds['全量']}
zt={r['代码']:r for r in rd(f'{D}/zt_pool.csv')}
seats=collections.defaultdict(dict)
for r in sd:
    n=r['席位']; net=float(r['净额']); buy=float(r['买入金额'])
    d=seats[r['代码']]
    if n in d:
        d[n]['净额']+=net
    else:
        d[n]=dict(净额=net,买=buy)
rows=[]
for c,r in bycode.items():
    x=dsi.get(c,{})
    sa=[]
    for n,v in seats.get(c,{}).items():
        f=fen.get(n)
        if f and f['档'] in ('S','A'):
            sa.append((n,f['档'],f['样本'],f['收缩执1胜率'],f['收缩执1均涨'],f['小样本'],v['净额']/1e4))
    sa.sort(key=lambda t:-abs(t[-1]))
    rows.append(dict(代码=c,名称=r['名称'],涨跌幅=float(r['涨跌幅']),净买亿=round(float(r['龙虎榜净买额'])/1e8,4),
        占比=round(float(r['净买额占总成交比']),2),成交额亿=round(float(r['市场总成交额'])/1e8,2),
        判定=x.get('判定'),源2亿=x.get('源2买侧净额亿'),源1口径=x.get('源1口径'),
        涨停=c in zt, 连板=(zt[c]['连板数'] if c in zt else ''),行业=(zt[c]['所属行业'] if c in zt else ''),
        原因='|'.join(sorted(set(r['_reasons'])))[:40], SA=sa))
print('%-7s%-9s %6s %8s %7s %-4s %-6s %-6s %s'%('代码','名称','涨幅','净买亿','占比%','判定','涨停','连板','S/A席'))
for x in sorted(rows,key=lambda z:-z['净买亿']):
    s=';'.join('%s[%s n=%d %.1f%%/%.2f%%%s]净%.0f万'%(n[0][:12],n[1],n[2],n[3],n[4],'⚠' if n[5] else '',n[6]) for n in x['SA'][:3])
    print('%-7s%-9s %6.2f %8.4f %7.2f %-4s %-6s %-6s %s'%(x['代码'],x['名称'],x['涨跌幅'],x['净买亿'],x['占比'],x['判定'] or '-',x['涨停'],x['连板'],s))
print()
print('=== 强矛盾6 ===')
for c in ['000823','002245','002343','300006','601811','603466']:
    x=dsi.get(c,{}); print(c,x.get('名称'),x.get('源1净买亿'),x.get('源2买侧净额亿'),x.get('判定'),x.get('源1口径'))
print('=== 一致清单 ===')
print([ (c,dsi[c]['名称']) for c in dsi if dsi[c].get('判定')=='一致'])
