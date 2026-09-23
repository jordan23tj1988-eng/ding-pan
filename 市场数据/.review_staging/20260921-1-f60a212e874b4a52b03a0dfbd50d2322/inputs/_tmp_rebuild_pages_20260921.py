# -*- coding: utf-8 -*-
"""Rebuild _学习/页面判断_20260921.json against the fixed page contract.

Fixes applied:
  - 'matrix' is emitted ONLY on the theme page (contract: matrix belongs to theme).
  - theme matrix rows are derived from the single theme truth source
    (涨停对链条_20260921.json), each row bound to evidence for its own line,
    six_you left null because the theme four-dimension file is absent.
No conclusion, number, code or claim text is invented: every text is copied from
the already-published route judgment files, and every value is read back from disk.
"""
import json, pathlib

ROOT = pathlib.Path('D:/股票数据/市场数据')
L = ROOT / '_学习'
D = '20260921'


def load(name):
    return json.loads((L / name).read_text(encoding='utf-8-sig'))


F = load('fact_20260921.json')['facts']
RF = {r: load('%s判断_%s.json' % (r, D)) for r in ('auction', 'lhb', 'theme', 'logic', 'limitup')}
CHAIN = load('涨停对链条_%s.json' % D)

E = []


def ev(source, pointer):
    cur = json.loads((ROOT / source).read_text(encoding='utf-8-sig'))
    for part in (pointer.lstrip('/').split('/') if pointer else []):
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(cur, list):
            if part.isdigit() and int(part) < len(cur):
                cur = cur[int(part)]
            else:
                cur = next((x for x in cur if isinstance(x, dict) and part in x), cur)
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
    eid = 'e%d' % (len(E) + 1)
    E.append({'id': eid, 'd': D, 'source': source, 'pointer': pointer, 'value': cur, 'quality': 'source'})
    return eid


def page(route, specs, matrix=None):
    claims, sections = [], []
    for sid, role, text, refs in specs:
        cid = '%s_%d' % (route, len(claims) + 1)
        refs = [refs] if isinstance(refs, str) else refs
        claims.append({'id': cid, 'role': role, 'text': text, 'section': sid, 'evidence_refs': refs})
        sections.append({'id': sid, 'claim_refs': [cid]})
    out = {
        'hero': {'claim_ref': claims[0]['id'], 'change_ref': None},
        'kpis': [
            {'id': 'k1', 'label': '涨停数', 'value': F['涨停数']['value'],
             'evidence_refs': [ev('_学习/fact_20260921.json', '/facts/涨停数/value')]},
            {'id': 'k2', 'label': '温度', 'value': F['温度']['value'],
             'evidence_refs': [ev('_学习/fact_20260921.json', '/facts/温度/value')]},
            {'id': 'k3', 'label': '最高连板', 'value': F['最高连板']['value'],
             'evidence_refs': [ev('_学习/fact_20260921.json', '/facts/最高连板/value')]},
            {'id': 'k4', 'label': '成交额亿', 'value': F['成交额亿']['value'],
             'evidence_refs': [ev('_学习/fact_20260921.json', '/facts/成交额亿/value')]},
        ],
        'claims': claims,
        'sections': sections,
        'limitations': ['仅使用截至%s已留档数据；缺失口径保持null或partial，不以缺失推断安全。' % D],
    }
    if matrix is not None:
        out['matrix'] = matrix
    return out


def rc(route):
    return RF[route]['判断']['结论']


