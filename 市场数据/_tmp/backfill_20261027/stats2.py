import csv, json, statistics as st, collections

rows = list(csv.DictReader(open('20261027/zt_pool.csv', encoding='utf-8-sig')))


def t(s):
    s = (s or '').strip()
    if not s:
        return None
    s = s.replace(':', '')
    return int(s[:4])


one = [r for r in rows if t(r['首次封板时间']) is not None and t(r['首次封板时间']) <= 925 and int(r['炸板次数']) == 0]
early = [r for r in rows if t(r['首次封板时间']) is not None and t(r['首次封板时间']) <= 936]
late = [r for r in rows if t(r['首次封板时间']) is not None and t(r['首次封板时间']) >= 1301]
mid = [r for r in rows if t(r['首次封板时间']) is not None and t(r['首次封板时间']) >= 1300 and t(r['首次封板时间']) < 1400]
zf0 = [r for r in rows if int(r['炸板次数']) == 0]
ratio = []
for r in rows:
    fm = float(r['封板资金'])
    cm = float(r['流通市值'])
    ratio.append(fm / cm * 100 if cm else 0)
print('n=%d 一字(<=0925且炸0)=%d/41 首封<=0936=%d/41(%.1f%%) 首封>=1301=%d/41(%.1f%%) 首封13:00-14:00=%d 炸0=%d/41(%.1f%%)'
      % (len(rows), len(one), len(early), len(early) / 41 * 100, len(late), len(late) / 41 * 100, len(mid), len(zf0), len(zf0) / 41 * 100))
print('封/流通中位 %.3f%%  均值 %.3f%%  n=%d' % (st.median(ratio), sum(ratio) / len(ratio), len(ratio)))
tb = collections.Counter(t(r['首次封板时间']) // 100 for r in rows)
print('首封小时分布:', dict(sorted(tb.items())))
bz = collections.Counter(int(r['炸板次数']) for r in rows)
print('炸板次数分布:', dict(sorted(bz.items())))
print('封板总额 %.4f亿 池内成交 %.2f亿' % (sum(float(r['封板资金']) for r in rows) / 1e8,
                                        sum(float(r['成交额']) for r in rows) / 1e8))
# 消费/机器人 封单
m = json.load(open('_学习/题材归位_20261027.json', encoding='utf-8'))['映射']
big = {}
for r in rows:
    d = m.get(r['代码'], {})
    k = d.get('大方向') or '未归位'
    big.setdefault(k, [0, 0.0])
    big[k][0] += 1
    big[k][1] += float(r['封板资金']) / 1e8
for k, v in sorted(big.items(), key=lambda x: -x[1][1]):
    print('  %-12s %2d 只 封单 %.4f 亿' % (k, v[0], v[1]))
# 5板/4板明细
for r in rows:
    if int(float(r['连板数'])) >= 4:
        print('  HIGH', r['代码'], r['名称'], r['连板数'], r['所属行业'], r['首次封板时间'], '炸', r['炸板次数'],
              '封/流通 %.3f%%' % (float(r['封板资金']) / float(r['流通市值']) * 100))
