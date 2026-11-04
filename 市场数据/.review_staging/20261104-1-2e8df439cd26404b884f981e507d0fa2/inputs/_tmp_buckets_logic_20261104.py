# -*- coding: utf-8 -*-
"""logic 路历史桶计算：按温度档切桶，算执1/执2 的 n/胜率/均收/中位。只读既有文件，零编造。"""
import json, io, sys, os, csv, glob, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
R = r'D:\股票数据\市场数据'
os.chdir(R)

wt = json.load(open('_学习/_市场温度表.json', encoding='utf-8'))
dates = sorted(wt.keys())

# bars cache: 代码 -> {date: (open, close)}
def load_bars(code):
    p = os.path.join('_学习/_bars_cache', code + '.csv')
    if not os.path.exists(p):
        return None
    out = {}
    with open(p, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            try:
                v = (float(row['open']), float(row['close']))
                out[row['date'].replace('-', '')] = v
                out[row['date']] = v
            except Exception:
                pass
    return out

def ymd(d):
    return d[:4] + '-' + d[4:6] + '-' + d[6:]

samples = []
missing_bars = 0
for i, d in enumerate(dates[:-1]):  # last date has no T+1 yet
    fp = '_学习/涨停对链条_%s.json' % d
    if not os.path.exists(fp):
        continue
    try:
        obj = json.load(open(fp, encoding='utf-8'))
    except Exception:
        continue
    nd = dates[i + 1]
    nd2 = dates[i + 2] if i + 2 < len(dates) else None
    temp = wt[d].get('温度')
    dang = wt[d].get('温度档')
    for line in obj.get('题材线', []):
        for env in line.get('环节', []):
            for s in env.get('个股', []):
                code = s.get('代码')
                b = load_bars(code)
                if not b:
                    missing_bars += 1
                    continue
                o1 = b.get(ymd(nd))
                if not o1:
                    continue
                o1o, o1c = o1
                r1 = (o1c / o1o - 1) * 100 if o1o else None
                r2 = None
                if nd2:
                    c2 = b.get(ymd(nd2))
                    if c2 and o1o:
                        r2 = (c2[1] / o1o - 1) * 100
                samples.append(dict(d=d, nd=nd, code=code, name=s.get('名称'), line=line.get('大方向'),
                                    env=env.get('环节'), lb=s.get('连板'), feng=s.get('封单比'),
                                    first=s.get('首封'), kb=s.get('开板次数'),
                                    cat=s.get('催化') or '', temp=temp, dang=dang, r1=r1, r2=r2))

print('样本:', len(samples), '缺bars:', missing_bars, '日期数:', len(set(x['d'] for x in samples)))
print('温度档分布:', {k: len(set(x['d'] for x in samples if x['dang'] == k)) for k in set(x['dang'] for x in samples)})

def stat(rows, label):
    r1 = [x['r1'] for x in rows if x['r1'] is not None]
    r2 = [x['r2'] for x in rows if x['r2'] is not None]
    if not r1:
        return dict(label=label, n=0)
    win = sum(1 for v in r1 if v > 0) / len(r1) * 100
    return dict(label=label, n=len(r1), 胜率=round(win, 1), 执1均收=round(sum(r1) / len(r1), 2),
                执1中位=round(st.median(r1), 2), n2=len(r2),
                执2均收=round(sum(r2) / len(r2), 2) if r2 else None,
                执2胜率=round(sum(1 for v in r2 if v > 0) / len(r2) * 100, 1) if r2 else None)

DANG = '中性'
mid = [x for x in samples if x['dang'] == DANG]
print('\n===== 中性档 %d 样本 / %d 交易日 =====' % (len(mid), len(set(x['d'] for x in mid))))
out = []
out.append(stat(mid, '中性档·全体'))
for lb in ['1', '2', '3']:
    out.append(stat([x for x in mid if str(x['lb']) == lb], '中性档·%s板' % lb))
out.append(stat([x for x in mid if str(x['lb']).isdigit() and int(x['lb']) >= 2], '中性档·2板加'))
# 封单比
def fb(x):
    try:
        return float(x['feng'])
    except Exception:
        return None
out.append(stat([x for x in mid if fb(x) is not None and fb(x) < 1], '中性档·封单<1%'))
out.append(stat([x for x in mid if fb(x) is not None and 1 <= fb(x) < 3], '中性档·封单1-3%'))
out.append(stat([x for x in mid if fb(x) is not None and fb(x) >= 3], '中性档·封单>=3%'))
# 首封
def fs(x):
    s = str(x['first'] or '')
    s = s.replace(':', '')
    return int(s[:4]) if len(s) >= 4 and s[:4].isdigit() else None
out.append(stat([x for x in mid if fs(x) is not None and fs(x) <= 935], '中性档·首封<=09:35'))
out.append(stat([x for x in mid if fs(x) is not None and 935 < fs(x) <= 1100], '中性档·首封09:35-11:00'))
out.append(stat([x for x in mid if fs(x) is not None and fs(x) > 1100], '中性档·首封>11:00'))
out.append(stat([x for x in mid if fs(x) is not None and fs(x) >= 1300], '中性档·首封>=13:00(尾盘)'))
# 开板
out.append(stat([x for x in mid if str(x['kb']) == '0'], '中性档·开板0次'))
out.append(stat([x for x in mid if str(x['kb']).isdigit() and int(x['kb']) >= 2], '中性档·开板>=2次'))
# 线
for line, kw in [('半导体', '半导体'), ('贵金属', '贵金属'), ('AI算力', 'AI算力'), ('PCB', 'PCB'), ('机器人', '机器人'), ('有色', '有色')]:
    out.append(stat([x for x in mid if line in str(x['line'])], '中性档·%s线' % line))
# 催化关键词（首板）
def has(x, kws):
    return any(k in (x['cat'] or '') for k in kws)
for kwname, kws in [('半导体催化', ['半导体', '芯片', '存储', '封装', '光刻', '靶材', '晶圆', 'HBM']),
                    ('AI算力催化', ['算力', '数据中心', '液冷', '服务器', 'AIDC', 'CPO']),
                    ('PCB催化', ['覆铜板', 'PCB', '印制电路', '电子布', '铜箔', '载板']),
                    ('黄金催化', ['黄金', '白银', '金价', '贵金属']),
                    ('机器人催化', ['机器人', '灵巧手', '减速器', '丝杠']) ]:
    sub = [x for x in mid if has(x, kws)]
    out.append(stat(sub, '中性档·催化含%s' % kwname))
    out.append(stat([x for x in sub if str(x['lb']) == '1'], '中性档·催化含%s·首板' % kwname))

for r in out:
    print(r)

# 全档（跨温度）对照
print('\n===== 全档对照 =====')
allr = []
allr.append(stat(samples, '全档·全体'))
allr.append(stat([x for x in samples if str(x['lb']) == '1'], '全档·首板'))
for kwname, kws in [('半导体催化', ['半导体', '芯片', '存储', '封装', '光刻', '靶材', '晶圆', 'HBM']),
                    ('AI算力催化', ['算力', '数据中心', '液冷', '服务器', 'AIDC', 'CPO']),
                    ('PCB催化', ['覆铜板', 'PCB', '印制电路', '电子布', '铜箔', '载板']),
                    ('黄金催化', ['黄金', '白银', '金价', '贵金属']),
                    ('机器人催化', ['机器人', '灵巧手', '减速器', '丝杠'])]:
    sub = [x for x in samples if has(x, kws)]
    allr.append(stat(sub, '全档·催化含%s' % kwname))
    allr.append(stat([x for x in sub if str(x['lb']) == '1'], '全档·催化含%s·首板' % kwname))
for r in allr:
    print(r)

json.dump(dict(样本数=len(samples), 中性=out, 全档=allr, 交易日数=len(set(x['d'] for x in samples)),
               窗口='%s~%s' % (dates[0], dates[-1])),
          open('_学习/_buckets_logic_20261104.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nwrote _学习/_buckets_logic_20261104.json')
