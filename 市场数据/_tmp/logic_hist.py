# -*- coding: utf-8 -*-
"""历史对照: 业绩票(中报预增雷达任一池)∩当日涨停 的 T+1 执行收益统计(零后视镜, 全部历史日<20261021)
执行口径: T+1 open 买入, T+1 close 卖出(与 _逻辑荐票结算 一致); gap>+4% 记「闸门外」不计入执行均收。
"""
import json, os, glob, csv, sys
sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\股票数据\市场数据'
L = os.path.join(D, '_学习')
CACHE = os.path.join(L, '_bars_cache')

def bars(code):
    p = os.path.join(CACHE, code + '.csv')
    if not os.path.exists(p):
        return None
    out = []
    for line in open(p, encoding='utf-8'):
        t = line.strip().split(',')
        if len(t) < 5 or not t[0]:
            continue
        try:
            out.append((t[0], float(t[1]), float(t[4])))
        except Exception:
            continue
    return out

def zt_of(d):
    p = os.path.join(D, d, 'zt_pool.csv')
    if not os.path.exists(p):
        return {}
    return {r['代码']: r for r in csv.DictReader(open(p, encoding='utf-8-sig'))}

files = sorted(glob.glob(os.path.join(L, '中报预增雷达_2026*.json')))
samples = []
detail = []
for f in files:
    d = os.path.basename(f).split('_')[-1].split('.')[0]
    if d >= '20261021':
        continue
    try:
        r = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    pool = set()
    for b in ['A共振池(重要度排序)', '概念叠加候选', '纯预增未叠加', '预期已兑现(年内已翻倍,不入候选)',
              '刚点火(有涨停未透支)', '已发酵对照Top12']:
        for it in r.get(b) or []:
            pool.add(it['代码'])
    z = zt_of(d)
    hits = [c for c in z if c in pool]
    if not hits:
        continue
    for c in hits:
        b = bars(c)
        if not b:
            continue
        idx = [i for i, x in enumerate(b) if x[0].replace('-', '') == d]
        if not idx:
            continue
        i = idx[0]
        if i + 1 >= len(b):
            continue
        d1, o1, c1 = b[i + 1]
        c0 = b[i][2]
        gap = round((o1 / c0 - 1) * 100, 2)
        ex = round((c1 / o1 - 1) * 100, 2)
        samples.append({'d': d, 'code': c, 'name': b and z[c]['名称'], 'gap': gap, 'exec': ex,
                        'gate': abs(gap) <= 4.0})
        detail.append({'荐票日': d, '代码': c, '名称': z[c]['名称'], '连板': z[c]['连板数'],
                       'gap%': gap, '执1%': ex, '闸门内': abs(gap) <= 4.0, 'T1日': d1})

ing = [s for s in samples if s['gate']]
import statistics as st
def agg(rows, k='exec'):
    if not rows:
        return None
    win = sum(1 for r in rows if r[k] > 0)
    return {'n': len(rows), '胜率%': round(win / len(rows) * 100, 1), '均收%': round(sum(r[k] for r in rows) / len(rows), 2),
            '中位%': round(st.median([r[k] for r in rows]), 2)}
res = {
    '样本说明': '业绩票=中报预增雷达当日任一池成员; 事件=当日涨停; 执行=T+1 open买/close卖; gap>|4%|记闸门外',
    '区间': [min(s['d'] for s in samples) if samples else None, max(s['d'] for s in samples) if samples else None],
    '全样本': agg(samples), '闸门内': agg(ing),
    '闸门外占比%': round((len(samples) - len(ing)) / len(samples) * 100, 1) if samples else None,
    '按连板': {str(k): agg([s for s in ing if False]) for k in []},
    '明细': detail,
}
# 按首板/连板分组(闸门内)
by = {}
for s in ing:
    lb = next((x['连板'] for x in detail if x['代码'] == s['code'] and x['荐票日'] == s['d']), '?')
    by.setdefault(str(lb), []).append(s)
res['按连板_闸门内'] = {k: agg(v) for k, v in sorted(by.items())}
json.dump(res, open(os.path.join(L, '_tmp_历史对照_业绩票_20261021.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ('区间', '全样本', '闸门内', '闸门外占比%', '按连板_闸门内')}, ensure_ascii=False, indent=1))
