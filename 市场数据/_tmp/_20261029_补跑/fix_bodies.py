# -*- coding: utf-8 -*-
"""20261029 补跑: 修 auction/lhb/limitup 三页段位契约(B 类骨架归一), 判断内容零改动。
只做三件事: ①补缺失契约段的 h2 ②把机器锚移到对应 h2 之下 ③补真实数据块。
"""
import json, os, re, statistics

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')
D = '20261029'
jp = os.path.join(L, f'judgment_{D}.json')
J = json.load(open(jp, encoding='utf-8'))
bodies = J['bodies']

# ---------- 真实数据: 竞价温度 ----------
q = json.load(open(os.path.join(L, f'竞价评分_{D}.json'), encoding='utf-8'))
det = q.get('明细') or []
scores = [x['竞价分'] for x in det if isinstance(x.get('竞价分'), (int, float))]
pool_mean = round(statistics.mean(scores), 2) if scores else None

def auction_temp_block():
    rows = ''.join(
        f'<tr><td>{x.get("名称","")} <span class="mut">{x.get("代码","")}</span></td>'
        f'<td>{x.get("连板","")}</td><td>{x.get("信号","")}</td>'
        f'<td>{x.get("封单比","")}</td><td>{x.get("炸板","")}</td>'
        f'<td><b>{x.get("竞价分","")}</b></td></tr>'
        for x in sorted(det, key=lambda z: -(z.get('竞价分') or 0)))
    return (
        f'<p><b>温度 {q.get("温度")}（{q.get("温度档")}）· 池基准 {q.get("池基准值")} · '
        f'当日池均分 {pool_mean}（n={len(det)}）· 极值 {max(scores) if scores else ""}/'
        f'{min(scores) if scores else ""}。</b> 温度口径与资金温度同源（{q.get("温度档")} 档），'
        f'池基准 {q.get("池基准值")} 是分桶库中位数参照，不是个股预言：'
        f'本条只回答「今日竞价处在哪个温度层、选股池相对基准偏上还是偏下」，'
        f'温度本身不构成方向判断，须与下方闸门对账联读。</p>'
        f'<table><thead><tr><th>标的</th><th>连板</th><th>信号</th><th>封单比</th>'
        f'<th>炸板</th><th>竞价分</th></tr></thead><tbody>{rows}</tbody></table>'
        f'<p class="mut">口径：{q.get("口径","")[:120]}…</p>'
    )

# ---------- 真实数据: 席位分档库 ----------
lib = json.load(open(os.path.join(L, '_席位分档.json'), encoding='utf-8'))
seats = lib['席位']
from collections import defaultdict
agg = defaultdict(list)
for name, v in seats.items():
    agg[v['档']].append(v)
order = ['S', 'A', 'B', 'C', 'P']
label = {'S': 'S 级（顶级游资）', 'A': 'A 级', 'B': 'B 级', 'C': 'C 级', 'P': 'P 级（量化/通道）'}

def seat_tier_block():
    rows = []
    for t in order:
        vs = agg.get(t) or []
        if not vs:
            continue
        wr = round(statistics.mean([v.get('执1胜率') or 0 for v in vs]), 1)
        av = round(statistics.mean([v.get('执1均涨') or 0 for v in vs]), 2)
        small = sum(1 for v in vs if v.get('小样本'))
        rows.append(f'<tr><td><b>{label[t]}</b></td><td>{len(vs)}</td><td>{wr}%</td>'
                    f'<td>{av}%</td><td>{small}</td></tr>')
    return (
        f'<p><b>席位分档库（更新 {lib.get("更新","")} · 窗口 {lib.get("窗口","")} · '
        f'{lib.get("席位数", len(seats))} 席 / {lib.get("笔数","")} 笔）是固定段，不随当日行情变化。</b>'
        f'下表为全库各档的滚动执1画像，用来给当日 S/A 出手定基准：'
        f'S/A 档的每一笔都要与该档历史胜率/均涨对照，而不是与全市场均值对照。</p>'
        f'<table><thead><tr><th>档位</th><th>席位数</th><th>执1胜率(均)</th>'
        f'<th>执1均涨(均)</th><th>其中小样本</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
        f'<p class="mut">口径：{lib.get("口径","")[:140]}…</p>'
    )

