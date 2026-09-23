"""黄金版主判断组件的跨页面回归门禁。

主判断只负责：标题、说明、状态 pill；证据必须留在正文/审计层。
"""
from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ('index', 'cycle', 'auction', 'lhb', 'theme', 'logic', 'limitup')


def api():
    spec = importlib.util.spec_from_file_location('hero_production', ROOT / 'review_pages.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def nodes(mod, node):
    if isinstance(node, mod._Node):
        yield node
        for child in node.children:
            yield from nodes(mod, child)


def hero(mod, html):
    return next(n for n in nodes(mod, mod._Tree(html).root) if n.attrs.get('class') == 'hero')


@pytest.mark.parametrize('route', ROUTES)
def test_every_route_hero_matches_golden_hierarchy_without_evidence_link(route):
    mod = api()
    model = mod.build_page_model(ROOT, '20260909', route)
    rendered = mod._render(model, mod._contract(), ROOT)
    actual = hero(mod, rendered)
    golden = hero(mod, Path('D:/黄金对照版717/' + route + '.html').read_text(encoding='utf8'))
    shape = lambda n: [(c.tag, c.attrs.get('class', '')) for c in n.children if isinstance(c, mod._Node)]

    # 结构一致：kick → h1 → p → stance；黄金版的页面内容可优化但显示方式不能漂移。
    # 例外(已在变更总账登记的既成改动)：涨停页 hero 内嵌 `p.hero-facts`
    # (梯队提炼/归位档 A·B·C)，由「Codex-20260915-limitup-hero-facts-root」
    # 登记并保留，黄金版 717 快照早于该改动，故只对 limitup 放行这一个节点。
    actual_shape = shape(actual)
    golden_shape = shape(golden)
    if route == 'limitup':
        actual_shape = [x for x in actual_shape if x != ('p', 'hero-facts')]
    assert actual_shape == golden_shape
    assert not any(n.tag in ('a', 'details') for n in nodes(mod, actual))
    assert any(n.tag == 'em' for n in nodes(mod, actual))
    assert len([n for n in nodes(mod, actual) if 'pill' in n.attrs.get('class','').split()]) == len([
        n for n in nodes(mod, golden) if 'pill' in n.attrs.get('class','').split()
    ])
    raw = mod._safe_html(actual)
    for text in ('截至 2026-09-09 收盘',):
        assert text in raw
    for text in ('回看完整判断与证据', '原判完整依据', '证据回链'):
        assert text not in raw
    # 证据并未丢失：每条模型 claim 仍在页面其他层有锚点。
    for claim in model['claims']:
        theme_hidden = route == 'theme' and (
            claim.get('section') in ('matrix', 'lifecycle', 'research', 'cognition') or
            claim.get('source_pointer','').startswith('/bodies/') or
            (claim.get('section') == 'recommendations' and claim.get('role') == 'observation')
        )
        if theme_hidden:
            assert 'id="claim-' + claim['id'] + '"' not in rendered
        else:
            assert 'id="claim-' + claim['id'] + '"' in rendered


def test_golden_hero_policy_covers_all_contract_routes():
    mod = api()
    assert tuple(mod.GOLDEN_HERO_ROUTES) == ROUTES