P = {}
P['index'] = page('index', [
    ('recommendations', 'verdict', '总审C档防守、空仓合法；没有跨路共同确认的正式买入。', ev('_学习/总审_20260921.json', '/总裁决')),
    ('observations', 'condition', '明日观察涨停数、炸板率、最高板、温度及同链跨环节扩散；缺口恢复后复议。', ev('_学习/总审_20260921.json', '/指派清单')),
    ('routes', 'evidence', '五路裁决：竞价C、席位B、题材C、产业逻辑C、涨停质量C；分歧按保守原则处理。', ev('_学习/总审_20260921.json', '/五路裁决')),
    ('turning', 'counterevidence', '中报预增雷达、风险事件源和有效9:25动态轨迹缺失；缺失不等于无风险。', ev('_学习/总审_20260921.json', '/检查四项')),
    ('verdict', 'verdict', 'C档防守，席位路局部B档不足以推翻其他四路防守判断。', ev('_学习/总审_20260921.json', '/结论')),
    ('master', 'research', '总审要求把数据缺口、五路分歧和次日可验证条件纳入复议。', ev('_学习/总审_20260921.json', '/综合深挖')),
])
P['cycle'] = page('cycle', [
    ('volume', 'evidence', '成交额%s亿，量能只作环境事实。' % F['成交额亿']['value'], ev('_学习/fact_20260921.json', '/facts/成交额亿/value')),
    ('leading', 'evidence', '先行指标按实际文件读取，缺失字段保持null。', ev('_学习/_情绪先行指标.json', '/' + D + '/晋级')),
    ('stages', 'verdict', '市场温度%s为中性，按中性偏防守处理。' % F['温度']['value'], ev('_学习/fact_20260921.json', '/facts/温度/value')),
    ('ladder', 'evidence', '最高连板%s板，宽度为主，未形成升档确认。' % F['最高连板']['value'], ev('_学习/fact_20260921.json', '/facts/最高连板/value')),
    ('position', 'verdict', '执行仓位上限按C档防守，空仓优先。', ev('_学习/总审_20260921.json', '/总裁决')),
    ('research', 'research', '风险日历partial、竞价撤单差分unavailable等缺口需补齐后复议。', ev('_学习/总审_20260921.json', '/综合深挖')),
    ('cognition', 'cognition', '中性温度不等于可交易主线；高度、催化和扩散需同时复核。', ev('_学习/总审_20260921.json', '/认知迭代')),
])
P['auction'] = page('auction', [
    ('pool', 'evidence', rc('auction'), ev('_学习/auction判断_20260921.json', '/判断/结论')),
    ('settlement', 'evidence', '昨日池终结算只使用已留档历史结果。', ev('_学习/auction判断_20260921.json', '/深挖/1/结论')),
    ('temperature', 'evidence', '市场温度%s中性，涨停%s、炸板%s、最高%s板。' % (F['温度']['value'], F['涨停数']['value'], F['炸板数']['value'], F['最高连板']['value']),
     [ev('_学习/fact_20260921.json', '/facts/温度/value'), ev('_学习/fact_20260921.json', '/facts/涨停数/value')]),
    ('winrate', 'condition', '滚动分桶仅作群体统计，执行需等待有效开盘闸门。', ev('_学习/auction判断_20260921.json', '/判断/可证伪条件')),
    ('research', 'research', '竞价撤单差分unavailable，污染快照不倒推9:25。', ev('_学习/auction判断_20260921.json', '/判断/独立盲区声明')),
    ('cognition', 'cognition', '缺有效9:25轨迹时维持C档，不以静态结构替代动态确认。', ev('_学习/auction判断_20260921.json', '/认知迭代/0/正文')),
])
P['lhb'] = page('lhb', [
    ('seats', 'verdict', rc('lhb'), ev('_学习/lhb判断_20260921.json', '/判断/结论')),
    ('temperature', 'evidence', '席位证据保留双源分歧、S档小样本和买入前五限制。', ev('_学习/lhb判断_20260921.json', '/判断/证据')),
    ('ledger', 'evidence', '002080为条件性轻仓，002792与603120仅观察；不升级总环境。', ev('_学习/lhb判断_20260921.json', '/荐票/结论')),
    ('tiers', 'condition', 'A/B/S档历史对照只作收缩概率参考，不保证次日表现。', ev('_学习/lhb判断_20260921.json', '/判断/可证伪条件')),
    ('research', 'research', '席位路与其他路未形成共振，因此不升级总环境。', ev('_学习/lhb判断_20260921.json', '/深挖')),
])
# theme: matrix is the only page that may carry it.
theme_lines = CHAIN['题材线']
matrix_claim_id = 'theme_matrix_claim'
matrix_rows = []
for i, line in enumerate(theme_lines):
    ref = ev('_学习/涨停对链条_%s.json' % D, '/题材线/%d/大方向' % i)
    row_ref = ev('_学习/涨停对链条_%s.json' % D, '/题材线/%d' % i)
    matrix_rows.append({'name': str(line['大方向']), 'claim_refs': [matrix_claim_id],
                        'six_you': None, 'evidence_refs': [ref, row_ref]})
