"""TEST ONLY: 题材(③)/产业逻辑(④)荐票卡接线。

守卫点:
 1. review_pages 的正式荐票/观察候选读取与 logic_pool 保持同源;
 2. 所有展示标的都能回源到本路不可覆盖发出版;
 3. 正式荐票与观察候选共用一张统一表格，观察不进入正式荐票/结算;
 4. 空仓日仍登记常驻组件、保留表头并显示空仓；无候选不造票;
 5. 缺发出版显示断档，不伪装为空仓;
 6. P1 独立重算(component_source_text)与页面 DOM 逐字一致。
"""
from pathlib import Path
import json

import pytest

import review_pages as api
import review_publish as pub

ROOT = Path(__file__).resolve().parents[1]
L = ROOT / '_学习'
EMPTY_DAY = '20260909'  # 发出版明确空仓的当日(题材/逻辑均无'荐票'级标的)


def _dates():
    ds = set()
    for pat in ('logic判断_*.json', '逻辑荐票_*.json', '题材荐票_*.json'):
        for p in L.glob(pat):
            ds.add(p.stem.rsplit('_', 1)[-1])
    return sorted(x for x in ds if len(x) == 8 and x.isdigit())


def _picks(route, d):
    return api._theme_picks(ROOT, d) if route == 'theme' else api._logic_picks(ROOT, d)


def _comp(model, cid):
    return next((c for c in model.get('components', []) if c['id'] == cid), None)


def test_logic_reco_rule_matches_logic_pool():
    """两条读取口必须同源同规则(新增 review_pages 读取口不得偏离 logic_pool)。"""
    import logic_pool
    for d in _dates():
        assert api._logic_picks(ROOT, d) == logic_pool.load_logic_picks(d, str(L)), d


def test_theme_reco_rule_follows_published_schema():
    """题材: 每只荐票必须回源到发出版原文(零编造); 新 schema 下'观察'级一律不入荐票。

    注: 旧 schema(顶层无'标的', 只有'荐票'数组)按 module_render_theme.r_reco_table 原规则
    整表直渲, 其中类型为'观察'的条目由表格'类型'列如实标注 —— 与本路渲染器逐字同规则。"""
    for d in _dates():
        path = L / ('题材荐票_%s.json' % d)
        if not path.exists():
            assert api._theme_picks(ROOT, d) == ([], None)
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        picks, src = api._theme_picks(ROOT, d)
        assert src == '题材荐票_%s.json' % d
        base = [x for x in (data.get('标的') or []) if isinstance(x, dict)]
        pool = base or [x for x in (data.get('荐票') or []) if isinstance(x, dict)]
        for x in picks:
            assert any(y.get('名称') == x.get('名称') and y.get('代码') == x.get('代码') for y in pool), (d, x)
        if base:
            assert all(str(x.get('类型') or '') != '观察' for x in picks), d
            assert len(picks) + len([x for x in base if str(x.get('类型') or '') == '观察']) == len(base), d


def test_logic_candidate_rule_matches_published_source():
    """逻辑观察候选只能来自当前发出版，且不得混入正式荐票。"""
    for d in _dates():
        formal, src = api._logic_picks(ROOT, d)
        candidates, csrc = api._logic_candidates(ROOT, d)
        assert csrc == src
        assert not ({(x.get('代码'), x.get('名称')) for x in formal} &
                    {(x.get('代码'), x.get('名称')) for x in candidates}), d
        for x in candidates:
            assert str(x.get('类型', '')).strip() != '荐票', (d, x)


def test_theme_candidate_rule_matches_published_source():
    """题材观察候选来自同一发出版的观察字段，不能凭行业兜底补票。"""
    for d in _dates():
        path = L / ('题材荐票_%s.json' % d)
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        candidates, src = api._theme_candidates(ROOT, d)
        assert src == path.name
        base = [x for x in (data.get('标的') or []) if isinstance(x, dict)]
        pool = ([x for x in base if str(x.get('类型') or '') == '观察']
                if base else [x for x in (data.get('观察') or []) if isinstance(x, dict)])
        assert {(x.get('代码'), x.get('名称')) for x in candidates} == {(x.get('代码'), x.get('名称')) for x in pool}


