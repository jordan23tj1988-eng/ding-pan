import json, io, sys, os, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
D = '20260826'
R = json.load(open(os.path.join(X, '中报预增雷达_%s.json' % D), 'r', encoding='utf-8'))
A = R['A共振池(重要度排序)']

pools = {k: R[k] for k in ['A共振池(重要度排序)', '概念叠加候选', '纯预增未叠加',
                           '预期已兑现(年内已翻倍,不入候选)', '刚点火(有涨停未透支)',
                           '已发酵对照Top12', '行情缺失']}
for code in ['600256', '001258', '603615']:
    hits = [k for k, v in pools.items() if any(str(e.get('代码')) == code for e in v)]
    print('%s 在雷达池: %s' % (code, hits or '0命中'))
    for k in hits:
        e = [x for x in pools[k] if str(x.get('代码')) == code][0]
        print('   ', k, json.dumps(e, ensure_ascii=False)[:500])

print()
print('=== A池 字段/成色依据分布 ===')
from collections import Counter
c1 = Counter()
for e in A:
    dep = e.get('成色依据') or ''
    c1[dep.split(';')[0][:24]] += 1
for k, v in c1.most_common(12): print(' %-30s %d' % (k, v))
print('成色来源:', Counter(e.get('成色来源') for e in A))
print('重要度分分布:', sorted(Counter(e.get('重要度分') for e in A).items(), key=lambda x: -(x[0] or 0)))
print('主类分布:', Counter(e.get('主类') for e in A).most_common())

NONREC = ['投资收益','资产处置','股权转让','公允价值','政府补助','债务重组','联营','合营',
          '理财','税收返还','拆迁','补偿款','非经常','出售','转让子公司','退税','减值冲回','诉讼']
MAIN = ['销量','产量','产销','订单','出货','交付','产能','价格上涨','量价','需求增长','营业收入增长',
        '收入增长','毛利','放量','满产','中标','新增装机','销售增长','市场份额','降本增效','客户拓展',
        '量增','价格同比上涨','开工率']
cnt = Counter()
for e in A:
    txt = e.get('原因') or ''
    nr = [w for w in NONREC if w in txt]
    mn = [w for w in MAIN if w in txt]
    r250 = e.get('r250')
    if nr and not mn: g = 'C'
    elif mn: g = 'A' if (r250 is None or r250 < 100) else 'B'
    else: g = 'B'
    cnt[g] += 1
print()
print('规则化三档复核分布:', dict(cnt))
print('样例:')
for e in A[:5]:
    print('  ', e['代码'], e['名称'], '| r250', e.get('r250'), '| 依据', (e.get('成色依据') or '')[:40], '| 原因', (e.get('原因') or '')[:80])