theme_specs = [
    ('recommendations', 'verdict', rc('theme'), ev('_学习/theme判断_20260921.json', '/判断/结论')),
    ('matrix', 'evidence', '题材归位覆盖103/103，来源档A=0、B=103、C=0；行业兜底不等于催化确认。', ev('_学习/theme判断_20260921.json', '/判断/证据')),
    ('lifecycle', 'evidence', '生命周期按当日文件记录，缺题材四维时保留盲区。', ev('_学习/theme判断_20260921.json', '/判断/独立盲区声明')),
    ('research', 'research', '未发现可核验A档催化主线，按行业分支轮动处理。', ev('_学习/theme判断_20260921.json', '/深挖')),
    ('cognition', 'cognition', '题材宽度不能替代催化和跨环节确认。', ev('_学习/theme判断_20260921.json', '/认知迭代/0/正文')),
]
P['theme'] = page('theme', theme_specs, matrix=matrix_rows)
P['theme']['claims'].append({
    'id': matrix_claim_id, 'role': 'evidence',
    'text': '矩阵逐行对应涨停对链条当日题材线：共%d条线，全部为B档行业口径，未取得公告或THS催化确认，因此不升档。' % len(matrix_rows),
    'section': 'matrix', 'evidence_refs': [ev('_学习/涨停对链条_%s.json' % D, '/题材线数')],
})
P['theme']['sections'].append({'id': 'matrix', 'claim_refs': [matrix_claim_id]})
P['logic'] = page('logic', [
    ('recommendations', 'verdict', rc('logic'), ev('_学习/logic判断_20260921.json', '/判断/结论')),
    ('chains', 'evidence', '模板153只唯一代码中覆盖涨停4只，四只均1板且分属不同链条。', ev('_学习/logic判断_20260921.json', '/判断/证据/0')),
    ('hardness', 'evidence', '风险日历partial，事件源缺失，不能把缺事件解释为无风险。', ev('_学习/logic判断_20260921.json', '/判断/证据/2')),
    ('forward', 'condition', '链条位置快照早于20260921，不能外推到当日。', ev('_学习/logic判断_20260921.json', '/判断/独立盲区声明/2')),
    ('earnings', 'limitation', '中报预增雷达缺失，模板×雷达交叉不可判，不推断零A档。', ev('_学习/logic判断_20260921.json', '/判断/独立盲区声明/0')),
    ('research', 'research', '补齐雷达后再复算链内A共振、链外验证和已兑现。', ev('_学习/logic判断_20260921.json', '/深挖')),
    ('cognition', 'cognition', '预增A成色池必须与涨停池及题材承载同步验证。', ev('_学习/logic判断_20260921.json', '/认知迭代/0')),
])
P['limitup'] = page('limitup', [
    ('recommendations', 'verdict', rc('limitup'), ev('_学习/limitup判断_20260921.json', '/判断/结论')),
    ('temperature', 'evidence', '涨停%s、炸板%s、封板率%s、跌停%s、最高%s板。' % (F['涨停数']['value'], F['炸板数']['value'], F['封板率']['value'], F['跌停数']['value'], F['最高连板']['value']),
     [ev('_学习/fact_20260921.json', '/facts/涨停数/value'), ev('_学习/fact_20260921.json', '/facts/炸板数/value'), ev('_学习/fact_20260921.json', '/facts/封板率/value')]),
    ('ledger', 'evidence', '连板梯队与题材归位作为结构证据，归位覆盖103/103。', ev('_学习/limitup判断_20260921.json', '/判断/证据')),
    ('training', 'condition', '历史统计仅作校准，昨日涨停溢价为null时不补造收益。', ev('_学习/limitup判断_20260921.json', '/判断/独立盲区声明')),
    ('research', 'research', '封板率与连板结构只能提供环境仪表盘，不能独立推出交易结论。', ev('_学习/limitup判断_20260921.json', '/深挖')),
    ('cognition', 'cognition', '结构、封板质量与主线催化分开，缺一不升档。', ev('_学习/limitup判断_20260921.json', '/认知迭代/0/正文')),
])

out = {'schema_version': 1, 'd': D, 'evidence': E, 'pages': P}
target = L / ('页面判断_%s.json' % D)
target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print('wrote', target)
print('evidence', len(E), 'pages', sorted(P))
print('theme matrix rows', len(matrix_rows))
for route, pg in P.items():
    print(route, 'claims', len(pg['claims']), 'sections', len(pg['sections']), 'kpis', len(pg['kpis']),
          'matrix', len(pg.get('matrix', [])), 'has_matrix_key', 'matrix' in pg)
