# -*- coding: utf-8 -*-
"""候选票所在格的同格历史（零后视镜，_竞价池样本_auction.json + 温度表）"""
import json
from pathlib import Path
L = Path(r'D:\股票数据\市场数据\_学习')
S = json.load(open(L / '_竞价池样本_auction.json', encoding='utf-8'))
T = json.load(open(L / '_市场温度表.json', encoding='utf-8'))
print('样本 n=', len(S), ' 窗口', S[0]['日'], '~', S[-1]['日'])
for r in S:
    r['T'] = (T.get(r['日']) or {}).get('温度')
print('温度可join', sum(1 for r in S if r['T'] is not None))

def st(sub, lab):
    if not sub:
        print('%-46s n=0' % lab); return
    n = len(sub); w = sum(1 for r in sub if r['执行'] > 0)
    m = sum(r['执行'] for r in sub) / n
    g5 = sum(1 for r in sub if r['T1高开'] >= 5) / n * 100
    print('%-46s n=%4d 胜%5.1f%% 均%6.2f%% P(gap≥5)=%5.1f%%' % (lab, n, 100.0 * w / n, m, g5))

def band(sub, lab):
    print('  -- %s n=%d' % (lab, len(sub)))
    for lo, hi, nm in [(-99, 0, '低开≤0'), (0, 5, '高开0~5'), (5, 99, '高开≥5')]:
        s2 = [r for r in sub if lo <= r['T1高开'] < hi]
        if s2:
            w = sum(1 for r in s2 if r['执行'] > 0)
            print('     %-8s n=%3d 胜%5.1f%% 均%6.2f%%' % (nm, len(s2), 100.0 * w / len(s2),
                                                          sum(r['执行'] for r in s2) / len(s2)))

f = lambda **kw: [r for r in S if all(
    (k == '信号' and r['信号'] == v) or (k == '连板' and r['连板'] == v) or
    (k == 'lb' and v(r['连板'])) or (k == 'fb' and r['封单比'] is not None and v(r['封单比'])) or
    (k == 'zb' and v(r['炸板'])) or (k == 'seg' and r['信号'] == v) for k, v in kw.items())]

print('\n=== 候选格 ===')
st(S, '全池基准')
c1 = f(信号='秒板', 连板=2, fb=lambda x: 0.5 <= x < 1.5, zb=lambda x: x >= 1)
st(c1, '秒板|2板|封0.5~1.5|炸1+  [000603]')
band(c1, '同格')
c1b = [r for r in c1 if r['T'] and 40 <= r['T'] < 65]
st(c1b, '  同上 × 温度中40~65')
c2 = f(信号='秒板', 连板=2, fb=lambda x: 0.5 <= x < 1.5, zb=lambda x: x == 0)
st(c2, '秒板|2板|封0.5~1.5|未炸  [603657/600641/002529]')
band(c2, '同格')
c3 = f(信号='秒板', 连板=2, fb=lambda x: x < 1.5, zb=lambda x: x >= 1)
st(c3, '秒板|2板|封<1.5|炸1+')
c4 = f(信号='秒板', 连板=1, fb=lambda x: x < 1.5)
st(c4, '秒板|首板|封<1.5  [603212 0.85]')
band(c4, '同格')
c5 = f(信号='一字', 连板=lambda x: x >= 3, fb=lambda x: x >= 4)
st(c5, '一字|3板+|封≥4  [002578/601599/603381]')
band(c5, '同格')
c6 = f(信号='秒板', 连板=2, fb=lambda x: x >= 4)
st(c6, '秒板|2板|封≥4  [301697 11.78]')
c7 = f(信号='秒板', 连板=lambda x: x >= 3)
st(c7, '秒板|3板+')
c8 = [r for r in S if r['炸板'] >= 3 and r['封单比'] < 1.5]
st(c8, '炸3+|封<1.5')
band(c8, '同格')

print('\n=== 高开档 × 温度（执行口径）===')
for nm, cond in [('中40~65', lambda r: r['T'] and 40 <= r['T'] < 65), ('冷<40', lambda r: r['T'] and r['T'] < 40)]:
    sub = [r for r in S if cond(r)]
    st(sub, ni := ('全部 ' + nm))
    for lo, hi, bnm in [(-99, 0, '低开≤0'), (0, 5, '0~5'), (5, 99, '≥5')]:
        s2 = [r for r in sub if lo <= r['T1高开'] < hi]
        st(s2, '   %s × %s' % (nm, bnm))
