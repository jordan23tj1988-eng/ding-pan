# -*- coding: utf-8 -*-
import sys, io, json, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
R = J(B+'_学习/风险事件_20261029.json')
zt = list(csv.DictReader(open(B+'20261029/zt_pool.csv', encoding='utf-8-sig')))
codes = {r['代码']: r for r in zt}
print('涨停', len(codes), '事件', len(R['事件']))
# 事件类型分布
from collections import Counter
print(Counter(e['类型'] for e in R['事件']))
print('--- 涨停股命中事件 ---')
hit = {}
for e in R['事件']:
    if e['代码'] in codes:
        hit.setdefault(e['代码'], []).append(e)
for c, evs in hit.items():
    print('##', c, codes[c]['名称'], '连板', codes[c]['连板数'])
    for e in evs:
        print('   ', json.dumps(e, ensure_ascii=False))
print('命中只数', len(hit), '/', len(codes))
# 全市场限售解禁未来窗口(20261030~20261129) 是否含今日涨停股
print('\n--- 窗口内解禁(全部) ---')
for e in R['事件']:
    if e['类型'] == '限售解禁':
        print(json.dumps(e, ensure_ascii=False))
# 中报雷达
rad = J(B+'_学习/中报预增雷达_20261029.json')
print('\n--- 今日涨停 ∩ 中报雷达各池 ---')
pools = ['A共振池(重要度排序)','概念叠加候选','纯预增未叠加','刚点火(有涨停未透支)','预期已兑现(年内已翻倍,不入候选)','行情缺失','已发酵对照Top12']
for pn in pools:
    arr = rad.get(pn) or []
    found = [x for x in arr if x.get('代码') in codes]
    if found:
        print(pn, len(found))
        for x in found:
            print('   ', x.get('代码'), x.get('名称'), x.get('预告类型'), x.get('变动幅度%'), x.get('公告日期') or x.get('公告日'), '成色', x.get('成色'), '|', (x.get('原因') or '')[:80])