# ---------- 1) auction: 补 temperature 段 ----------
a = bodies['auction']
anchor_h2 = '<h2>三 竞价池兑现与信号胜率</h2>'
assert anchor_h2 in a, 'auction 锚标题未找到'
# 从后往前重编号, 避免撞车
a = a.replace('<h2>六 认知迭代</h2>', '<h2>七 认知迭代</h2>')
a = a.replace('<h2>五 深挖</h2>', '<h2>六 深挖</h2>')
a = a.replace('<h2>四 明日竞价预案 · 当日池处置</h2>', '<h2>五 明日竞价预案 · 当日池处置</h2>')
a = a.replace(anchor_h2, '<h2>四 竞价池兑现与信号胜率</h2>')
a = a.replace(anchor_h2.replace('三 竞价池兑现与信号胜率', '四 竞价池兑现与信号胜率'),
              '<h2>四 竞价池兑现与信号胜率</h2>')  # 幂等
ins = '<h2>三 竞价温度 · 当日分位与池基准</h2>\n' + auction_temp_block() + '\n'
a = a.replace('<h2>四 竞价池兑现与信号胜率</h2>', ins + '<h2>四 竞价池兑现与信号胜率</h2>', 1)
# POOLLEDGER 锚补在结算段
if '<!--POOLLEDGER-->' not in a:
    a = a.replace('<h2>四 竞价池兑现与信号胜率</h2>',
                  '<h2>四 竞价池兑现与信号胜率</h2>\n<!--POOLLEDGER--><!--/POOLLEDGER-->', 1)
bodies['auction'] = a

# ---------- 2) limitup: 补 ledger 段 ----------
lu = bodies['limitup']
assert '<h2>三 炸板与虚胖检测 · 质量库</h2>' in lu, 'limitup 锚标题未找到'
lu = lu.replace('<h2>六 认知迭代</h2>', '<h2>七 认知迭代</h2>')
lu = lu.replace('<h2>五 深挖</h2>', '<h2>六 深挖</h2>')
lu = lu.replace('<h2>四 全池期望与荐票</h2>', '<h2>五 全池期望与荐票</h2>')
lu = lu.replace('<h2>三 炸板与虚胖检测 · 质量库</h2>', '<h2>四 炸板与虚胖检测 · 质量库</h2>')
lu = lu.replace('<h2>四 炸板与虚胖检测 · 质量库</h2>',
                '<h2>三 归位台账与结算</h2>\n<!--LEDGER--><!--/LEDGER-->\n<h2>四 炸板与虚胖检测 · 质量库</h2>', 1)
bodies['limitup'] = lu

# ---------- 3) lhb: 补 ledger + tiers ----------
lh = bodies['lhb']
old = '<h2>三 席位训练库 · 游资量化扫描</h2>\n<!--LHBLEDGER-->'
assert old in lh, 'lhb 锚结构未找到'
lh = lh.replace('<h2>六 认知迭代</h2>', '<h2>七 认知迭代</h2>')
lh = lh.replace('<h2>五 深挖</h2>', '<h2>六 深挖</h2>')
lh = lh.replace('<h2>四 席位荐票与明日预案</h2>', '<h2>五 席位荐票与明日预案</h2>')
lh = lh.replace(old, '<h2>三 龙虎榜台账 · 席位动向与净买</h2>\n<!--LHBLEDGER-->\n'
                    '<h2>四 席位训练库 · 游资量化扫描</h2>')
if '<h2>八 全市场席位分档库</h2>' not in lh:
    lh = lh.rstrip() + '\n<h2>八 全市场席位分档库</h2>\n' + seat_tier_block() + '\n'
bodies['lhb'] = lh

json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# 同步独立 body 文件(渲染 fallback 用)
for r in ('auction', 'lhb', 'limitup'):
    open(os.path.join(L, f'{r}_body_{D}.html'), 'w', encoding='utf-8').write(bodies[r])

for r in ('auction', 'lhb', 'limitup'):
    s = bodies[r]
    h2 = [re.sub(r'<[^>]+>', '', m).strip() for m in re.findall(r'<h2[^>]*>.*?</h2>', s, re.S)]
    print(r, 'len', len(s), '| h2:', h2)
    print('   anchors LHBLEDGER', s.count('<!--LHBLEDGER-->'), 'LEDGER', s.count('<!--LEDGER-->'),
          'POOLLEDGER', s.count('<!--POOLLEDGER-->'))
print('OK 写回', jp)
