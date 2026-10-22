# -*- coding: utf-8 -*-
"""三季报临时池_20261021.py —— 承接 Master 指派 MA-20261020-05①
源: 东财 datacenter 业绩预告 stock_yjyg_em(报告期=20260930), 公告日期<=20261021 (零后视镜)
口径: 预测指标含'净利润'且不含'扣除'; 预告类型∈{预增,扭亏}; 按代码去重; 剔ST/退/N/C
输出: _学习/三季报临时池_20261021.json  (不覆盖中报雷达)
"""
import sys, os, json, csv, re

D = r'D:\股票数据\市场数据'
L = os.path.join(D, '_学习')
d = '20261021'
dd = '2026-10-21'

import akshare as ak
df = ak.stock_yjyg_em(date='20260930')
raw = len(df)
df = df[df['预测指标'].astype(str).str.contains('净利润')]
df = df[~df['预测指标'].astype(str).str.contains('扣除')]
df = df[df['预告类型'].astype(str).isin(['预增', '扭亏'])]
df['公告日期'] = df['公告日期'].astype(str).str[:10]
# 零后视镜: 公告日 <= 20261021
df = df[df['公告日期'] <= dd]
df = df.drop_duplicates(subset=['股票代码'], keep='first')

BAD = ('ST', '退', 'N', 'C')
def bad(name):
    n = str(name).strip()
    return n.startswith('ST') or n.startswith('*ST') or '退' in n or n.startswith('N') or n.startswith('C')

NONREC = ['非经常性', '公允价值变动', '股权处置', '资产处置', '处置子公司', '债务重组', '诉讼', '政府补助',
          '坏账', '信用减值', '冲回', '投资收益', '出售', '转让', '并表', '理财']
MAIN = ['主营业务', '销量', '价格上涨', '涨价', '订单', '产能', '产品结构', '营业收入增长', '毛利率', '放量']

zt = {r['代码']: r for r in csv.DictReader(open(os.path.join(D, d, 'zt_pool.csv'), encoding='utf-8-sig'))}
tpl = json.load(open(os.path.join(D, '产业链模板.json'), encoding='utf-8'))
tpl_map = {}
for chain, v in tpl.items():
    if chain == '说明' or not isinstance(v, dict):
        continue
    envs = v.get('环节') if isinstance(v.get('环节'), dict) else v
    if not isinstance(envs, dict):
        continue
    for seg, ev in envs.items():
        st = ev.get('公司') if isinstance(ev, dict) else ev
        for pair in st or []:
            if len(pair) >= 2:
                tpl_map[pair[0]] = (chain, seg)
radar = json.load(open(os.path.join(L, '中报预增雷达_%s.json' % d), encoding='utf-8'))
mid = set()
for b in ['A共振池(重要度排序)', '概念叠加候选', '纯预增未叠加', '预期已兑现(年内已翻倍,不入候选)',
          '刚点火(有涨停未透支)', '已发酵对照Top12']:
    for it in radar.get(b) or []:
        mid.add(it['代码'])

rows, n_st = [], 0
for _, r in df.iterrows():
    code = str(r['股票代码']).zfill(6)
    name = str(r['股票简称']).strip()
    if bad(name):
        n_st += 1
        continue
    reason = str(r['业绩变动原因'] or '')
    nr = [k for k in NONREC if k in reason]
    mn = [k for k in MAIN if k in reason]
    amp = r['业绩变动幅度']
    try:
        amp = round(float(amp), 1)
    except Exception:
        amp = None
    rows.append({
        '代码': code, '名称': name, '预告类型': str(r['预告类型']),
        '变动幅度%': amp, '公告日期': r['公告日期'],
        '变动原因': reason[:300],
        '非经常词': nr, '主营词': mn,
        '驱动判定': ('含非经常' if nr else '主营驱动') if not (nr and not mn) else '疑似非经常主导',
        'in_zt': code in zt, 'in_tpl': code in tpl_map, 'in_中报池': code in mid,
    })
rows.sort(key=lambda x: (-(x['变动幅度%'] or -999)))
hit = [x for x in rows if x['in_zt']]
out = {
    'schema_version': 1, 'as_of': d, '日期': d,
    '来源': 'akshare ak.stock_yjyg_em(报告期=20260930) = 东财 datacenter RPT_PUBLIC_OP_NEWPREDICT',
    '口径': '预测指标含净利润且不含扣除; 预告类型∈{预增,扭亏}; 公告日期<=%s(零后视镜); 按代码去重; 剔ST/退/N/C' % dd,
    '原始条数': raw,
    '池大小': len(rows),
    '剔ST退NC': n_st,
    '∩当日涨停': [{'代码': x['代码'], '名称': x['名称'], '预告类型': x['预告类型'], '变动幅度%': x['变动幅度%'],
                '公告日期': x['公告日期'], '驱动判定': x['驱动判定'], '非经常词': x['非经常词'],
                '涨停': {'连板': zt[x['代码']]['连板数'], '首封': zt[x['代码']]['首次封板时间'],
                        '炸板': zt[x['代码']]['炸板次数']}} for x in hit],
    '∩当日涨停_只数': len(hit),
    '∩模板': len([x for x in rows if x['in_tpl']]),
    '∩模板_名单': [{'代码': x['代码'], '名称': x['名称'], '链': tpl_map[x['代码']][0], '环节': tpl_map[x['代码']][1]} for x in rows if x['in_tpl']],
    '三交叉(池∩模板∩涨停)': [x['代码'] for x in hit if x['in_tpl']],
    '与中报池差异': {'中报池只数': len(mid), '三季报池只数': len(rows),
                  '交集只数': len([x for x in rows if x['in_中报池']]),
                  '仅三季报池': len([x for x in rows if not x['in_中报池']]),
                  '仅中报池': len([c for c in mid if c not in {x['代码'] for x in rows}])},
    '主营驱动只数': len([x for x in rows if not x['非经常词']]),
    '含非经常词只数': len([x for x in rows if x['非经常词']]),
    '明细Top40': rows[:40],
    '全部明细': rows,
    '代码名单': [x['代码'] for x in rows],
}
p = os.path.join(L, '三季报临时池_%s.json' % d)
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ('原始条数', '池大小', '剔ST退NC', '∩当日涨停_只数', '∩模板',
                                      '三交叉(池∩模板∩涨停)', '与中报池差异', '主营驱动只数', '含非经常词只数',
                                      '∩当日涨停')}, ensure_ascii=False, indent=1))
print('WROTE', p, os.path.getsize(p))
