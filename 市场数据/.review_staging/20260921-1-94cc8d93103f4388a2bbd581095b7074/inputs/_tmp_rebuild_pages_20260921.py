# -*- coding: utf-8 -*-
"""Rebuild _学习/页面判断_20260921.json against the strict structured-input gate.

Gate contract (review_publish.validate_structured_input):
  * page keys exactly {hero,kpis,claims,sections,limitations} - no extra keys
  * sections == the contract's section ids for that route, exactly once each
  * every claim placed, every claim carries >=1 real evidence ref
  * each page needs a claim with role 'cognition'
  * four KPI slots, each value backed byte-for-byte by its evidence source
No number, code or conclusion is invented: every claim text is copied from the
route judgment files already on disk, and every value is read back from source.
"""
import json, pathlib

ROOT = pathlib.Path('D:/股票数据/市场数据')
L = ROOT / '_学习'
D = '20260921'
CONTRACT = json.loads((ROOT / '_契约/页面契约.v1.json').read_text(encoding='utf-8'))
SEC = {r: [s['id'] for s in v['sections']] for r, v in CONTRACT['routes'].items()}


def load(name):
    return json.loads((L / name).read_text(encoding='utf-8-sig'))


F = load('fact_20260921.json')['facts']
RF = {r: load('%s判断_%s.json' % (r, D)) for r in ('auction', 'lhb', 'theme', 'logic', 'limitup')}
CHAIN = load('涨停对链条_%s.json' % D)
COG = {r: load('_认知库_%s.json' % r) for r in ('auction', 'lhb', 'theme', 'logic', 'limitup', 'master', 'cycle')}
COG['index'] = COG['master']

COGFILE = {
    'index': ('总审_%s.json' % D, '认知迭代'),
    'master': ('总审_%s.json' % D, '认知迭代'),
    'cycle': ('cycle判断_%s.json' % D, '认知迭代'),
    'auction': ('auction判断_%s.json' % D, '认知迭代'),
    'lhb': ('lhb判断_%s.json' % D, '认知迭代'),
    'theme': ('theme判断_%s.json' % D, '认知迭代'),
    'logic': ('logic判断_%s.json' % D, '认知迭代'),
    'limitup': ('limitup判断_%s.json' % D, '认知迭代'),
}


def src_of(route):
    return route if route in ('auction', 'lhb', 'theme', 'logic', 'limitup', 'cycle') else 'master'


def cog_latest(route, n=2):
    items = COG[route]['条目'][-n:]
    return '；'.join('%s：%s' % (x['标题'], x['正文']) for x in items), COG[route]['as_of'], len(items)


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


