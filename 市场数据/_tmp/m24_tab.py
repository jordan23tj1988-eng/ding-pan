import csv
rows={r['代码']:r for r in csv.DictReader(open('20261023/zt_pool.csv',encoding='utf-8-sig'))}
def f(x):
    try: return float(x)
    except: return 0.0
for c in ['002474','300296','603721','301502','002979','688836','003021','300561','002724','603278','600487']:
    r=rows.get(c)
    if not r: print(c,'NOT IN ZT_POOL'); continue
    amt=f(r['成交额']); fl=f(r['流通市值']); feng=f['封板资金'] if False else f(r['封板资金'])
    print('%s %s | 涨%.2f 价%.2f 成交%.2f亿 流通%.1f亿 换手%s 封单%.2f亿(成交%.2f%%/流通%.3f%%) 首封%s 末封%s 炸%s 连板%s %s'%(
      c,r['名称'],f(r['涨跌幅']),f(r['最新价']),amt/1e8,fl/1e8,r['换手率'],feng/1e8,feng/amt*100,feng/fl*100,r['首次封板时间'],r['最后封板时间'],r['炸板次数'],r['连板数'],r['所属行业']))
