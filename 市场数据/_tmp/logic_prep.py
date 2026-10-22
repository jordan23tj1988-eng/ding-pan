# -*- coding: utf-8 -*-
"""logic 20261021 数据准备：机械计算，不做判断，全部输出到 _tmp/logic_prep_20261021.json"""
import json, csv, os, sys, collections

L = r'D:\股票数据\市场数据\_学习'
D = r'D:\股票数据\市场数据'
d = '20261021'
prev = '20261020'

out = {}

# ---------- 1. 涨停池 ----------
zt = {}
with open(os.path.join(D, d, 'zt_pool.csv'), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        r['封板资金'] = float(r['封单资金'] if '封单资金' in r else r['封板资金'])
        r['成交额'] = float(r['成交额'])
        r['封单比'] = round(r['封板资金'] / r['成交额'] * 100, 2) if r['成交额'] else None
        r['连板数'] = int(r['连板数'])
        r['炸板次数'] = int(r['炸板次数'])
        r['换手率'] = round(float(r['换手率']), 2)
        zt[r['代码']] = r
out['zt_count'] = len(zt)

# ---------- 2. 产业链模板 ----------
tpl_path = os.path.join(L, '_bak_产业链模板_20261019.json')
tpl = json.load(open(tpl_path, encoding='utf-8'))
tpl_map = {}   # code -> (链, 环节)
chain_counts = {}
for chain, v in tpl.items():
    if chain in ('说明',):
        continue
    chain_counts[chain] = 0
    if not isinstance(v, dict):
        continue
    for seg, arr in (v.get('环节') or {}).items():
        for pair in arr or []:
            if len(pair) >= 2:
                tpl_map[pair[0]] = (chain, seg)
                chain_counts[chain] += 1
out['tpl_path'] = tpl_path
out['tpl_size'] = len(tpl_map)
out['tpl_chains'] = {k: len((tpl[k].get('环节') or {})) for k in tpl if k != '说明'}
out['tpl_codes'] = len(tpl_map)
out['tpl_hit_zt'] = [{'代码': c, '名称': zt[c]['名称'], '链': tpl_map[c][0], '环节': tpl_map[c][1],
                      '连板': zt[c]['连板数'], '封单比': zt[c]['封单比'], '炸板': zt[c]['炸板次数'],
                      '首封': zt[c]['首次封板时间'], '换手': zt[c]['换手率'], '成交额亿': round(zt[c]['成交额']/1e8, 2)}
                     for c in zt if c in tpl_map]

# ---------- 3. 中报雷达 ----------
radar = json.load(open(os.path.join(L, '中报预增雷达_%s.json' % d), encoding='utf-8'))
buckets = ['A共振池(重要度排序)', '概念叠加候选', '纯预增未叠加', '预期已兑现(年内已翻倍,不入候选)',
           '刚点火(有涨停未透支)', '已发酵对照Top12']
pool = {}
for b in buckets:
    for it in radar.get(b) or []:
        pool.setdefault(it['代码'], dict(it, _bucket=b))
out['radar_stats'] = radar['统计']
out['radar_pool_union'] = len(pool)
out['radar_hit_zt'] = []
for c in zt:
    if c in pool:
        it = pool[c]
        out['radar_hit_zt'].append({
            '代码': c, '名称': it['名称'], '桶': it['_bucket'], '预告': it['预告类型'],
            '变动%': it.get('变动幅度%'), '公告日': it.get('公告日期'),
            'r20': it.get('近20日涨幅%'), 'r250': it.get('r250'), '距高%': it.get('距250日高%'),
            '概念板块': it.get('概念板块'), '原因': (it.get('原因') or '')[:400]})
# 三交叉
tri = [x for x in out['radar_hit_zt'] if x['代码'] in tpl_map]
out['tri_cross'] = [{'代码': t['代码'], '名称': t['名称'], '链': tpl_map[t['代码']][0], '环节': tpl_map[t['代码']][1]} for t in tri]

# ---------- 4. 链条纵深 ----------
chain = json.load(open(os.path.join(L, '涨停对链条_%s.json' % d), encoding='utf-8'))
rows = []
for line in chain['题材线']:
    segs = line.get('环节') or []
    n = line.get('家数') or 0
    rows.append({'线': line['大方向'], '家数': n, '环节数': len(segs),
                 '环节/家数': round(len(segs)/n, 2) if n else None,
                 '最高连板': line.get('最高连板'), '最早封板': line.get('最早封板'),
                 '开板占比': line.get('开板占比'), '强度画像': line.get('强度画像'),
                 '环节名': [s.get('环节') for s in segs],
                 '个股': [(i['代码'], i['名称'], i['连板'], i.get('开板次数'), i['封单比'], i['首封']) for s in segs for i in s.get('个股') or []]})
out['chains'] = sorted(rows, key=lambda x: -x['家数'])

# ---------- 5. 三季报临时池（MA-20261020-05①）----------
q3 = []
for c, it in pool.items():
    tags = it.get('概念板块') or []
    if any('三季报预增' in t for t in tags):
        q3.append({'代码': c, '名称': it['名称'], '公告日': it.get('公告日期'),
                   '桶': it['_bucket'], 'in_zt': c in zt, 'in_tpl': c in tpl_map})
out['q3_tag_pool'] = {'n': len(q3), 'n_in_zt': sum(1 for x in q3 if x['in_zt']),
                      'list': q3}
# 涨停原因文本中的三季报字样
zty = json.load(open(os.path.join(L, '涨停原因_%s.json' % d), encoding='utf-8'))
out['zt_reason_q3'] = {c: v['原因'] for c, v in zty['映射'].items() if '三季报' in (v.get('原因') or '')}

# ---------- 6. 风险事件 ----------
ev = json.load(open(os.path.join(L, '风险事件_%s.json' % d), encoding='utf-8'))
print_ev = {k: (len(v) if hasattr(v, '__len__') else v) for k, v in ev.items() if not isinstance(v, (dict, list))}
out['risk_top'] = print_ev
# 找事件列表结构
def find_lists(o, path=''):
    res = []
    if isinstance(o, dict):
        for k, v in o.items():
            res += find_lists(v, path + '/' + str(k))
    elif isinstance(o, list):
        if o and isinstance(o[0], dict):
            res.append((path, len(o), list(o[0].keys())))
        else:
            for i, v in enumerate(o[:3]):
                res += find_lists(v, path + '/%d' % i)
    return res
out['risk_struct'] = find_lists(ev)[:12]
json.dump(out, open(os.path.join(D, '_tmp', 'logic_prep_%s.json' % d), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ('zt_count', 'tpl_size', 'tpl_hit_zt', 'tri_cross', 'radar_pool_union',
                                      'radar_hit_zt', 'q3_tag_pool', 'zt_reason_q3', 'risk_top', 'risk_struct')},
                 ensure_ascii=False, indent=1)[:6000])
print('--- CHAINS ---')
for r in out['chains'][:8]:
    print(r['线'], r['家数'], '环节', r['环节数'], r['环节/家数'], '最高', r['最高连板'], '开板', r['开板占比'])