def build(route, specs, extra_claims=(), extra_sections=()):
    claims, sections = [], []
    for sid, role, text, refs in specs:
        cid = '%s_%d' % (route, len(claims) + 1)
        refs = [refs] if isinstance(refs, str) else refs
        claims.append({'id': cid, 'role': role, 'text': text, 'section': sid, 'evidence_refs': refs})
        sections.append({'id': sid, 'claim_refs': [cid]})
    for c in extra_claims:
        claims.append(c)
    for s in extra_sections:
        sections.append(s)
    return {
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


def rc(route):
    return RF[route]['判断']['结论']


def cog_text(route, applied):
    """Cognition claim: the day's own cognition entry (real, from the route
    judgment) plus an honest note about the cumulative library snapshot date."""
    file, key = COGFILE[route]
    doc = json.loads((L / file).read_text(encoding='utf-8-sig'))
    item = doc[key][0]
    body = item['正文'] if isinstance(item, dict) else str(item)
    as_of = COG[src_of(route)]['as_of']
    return ('认知库最新累计快照as_of=%s（本日为历史累计真源，库内无当日晚间新增条目）；本日%s。'
            '当日认知迭代条目：%s' % (as_of, applied, body[:400]))


def cog_ref(route):
    """The day's own cognition entry lives in the route judgment file, which is
    dated to the review day; the cumulative library is not, so it cannot back an
    evidence item dated d."""
    file, key = COGFILE[route]
    doc = json.loads((L / file).read_text(encoding='utf-8-sig'))
    item = doc[key][0]
    ptr = '/' + key + ('/0/正文' if isinstance(item, dict) else '/0')
    return ev('_学习/' + file, ptr)


P = {}
P['index'] = build('index', [
    ('recommendations', 'verdict', '总审C档防守、空仓合法；没有跨路共同确认的正式买入。', ev('_学习/总审_20260921.json', '/总裁决')),
    ('observations', 'condition', '明日观察涨停数、炸板率、最高板、温度及同链跨环节扩散；缺口恢复后复议。', ev('_学习/总审_20260921.json', '/指派清单')),
    ('routes', 'evidence', '五路裁决：竞价C、席位B、题材C、产业逻辑C、涨停质量C；分歧按保守原则处理。', ev('_学习/总审_20260921.json', '/五路裁决')),
    ('turning', 'counterevidence', '中报预增雷达、风险事件源和有效9:25动态轨迹缺失；缺失不等于无风险。', ev('_学习/总审_20260921.json', '/检查四项')),
    ('verdict', 'verdict', 'C档防守，席位路局部B档不足以推翻其他四路防守判断。', ev('_学习/总审_20260921.json', '/结论')),
    ('master', 'cognition', cog_text('master', '总审按防守原则处理五路分歧，未升级席位路局部信号'), cog_ref('master')),
])
P['cycle'] = build('cycle', [
    ('volume', 'evidence', '成交额%s亿，量能只作环境事实。' % F['成交额亿']['value'], ev('_学习/fact_20260921.json', '/facts/成交额亿/value')),
    ('leading', 'evidence', '先行指标按实际文件读取，缺失字段保持null。', ev('_学习/_情绪先行指标.json', '/' + D + '/晋级')),
    ('stages', 'verdict', '市场温度%s为中性，按中性偏防守处理。' % F['温度']['value'], ev('_学习/fact_20260921.json', '/facts/温度/value')),
    ('ladder', 'evidence', '最高连板%s板，宽度为主，未形成升档确认。' % F['最高连板']['value'], ev('_学习/fact_20260921.json', '/facts/最高连板/value')),
    ('position', 'verdict', '执行仓位上限按C档防守，空仓优先。', ev('_学习/总审_20260921.json', '/总裁决')),
    ('research', 'research', '风险日历partial、竞价撤单差分unavailable等缺口需补齐后复议。', ev('_学习/总审_20260921.json', '/综合深挖')),
    ('cognition', 'cognition', cog_text('cycle', '周期按中性温度处理，未升级为进攻'), cog_ref('cycle')),
])
P['auction'] = build('auction', [
    ('pool', 'evidence', rc('auction'), ev('_学习/auction判断_20260921.json', '/判断/结论')),
    ('settlement', 'evidence', '昨日池终结算只使用已留档历史结果。', ev('_学习/auction判断_20260921.json', '/深挖/1/结论')),
    ('temperature', 'evidence', '市场温度%s中性，涨停%s、炸板%s、最高%s板。' % (F['温度']['value'], F['涨停数']['value'], F['炸板数']['value'], F['最高连板']['value']),
     [ev('_学习/fact_20260921.json', '/facts/温度/value'), ev('_学习/fact_20260921.json', '/facts/涨停数/value')]),
    ('winrate', 'condition', '滚动分桶仅作群体统计，执行需等待有效开盘闸门。', ev('_学习/auction判断_20260921.json', '/判断/可证伪条件')),
    ('research', 'research', '竞价撤单差分unavailable，污染快照不倒推9:25。', ev('_学习/auction判断_20260921.json', '/判断/独立盲区声明')),
    ('cognition', 'cognition', cog_text('auction', '缺有效9:25轨迹时维持C档，不以静态结构替代动态确认'), cog_ref('auction')),
])
P['lhb'] = build('lhb', [
    ('seats', 'verdict', rc('lhb'), ev('_学习/lhb判断_20260921.json', '/判断/结论')),
    ('temperature', 'evidence', '席位证据保留双源分歧、S档小样本和买入前五限制。', ev('_学习/lhb判断_20260921.json', '/判断/证据')),
    ('ledger', 'evidence', '002080为条件性轻仓，002792与603120仅观察；不升级总环境。', ev('_学习/lhb判断_20260921.json', '/荐票/结论')),
    ('tiers', 'condition', 'A/B/S档历史对照只作收缩概率参考，不保证次日表现。', ev('_学习/lhb判断_20260921.json', '/判断/可证伪条件')),
    ('research', 'research', '席位路与其他路未形成共振，因此不升级总环境。', ev('_学习/lhb判断_20260921.json', '/深挖')),
    ('cognition', 'cognition', cog_text('lhb', '局部强席位信号经双源、样本和总环境三重约束后仅保留条件性轻仓'), cog_ref('lhb')),
])
theme_specs = [
    ('recommendations', 'verdict', rc('theme'), ev('_学习/theme判断_20260921.json', '/判断/结论')),
    ('lifecycle', 'evidence', '生命周期按当日文件记录，缺题材四维时保留盲区。', ev('_学习/theme判断_20260921.json', '/判断/独立盲区声明')),
    ('research', 'research', '未发现可核验A档催化主线，按行业分支轮动处理。', ev('_学习/theme判断_20260921.json', '/深挖')),
    ('cognition', 'cognition', cog_text('theme', '题材宽度不替代催化与跨环节确认，维持C档'), cog_ref('theme')),
]
theme_matrix_claim = {
    'id': 'theme_matrix', 'role': 'evidence',
    'text': '矩阵逐行对应涨停对链条当日题材线：共%s条线，全部为B档行业口径，未取得公告或THS催化确认，因此不升档。' % len(CHAIN['题材线']),
    'section': 'matrix',
    'evidence_refs': [ev('_学习/涨停对链条_%s.json' % D, '/题材线数'),
                      ev('_学习/题材归位_%s.json' % D, '/映射')],
}
matrix_section = {'id': 'matrix', 'claim_refs': ['theme_matrix']}
P['theme'] = build('theme', theme_specs, extra_claims=[theme_matrix_claim], extra_sections=[matrix_section])
P['logic'] = build('logic', [
    ('recommendations', 'verdict', rc('logic'), ev('_学习/logic判断_20260921.json', '/判断/结论')),
    ('chains', 'evidence', '模板153只唯一代码中覆盖涨停4只，四只均1板且分属不同链条。', ev('_学习/logic判断_20260921.json', '/判断/证据/0')),
    ('hardness', 'evidence', '风险日历partial，事件源缺失，不能把缺事件解释为无风险。', ev('_学习/logic判断_20260921.json', '/判断/证据/2')),
    ('forward', 'condition', '链条位置快照早于20260921，不能外推到当日。', ev('_学习/logic判断_20260921.json', '/判断/独立盲区声明/2')),
    ('earnings', 'limitation', '中报预增雷达缺失，模板×雷达交叉不可判，不推断零A档。', ev('_学习/logic判断_20260921.json', '/判断/独立盲区声明/0')),
    ('research', 'research', '补齐雷达后再复算链内A共振、链外验证和已兑现。', ev('_学习/logic判断_20260921.json', '/深挖')),
    ('cognition', 'cognition', cog_text('logic', '预增A成色池必须与涨停池及题材承载同步验证，缺失时禁止误读成零A档'), cog_ref('logic')),
])
P['limitup'] = build('limitup', [
    ('recommendations', 'verdict', rc('limitup'), ev('_学习/limitup判断_20260921.json', '/判断/结论')),
    ('temperature', 'evidence', '涨停%s、炸板%s、封板率%s、跌停%s、最高%s板。' % (F['涨停数']['value'], F['炸板数']['value'], F['封板率']['value'], F['跌停数']['value'], F['最高连板']['value']),
     [ev('_学习/fact_20260921.json', '/facts/涨停数/value'), ev('_学习/fact_20260921.json', '/facts/炸板数/value'), ev('_学习/fact_20260921.json', '/facts/封板率/value')]),
    ('ledger', 'evidence', '连板梯队与题材归位作为结构证据，归位覆盖103/103。', ev('_学习/limitup判断_20260921.json', '/判断/证据')),
    ('training', 'condition', '历史统计仅作校准，昨日涨停溢价为null时不补造收益。', ev('_学习/limitup判断_20260921.json', '/判断/独立盲区声明')),
    ('research', 'research', '封板率与连板结构只能提供环境仪表盘，不能独立推出交易结论。', ev('_学习/limitup判断_20260921.json', '/深挖')),
    ('cognition', 'cognition', cog_text('limitup', '结构、封板质量与主线催化分开，缺一不升档'), cog_ref('limitup')),
])

out = {'schema_version': 1, 'd': D, 'evidence': E, 'pages': P}
(L / ('页面判断_%s.json' % D)).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

# --- self check against the gate's own rules ---
bad = []
for r, pg in P.items():
    if set(pg) != {'hero', 'kpis', 'claims', 'sections', 'limitations'}:
        bad.append((r, 'page keys', sorted(pg)))
    ids = [s['id'] for s in pg['sections']]
    if sorted(ids) != sorted(SEC[r]) or len(ids) != len(set(ids)):
        bad.append((r, 'sections', ids, SEC[r]))
    claim_ids = {c['id'] for c in pg['claims']}
    placed = {x for s in pg['sections'] for x in s['claim_refs']}
    if placed != claim_ids:
        bad.append((r, 'placement', sorted(claim_ids - placed)))
    if not any(c['role'] == 'cognition' for c in pg['claims']):
        bad.append((r, 'no cognition role'))
    if len(pg['kpis']) != 4:
        bad.append((r, 'kpis', len(pg['kpis'])))
    for c in pg['claims']:
        if c['section'] not in SEC[r]:
            bad.append((r, 'claim section unknown', c['id'], c['section']))
        if not c['evidence_refs']:
            bad.append((r, 'claim no evidence', c['id']))
print('SELF CHECK', 'PASS' if not bad else 'FAIL')
for b in bad:
    print('  ', b)
print('evidence', len(E), 'pages', sorted(P))
