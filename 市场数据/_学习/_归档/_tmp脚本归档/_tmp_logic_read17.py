# -*- coding: utf-8 -*-
import sys, io, json, csv, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/_学习/'
ROOT = 'D:/股票数据/市场数据/'

# ---- 涨停36 ----
rows = list(csv.reader(open(ROOT+'20261014/zt_pool.csv', encoding='utf-8')))
hdr = rows[0]; zt = {}
for r in rows[1:]:
    d = dict(zip(hdr, r)); zt[d['代码'].strip()] = d
print('涨停', len(zt))

# ---- 产业链模板153 ----
tpl = json.load(open(ROOT+'产业链模板.json', encoding='utf-8'))
codes = set()
def walk(o):
    if isinstance(o, dict):
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o:
            if isinstance(v, str) and re.fullmatch(r'\d{6}', v): codes.add(v)
            else: walk(v)
walk(tpl)
print('模板代码数', len(codes))
inter = codes & set(zt)
print('模板∩涨停 覆盖率 =', len(inter), '/', len(zt), '=', round(len(inter)/len(zt),4), [(c, zt[c]['名称'], zt[c]['连板数'], zt[c]['所属行业']) for c in inter])

# ---- 位置计算 ----
def pos(code):
    p = B+'_bars_cache/'+code+'.csv'
    if not os.path.exists(p): return None
    r = list(csv.reader(open(p, encoding='utf-8')))
    if len(r) < 2: return None
    h = r[0]; d = [dict(zip(h, x)) for x in r[1:] if x and x[0]]
    d = [x for x in d if x.get('close')]
    if len(d) < 252: pass
    cl = [float(x['close']) for x in d]
    last = cl[-1]
    def chg(n):
        return round((last/cl[-1-n]-1)*100, 2) if len(cl) > n else None
    hi250 = max(float(x['high']) for x in d[-250:]) if len(d) >= 250 else max(float(x['high']) for x in d)
    ytd_base = None
    for x in d:
        if x['date'] >= '2026-01-01':
            ytd_base = float(x['open']); break
    return {
      'r5': chg(5), 'r20': chg(20), 'r60': chg(60),
      'r250': round((last/cl[-250]-1)*100,2) if len(cl)>=250 else None,
      'ytd': round((last/ytd_base-1)*100,2) if ytd_base else None,
      '距250高%': round((last/hi250-1)*100, 2),
      'last': last, 'n': len(d), '首日': d[0]['date'], '末日': d[-1]['date'],
    }

CAND = ['000823','002552','605189','000601','002343','603096','002696','603968','000530','002860','601188','600391','300299','603533','002917','600202','001318','603258','002813','000668','600121','601811','601858','603598','002469','600847','603656','300006','600252','001216','001299','600408','002029','000573','600097','603992']
print()
print('代码 名称 连板 首封 r5 r20 r60 r250 ytd 距250高% 末日')
for c in CAND:
    if c not in zt: continue
    p = pos(c)
    if not p: print(c, zt[c]['名称'], zt[c]['连板数'], 'NODATA'); continue
    print(f"{c} {zt[c]['名称']} {zt[c]['连板数']}板 封{zt[c]['首次封板时间']} r5={p['r5']} r20={p['r20']} r60={p['r60']} r250={p['r250']} ytd={p['ytd']} 距250高={p['距250高%']} 末日={p['末日']}")
