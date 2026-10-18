# -*- coding: utf-8 -*-
"""周训练手算聚合(20261016) —— weekly_training_run.py 缺失时的替代取证。
口径: 全部读留档结算文件, 不新增判断、不补数字。
周 = 20261012~20261016 (最后一个完整结算票日为20261015, 10/16链路断)。
"""
import json, os, io, sys

L = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_学习')
DAYS = ['20261012', '20261013', '20261014', '20261015']
FILES = {
    'auction': ('竞价池结算_%s.json', '执行胜率', '执行均收', '全场涨停均收'),
    'lhb':     ('席位荐票结算_%s.json', '执行胜率', '均收', None),
    'theme':   ('题材荐票结算_%s.json', '执行胜率', '执行均收', '全场涨停均收'),
    'logic':   ('逻辑荐票结算_%s.json', '执行胜率', '执行均收', '全场涨停均收'),
    'limitup': ('质量荐票结算_%s.json', '执行胜率', '执行均收', '全场均收'),
}

def load(f):
    p = os.path.join(L, f)
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding='utf-8'))

def parse_win(s):
    try:
        a, b = str(s).split('/')
        return int(a), int(b)
    except Exception:
        return None, None

# 每日全场上限涨停执行均收(按票日索引, 供 lhb 补基准)
mkt = {}
for d in DAYS:
    x = load('质量荐票结算_%s.json' % d)
    if x:
        mkt[d] = (x.get('汇总') or {}).get('全场均收')

out = {'周': [DAYS[0], '20261016'], '生成方式': '手算聚合(weekly_training_run.py 缺失, 未生成训练底座体检等训练脚本专属字段)',
       '口径': '票加权: 均收=∑(日均收×日票数)/∑票数; 全场基准按同日同票数加权; 增益=路均收-全场基准; 胜率=胜/可结算票数',
       '五路': {}, '六账本': '见 周考核_20261016.json(模拟盘引擎 weekly 实跑)', '缺口': []}

for route, (pat, wk, rk, bk) in FILES.items():
    rows = []
    for d in DAYS:
        x = load(pat % d)
        if not x:
            rows.append({'票日': d, '状态': 'missing'})
            continue
        s = x.get('汇总') or {}
        w, n = parse_win(s.get(wk))
        ret = s.get(rk)
        base = s.get(bk) if bk else mkt.get(d)
        if base is None:
            base = mkt.get(d)
        rows.append({'票日': d, '结算日': x.get('结算日'), '胜': w, '票数': n,
                     '均收pct': ret, '全场基准pct': base,
                     '日增益pp': s.get('增益pp') if '增益pp' in s else (round(ret - base, 2) if (ret is not None and base is not None) else None)})
    tot_n = sum(r['票数'] for r in rows if r.get('票数'))
    tot_w = sum(r['胜'] for r in rows if r.get('胜') is not None)
    num = sum(r['均收pct'] * r['票数'] for r in rows if r.get('均收pct') is not None and r.get('票数'))
    bnum = sum(r['全场基准pct'] * r['票数'] for r in rows if r.get('全场基准pct') is not None and r.get('票数'))
    bn = sum(r['票数'] for r in rows if r.get('全场基准pct') is not None and r.get('票数'))
    avg = round(num / tot_n, 2) if tot_n else None
    bavg = round(bnum / bn, 2) if bn else None
    zero_days = [r['票日'] for r in rows if r.get('票数') == 0]
    zero_ok = [r['票日'] for r in rows if r.get('票数') == 0 and (r.get('全场基准pct') or 0) < 0]
    out['五路'][route] = {
        '逐日': rows,
        '票数': tot_n,
        '胜数': tot_w,
        '胜率pct': round(tot_w / tot_n * 100, 1) if tot_n else None,
        '均收pct': avg,
        '全场基准pct': bavg,
        '选股增益pp': round(avg - bavg, 2) if (avg is not None and bavg is not None) else None,
        '零票日': zero_days,
        '空仓正确率': ('%d/%d' % (len(zero_ok), len(zero_days))) if zero_days else None,
    }
    print(route, json.dumps(out['五路'][route], ensure_ascii=False))

p = os.path.join(L, '_周训练手算_20261016.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('->', p)
