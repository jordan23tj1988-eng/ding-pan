# -*- coding: utf-8 -*-
import json, io, sys, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
R = r'D:\股票数据\市场数据'
os.chdir(R)

zt = list(csv.DictReader(open('20261104/zt_pool.csv', encoding='utf-8-sig')))
codes = {r['代码']: r for r in zt}
print('涨停', len(zt))

tpl = json.load(open('产业链模板.json', encoding='utf-8'))
tpl_map = {}  # code -> [(链, 环节)]
for chain, v in tpl.items():
    if chain == '说明':
        continue
    for env, lst in (v.get('环节') or {}).items():
        for pair in lst:
            tpl_map.setdefault(pair[0], []).append((chain, env))
hits = [(c, tpl_map[c]) for c in codes if c in tpl_map]
print('模板命中 %d/%d' % (len(hits), len(zt)))
for c, v in hits:
    r = codes[c]
    print('  ', c, r['名称'], '连板', r['连板数'], '封单亿', round(float(r['封板资金'])/1e8, 2), '首封', r['首次封板时间'], '炸', r['炸板次数'], '换手', round(float(r['换手率']),2), '|', v)

radar = json.load(open('_学习/中报预增雷达_20261104.json', encoding='utf-8'))
print('雷达 报告期', radar.get('报告期'), '口径', radar.get('口径'))
A = {x['代码']: x for x in radar['A共振池(重要度排序)']}
inter = [c for c in codes if c in A]
print('A共振池∩涨停 =', len(inter))
for c in inter:
    x = A[c]
    r = codes[c]
    print('  ', c, r['名称'], '连板', r['连板数'], '|', x['预告类型'], x['变动幅度%'], '重要度', x['重要度分'], '|', x['成色依据'], '|', x['成色来源'], '| r250', x['r250'], '距高', x['距250日高%'])

jk = {x['代码']: x for x in radar['刚点火(有涨停未透支)']}
inter2 = [c for c in codes if c in jk]
print('刚点火∩涨停 =', len(inter2), [codes[c]['名称'] for c in inter2])

risk = json.load(open('_学习/风险事件_20261103.json', encoding='utf-8'))
ev = risk['事件']
risk_codes = {}
for e in ev:
    if e.get('类型') == '减持' and e.get('代码') in codes:
        risk_codes.setdefault(e['代码'], []).append(e)
print('\n风险事件命中(减持) %d 只:' % len(risk_codes))
for c, lst in risk_codes.items():
    print('  ', c, codes[c]['名称'], '连板', codes[c]['连板数'], '公告日', [x.get('公告日') for x in lst], '变动截止', [x.get('变动截止日') for x in lst])
