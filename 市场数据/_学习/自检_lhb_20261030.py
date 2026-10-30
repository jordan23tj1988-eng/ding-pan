# -*- coding: utf-8 -*-
"""lhb 路线四件套收尾自检（20261030）。全绿则打印 OK。"""
import csv, json, re, sys
from pathlib import Path

L = Path('D:/股票数据/市场数据/_学习')
D = '20261030'
fails = []


def chk(cond, msg):
    if not cond:
        fails.append(msg)


J = json.load(open(L / f'lhb判断_{D}.json', encoding='utf-8'))
P = json.load(open(L / f'交易计划_lhb_{D}.json', encoding='utf-8'))
C = json.load(open(L / f'能力使用回执_lhb_{D}.json', encoding='utf-8'))
H = (L / f'lhb_body_{D}.html').read_text(encoding='utf-8')

# 1 结构
chk(J['日期'] == D and J['路'] == 'lhb', '判断 日期/路 不符')
chk(P['日期'] == D and P['路'] == 'lhb', '计划 日期/路 不符')
chk(C['route'] == 'lhb', '回执 route 不符')
chk(bool(J['判断']['结论'].strip()), '判断结论为空')
chk(len(J['判断']['证据']) >= 5, '证据条数 <5')
chk(isinstance(J['判断']['置信度'], int) and 0 <= J['判断']['置信度'] <= 100, '置信度越界')
chk(J['判断']['档位'] in ('A', 'B', 'C'), '档位非法')
chk(bool(J['判断']['可证伪条件']), '可证伪条件为空')
chk(bool(J['判断']['独立盲区声明']), '独立盲区声明为空')
chk(len(J['认知迭代']) >= 3, '认知迭代 <3')
chk('承接Master指派' in J['深挖'] and '深挖结果' in J['深挖'], '深挖缺承接格式')

# 2 标的 ∈ 当日 zt_pool
zt = {r['代码']: r for r in csv.DictReader((Path('D:/股票数据/市场数据') / D / 'zt_pool.csv').open(encoding='utf-8-sig'))}
targets = J['荐票']['标的']
chk(0 < len(targets) <= 3, f'荐票标的数非法 {len(targets)}')
for t in targets:
    chk(t['代码'] in zt, f"{t['代码']} 不在 zt_pool")
    chk(t['类型'] in ('荐票', '观察'), f"{t['代码']} 类型非法 {t['类型']}")
    chk(bool(t['历史对照'].strip()) and 'n=' in t['历史对照'], f"{t['代码']} 历史对照缺量化对照")
    chk(bool(t['理由'].strip()), f"{t['代码']} 理由为空")
chk(sum(1 for t in targets if t['类型'] == '荐票') <= 3, '荐票超 3 只')

# 3 污染嫌疑不得入荐票
dual = json.load(open(L / f'龙虎榜双源校验_{D}.json', encoding='utf-8'))
bad = {x['代码'] for x in (dual.get('强矛盾清单') or [])}
leak = bad & {t['代码'] for t in targets}
chk(not leak, f'污染嫌疑入荐票: {leak}')
chk(bool(dual.get('强矛盾清单')), '双源强矛盾清单为空（应复核）')
for code in bad:
    chk(code in json.dumps(J, ensure_ascii=False), f'强矛盾 {code} 未在证据中处置')

# 4 交易计划在持票无漏
st = json.load(open(L / '_模拟盘/lhb/状态.json', encoding='utf-8'))
held = {h['代码'] for h in (st.get('持仓') or [])}
plan_sell = {s['代码'] for s in P['sells']}
miss = held - plan_sell
chk(not miss, f'在持票未表态: {miss}')
for b in P['buys']:
    chk(b['代码'] in zt, f"买入 {b['代码']} 不在 zt_pool")
    chk(isinstance(b['权重%'], int) and 0 < b['权重%'] <= 100, f"权重非法 {b['权重%']}")
    g = b['buy_gate']
    chk(isinstance(g.get('min_gap_pct'), (int, float)) and isinstance(g.get('max_gap_pct'), (int, float)), 'buy_gate 非法')
chk(bool(P['notes'].strip()), 'notes 为空')
if not P['buys']:
    chk('空仓' in P['notes'] or '理由' in P['notes'], '空仓未写理由')

# 5 能力回执
pre = json.load(open(L / f'能力预加载_{D}.json', encoding='utf-8'))['routes']['lhb']['records']
pre_ids = {r['id'] for r in pre}
chk(set(C['considered_ids']) == pre_ids, f"considered_ids 与预加载不一致 {set(C['considered_ids']) ^ pre_ids}")
ans = {a['id'] for a in C['applied']} | {r['id'] for r in C['rejected']}
chk(ans == pre_ids, f'能力未逐条回应 {pre_ids - ans}')
chk(C['status'] in ('applied', 'rejected_all', 'no_eligible_capabilities'), 'status 非法')
for a in C['applied']:
    chk(bool(a['effect'].strip()) and bool(a['source_locator'].strip()), f"{a['id']} 缺 effect/source_locator")

# 6 HTML
titles = ['一 席位综合判断', '二 资金温度与席位结构', '三 龙虎榜台账 · 席位量化扫描',
          '四 全市场席位分档库', '五 自主深挖', '六 认知迭代']
h2 = re.findall(r'<h2>(.*?)</h2>', H)
chk(len(h2) == 6, f'h2 数量 {len(h2)}')
chk(h2 == titles, f'h2 标题不一致: {h2}')
opens, closes = len(re.findall(r'<div\b', H)), len(re.findall(r'</div>', H))
chk(opens == closes, f'div 不配平 {opens} vs {closes}')
depth = 0
for tag in re.findall(r'<div\b[^>]*>|</div>', H):
    depth += 1 if tag.startswith('<div') else -1
    chk(depth >= 0, 'div 出现负深度')
chk(depth == 0, f'div 嵌套未归零 depth={depth}')
chk(not re.search(r'>\s*(null|None|NaN|undefined)\s*<', H), 'HTML 有裸 null/None')
chk('class="trow"' in H, '表格未用 trow')
chk(H.count('class="obs"') == sum(1 for t in targets), 'obs 卡数 ≠ 标的数')
chk('class="obswrap obslist"' in H, '缺 obslist 外壳')
for t in targets:
    chk(t['名称'] in H and t['代码'] in H, f"{t['代码']} 卡片缺失")
    chk(t['类型'] in H, f"{t['代码']} 类型未上卡")
chk('obs-head' in H and 'obs-nm' in H and 'obs-pos' in H and 'obs-watch' in H and 'obs-lab' in H
    and 'obs-rec' in H and 'obs-lab2' in H, 'obs 组件结构不全')

# 7 无自造类：body 内 class 必须在已知集合
known = {'obs', 'obslist', 'obswrap', 'obs-head', 'obs-nm', 'obs-pos', 'obs-watch', 'obs-lab', 'obs-lab2',
         'obs-rec', 'card', 'mut', 'trow', 'hint', 's-ok', 's-mid'}
used = set()
for c in re.findall(r'class="([^"]+)"', H):
    used |= set(c.split())
chk(used <= known, f'自造 class: {used - known}')

print(f'判断 {J["判断"]["档位"]} 置信 {J["判断"]["置信度"]} 标的 {len(targets)} 只(h2 {len(h2)}/div {opens}) 强矛盾 {len(bad)} 只已全部处置')
for t in targets:
    print(f'  {t["代码"]} {t["名称"]} {t["类型"]}')
if fails:
    print('FAIL:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('OK')
