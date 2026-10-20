# -*- coding: utf-8 -*-
import json,csv,os,collections
os.chdir(r"D:/股票数据/市场数据"); D='20261020'
def rd(p):
    with open(p,encoding='utf-8-sig') as f: return list(csv.DictReader(f))
sd=rd(f'_学习/_席位动向/{D}.csv')
fen=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
zt={r['代码']:r for r in rd(f'{D}/zt_pool.csv')}
ds={x['代码']:x for x in json.load(open(f'_学习/龙虎榜双源校验_{D}.json',encoding='utf-8'))['全量']}
lhb={}
for r in rd(f'{D}/lhb.csv'): lhb.setdefault(r['代码'],r)
codes=['300115','688608','688018','688787','300244','002164','600267','002242','301313','002696','605488','603626','003029','920096','300466','600178','603119','688836']
for c in codes:
    r=lhb.get(c,{}); x=ds.get(c,{})
    print('\n###',c,r.get('名称'),'涨幅',r.get('涨跌幅'),'净买亿',round(float(r.get('龙虎榜净买额',0))/1e8,4) if r else None,
          '占比',r.get('净买额占总成交比'),'判定',x.get('判定'),'口径',x.get('源1口径'),'源2亿',x.get('源2买侧净额亿'))
    print('   原因:',r.get('上榜原因'),'| 涨停池:', zt.get(c,{}).get('连板数'), zt.get(c,{}).get('所属行业'),
          '封单',zt.get(c,{}).get('封板资金'),'首封',zt.get(c,{}).get('首次封板时间'),'末封',zt.get(c,{}).get('最后封板时间'),'炸',zt.get(c,{}).get('炸板次数'),'统计',zt.get(c,{}).get('涨停统计'),'换手',zt.get(c,{}).get('换手率'))
    rows=[z for z in sd if z['代码']==c]
    for z in sorted(rows,key=lambda z:-float(z['净额'])):
        f=fen.get(z['席位'],{})
        print('   %-46s %s n=%-3s 收缩%.1f%%/%.2f%% %s 净%+.0f万 买%.0f万'%(z['席位'][:46],f.get('档','?'),f.get('样本','-'),f.get('收缩执1胜率',0),f.get('收缩执1均涨',0),'⚠' if f.get('小样本') else '  ',float(z['净额'])/1e4,float(z['买入金额'])/1e4))