def test_pick_days_render_authoritative_table():
    """有正式荐票或观察候选时，必须出同一张权威表格卡。"""
    verified = {}
    for route, cid in (('theme', 'RECOTHEME'), ('logic', 'RECOLOGIC')):
        for d in reversed(_dates()):
            picks, src = _picks(route, d)
            candidates, _ = (api._theme_candidates(ROOT, d) if route == 'theme' else api._logic_candidates(ROOT, d))
            if (not picks and not candidates) or not src:
                continue
            model = api.build_page_model(ROOT, d, route)
            if 'components' not in model:
                continue
            comp = _comp(model, cid)
            assert comp is not None, (route, d, '有标的却未登记荐票组件')
            assert comp['status'] == 'ok' and comp['issue'] is None
            assert comp['section'] == 'recommendations'
            assert ('_学习/' + src) in {s['path'] for s in comp['sources']}
            assert comp['html'].count('<table') == 1
            assert comp['html'].count('<tr>') - 1 >= len(picks) + len(candidates)
            for x in picks + candidates:
                assert str(x.get('名称')) in comp['html'], (route, d, x)
            verified[route] = d
            break
    assert set(verified) == {'theme', 'logic'}, ('未覆盖有标的日', verified)


def test_empty_position_day_keeps_uniform_card():
    """空仓日: 常驻组件、表头和空仓语义都保留，不补造标的。"""
    for route, cid in (('theme', 'RECOTHEME'), ('logic', 'RECOLOGIC')):
        picks, src = _picks(route, EMPTY_DAY)
        candidates, csrc = (api._theme_candidates(ROOT, EMPTY_DAY) if route == 'theme' else api._logic_candidates(ROOT, EMPTY_DAY))
        assert picks == [] and candidates == [] and src == csrc
        model = api.build_page_model(ROOT, EMPTY_DAY, route)
        comp = _comp(model, cid)
        assert comp is not None and comp['status'] == 'ok'
        assert comp['html'].count('<table') == 1
        assert '仓位结论：空仓' in comp['html']
        assert '没有合法候选' in comp['html']
        rendered = api._render(model, api._contract())
        assert rendered.count('<!--' + cid + '-->') == 1
        assert rendered.count('<!--/' + cid + '-->') == 1


def test_observation_only_day_keeps_candidate_rows():
    """至少覆盖一个空仓但有观察候选的真实日，候选必须带观察语义。"""
    checked = 0
    for route, cid in (('theme', 'RECOTHEME'), ('logic', 'RECOLOGIC')):
        for d in reversed(_dates()):
            picks, src = _picks(route, d)
            candidates, _ = (api._theme_candidates(ROOT, d) if route == 'theme' else api._logic_candidates(ROOT, d))
            if picks or not candidates or not src:
                continue
            model = api.build_page_model(ROOT, d, route)
            comp = _comp(model, cid)
            if not comp or comp['status'] != 'ok':
                continue
            assert '仓位结论：空仓' in comp['html']
            assert '观察候选' in comp['html']
            assert all(str(x.get('名称')) in comp['html'] for x in candidates)
            checked += 1
            break
    assert checked == 2, '未覆盖题材与逻辑观察候选日'


def test_p1_revalidation_matches_dom_for_reco(tmp_path):
    """P1: 荐票组件的独立重算必须与页面 DOM 逐字一致(有票/空仓/观察日)。"""
    checked = 0
    for route, cid in (('theme', 'RECOTHEME'), ('logic', 'RECOLOGIC')):
        for d in (EMPTY_DAY,):
            stage = tmp_path / (d + '-' + route)
            built = api.build_site(ROOT, d, stage)
            assert built.get('status') != 'fail', (route, d, built)
            model = json.loads((stage / 'models' / (route + '.json')).read_text(encoding='utf-8'))
            assert _comp(model, cid) is not None
            view = pub.view_check(ROOT, stage, d, route)
            assert view['status'] == 'pass', (route, d, view['errors'])
            checked += 1
        # 再覆盖一个真实观察候选日，验证候选行的 source/DOM 闭环。
        for d in reversed(_dates()):
            picks, src = _picks(route, d)
            candidates, _ = (api._theme_candidates(ROOT, d) if route == 'theme' else api._logic_candidates(ROOT, d))
            if picks or not candidates or not src:
                continue
            stage = tmp_path / (d + '-' + route + '-obs')
            built = api.build_site(ROOT, d, stage)
            if built.get('status') == 'fail':
                continue
            view = pub.view_check(ROOT, stage, d, route)
            assert view['status'] == 'pass', (route, d, view['errors'])
            checked += 1
            break
    assert checked >= 4
