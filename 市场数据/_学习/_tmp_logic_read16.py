# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/_学习/'
rad = json.load(open(B+'中报预增雷达_20261014.json', encoding='utf-8'))
print('雷达_20261014 报告期 =', rad['报告期'], '| 日期 =', rad['日期'])
print('雷达_20261013 报告期 =', json.load(open(B+'中报预增雷达_20261013.json', encoding='utf-8'))['报告期'])
TARGET = ['605189','000601','002552','000823','002696','002343','603096','603968','000530','002860','002917','600391','300006','605189']
buckets = ['A共振池(重要度排序)','概念叠加候选','纯预增未叠加','预期已兑现(年内已翻倍,不入候选)','刚点火(有涨停未透支)','已发酵对照Top12','行情缺失']
for k in buckets:
    v = rad.get(k) or []
    if isinstance(v, int): print(k, '= ', v); continue
    print('---', k, 'n=', len(v))
    for x in v:
        c = x['代码'] if isinstance(x,dict) else str(x)
        if c in TARGET:
            print('   HIT', json.dumps(x, ensure_ascii=False)[:520])
# 按题材归类 里也查
print('--- 按题材归类 keys:', list(rad['按题材归类'].keys()))
for k,v in rad['按题材归类'].items():
    for x in v:
        c = x['代码'] if isinstance(x,dict) else str(x)
        if c in TARGET: print('   归类HIT', k, json.dumps(x, ensure_ascii=False)[:400])
