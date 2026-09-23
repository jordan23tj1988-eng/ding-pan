# -*- coding: utf-8 -*-
"""五路+概览两块标准能力模块回归测试(2026-09-22 重写)

背景(用户指令): 「自主拓展 · 能力进化」「认知迭代 · 能力进化」是每一路(五路)与概览都该
有的公共能力，但历史实现只同步主题页 → 概览/竞价/产业逻辑/涨停页长期缺块，龙虎榜页与
旧『自主深挖/我的认知迭代』并存；本文件锁住修复后的契约：

  1) 七页(index + 五路)全部由唯一真源(_学习 能力库 + 能力进化模块.py)直出两块模块，
     不从页面搬运冻结字节；
  2) 展示层旧模块(自主深挖/我的认知迭代)不再并存(与主题/周期/龙虎榜同一口径)；
  3) 编号按各页业务段数顺延，段数漂移/缺块/重复/错位/残留旧标题 → 必须报错(门禁非空转)；
  4) 注入幂等：同输入同字节。
"""
import importlib.util
import re
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FOOT = '<div class="foot">'


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, BASE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evo():
    return _load('capability_module_under_test', '能力进化模块.py')


def _gen():
    return _load('gen_dashboard_capability', '生成盯盘台.py')


def _page(route, business_sections, legacy=()):
    """造一页: business_sections 段业务 + 可选旧展示模块。"""
    cn = '一二三四五六七八九十'
    body = ''.join('<section id="s%d"><h2>%s 业务段%d<span class="hint">说明</span></h2><p>x</p></section>'
                   % (i, cn[i - 1], i) for i in range(1, business_sections + 1))
    for title in legacy:
        body += '<h2>%s %s</h2><p>旧展示模块</p>' % (cn[business_sections], title)
        business_sections += 1
    return ('<!DOCTYPE html><html><head><title>t</title></head><body><div class="wrap">'
            '<div class="rowA"><h1>页</h1></div>%s<div class="foot">foot</div></div></body></html>' % body)


def _fixture(tmp_path):
    """造 7 页站点(含竞价/产业逻辑/涨停页的旧展示模块)，返回站点目录。"""
    site = tmp_path / 'site'
    site.mkdir()
    for route, sections in _evo().BUSINESS_SECTIONS.items():
        legacy = ('自主深挖 · 信号孵化', '我的认知迭代 · 最新') if route in ('auction', 'logic', 'limitup') else ()
        (site / (route + '.html')).write_text(_page(route, sections, legacy), encoding='utf-8')
    return site


def test_all_seven_pages_get_exactly_two_modules(tmp_path):
    """五路+概览全部拿到两块模块，且编号按各自段数顺延。"""
    gen = _gen()
    evo = _evo()
    site = _fixture(tmp_path)
    report = gen._sync_capability_blocks(site, '20260921')
    assert len(report) == len(evo.ROUTES) == 7
    for route, expected in evo.BUSINESS_SECTIONS.items():
        html = (site / (route + '.html')).read_text(encoding='utf-8')
        assert html.count('<section class="evolution"') == 2, route
        assert html.count('id="overview-evolution-sync"') == 1, route
        assert html.count(evo.SYNC_START) == 1 and html.count(evo.SYNC_END) == 1, route
        assert not evo.legacy_headings(html), route
        assert evo.verify_page(html, route, BASE, '20260921') == [], route
        blocks = re.findall(r'<section class="evolution">.*?</section>', html, re.S)
        cn = evo.NUMERALS
        assert '<h2>%s 自主拓展' % cn[expected] in blocks[0], route
        assert '<h2>%s 认知迭代' % cn[expected + 1] in blocks[1], route
        assert html.index(blocks[0]) < html.rindex(FOOT), route


def test_modules_match_single_source_and_are_idempotent(tmp_path):
    """两块模块字节必须等于当日唯一真源；重跑不叠加、不漂移。"""
    gen = _gen()
    evo = _evo()
    site = _fixture(tmp_path)
    gen._sync_capability_blocks(site, '20260921')
    first = {p.name: p.read_bytes() for p in site.glob('*.html')}
    for route in evo.ROUTES:
        blocks = re.findall(r'<section class="evolution">.*?</section>',
                            first[route + '.html'].decode('utf-8'), re.S)
        assert blocks == evo.canonical_sections(BASE, '20260921', route), route
    gen._sync_capability_blocks(site, '20260921')
    second = {p.name: p.read_bytes() for p in site.glob('*.html')}
    assert first == second


def test_gate_flags_every_kind_of_deformation(tmp_path):
    """门禁(verify_page)必须对缺块/重复/编号漂移/旧标题回归/段数漂移全部报错。"""
    evo = _evo()
    good = _page('auction', 4)
    good = re.sub(r'<div class="foot">',
                  evo.SYNC_START + '\n' + '\n'.join(evo.canonical_sections(BASE, '20260921', 'auction'))
                  + '\n' + evo.SYNC_END + '\n' + FOOT, good, count=1)
    good = good.replace('</head>', '<style id="overview-evolution-sync">%s</style></head>' % evo.CSS, 1)
    assert evo.verify_page(good, 'auction', BASE, '20260921') == []

    mutations = {
        '缺一块': good.replace('<section class="evolution">', '<section class="evolutionX">', 1),
        '重复块': good.replace(FOOT, '<section class="evolution"><h2>五 自主拓展 · 能力进化</h2></section>' + FOOT, 1),
        '编号漂移': good.replace('<h2>五 自主拓展', '<h2>九 自主拓展', 1),
        '旧标题回归': good.replace(FOOT, '<h2>五 自主深挖 · 信号孵化</h2><p>x</p>' + FOOT, 1),
        '旧样式残留': good.replace('</head>', '<style id="evolution-style-sync">x</style></head>', 1),
        '业务段数漂移': good.replace('<h2>四 业务段4', '<h2>四X 业务段4', 1),
    }
    for name, html in mutations.items():
        assert evo.verify_page(html, 'auction', BASE, '20260921'), name


def test_missing_page_is_refused(tmp_path):
    """七页缺一页时必须报错，不能只处理存在的页面。"""
    gen = _gen()
    site = _fixture(tmp_path)
    (site / 'limitup.html').unlink()
    try:
        gen._sync_capability_blocks(site, '20260921')
    except RuntimeError as exc:
        assert '缺页' in str(exc)
    else:
        raise AssertionError('should refuse to process an incomplete site')


def test_publish_gate_reports_missing_modules(tmp_path):
    """发布门禁(review_publish.validate_capability_blocks)对缺块站点必须产出错误。"""
    publish = _load('review_publish_capability', 'review_publish.py')
    site = _fixture(tmp_path)          # 未注入: 等价于历史"只同步主题页"的站点
    errors = publish.validate_capability_blocks(BASE, site, '20260921')
    assert errors, 'gate must flag pages without the standard capability blocks'
    assert any('index.html' in e for e in errors)
    assert any('残留旧模块标题' in e for e in errors)


def test_cycle_sentinel_flags_display_deformation():
    """cycle 哨兵仍必须对展示组件缺件/本路板块缺失报 FAIL(旧回归保持)。"""
    mod = _load('cycle_sentinel', 'cycle数据核对.py')
    d = '20260910'
    cn = '一二三四五六七八九十'
    own = [('volume', '一 量能台阶 · 我站在哪一阶', '<div class="steps"><div class="step"><span class="sr">≥3.8</span><span class="sn">主升2确认</span></div></div>'),
           ('leading', '二 先行指标 · 三窗触发器', '<svg viewBox="0 0 880 196"><line x1="1" y1="1" x2="2" y2="2"/></svg>'),
           ('stages', '三 情绪五阶段 · 五路周期投票', '<div class="stages"><div class="st on">退潮</div></div><!--VOTEBOARD--><div>五路周期投票</div><!--/VOTEBOARD-->'),
           ('ladder', '四 连板梯队', '<div class="cols"><div class="col"><i style="height:9%"></i><b>1</b><span>5板</span></div></div>'),
           ('position', '五 攻防 · 仓位总开关', '<div class="stages"><div class="st on">退潮</div></div><div class="posmeter"><i style="width:20%"></i></div>'),
           ('research', '六 自主深挖 · 指标与阈值孵化', '<p>待深挖清单应答：无强制应答项；今晚进度=分量钝化体检推进，见段六清单。</p>'),
           ('cognition', '七 我的认知迭代 · 最新', '<div class="tl"><div class="tli"><b>09-10</b> 温度冰点不等于买入信号，先看封板率与梯队承接。</div></div>')]
    body = ''.join('<section id="%s"><h2>%s<span class="hint">说明</span></h2>%s</section>' % (sid, title, inner)
                   for sid, title, inner in own)
    good = ('<!DOCTYPE html><html><head><title>周期情绪</title></head><body><div class="wrap">'
            '<div class="rowA"><h1>%s 周期</h1></div>%s'
            '<section class="evolution"><h2>八 自主拓展 · 能力进化</h2></section>'
            '<section class="evolution"><h2>九 认知迭代 · 能力进化</h2></section>'
            '<div class="foot">foot</div></div></body></html>' % (d, body))
    rows = {label: ok for ok, label, _detail in mod.check_page(good, d)}
    for label in ('本路七段section齐全', '段一量能台阶组件在位', '段二先行指标图/卡在位',
                  '段三五路投票块在位', '段四连板梯队条在位',
                  '段五三态+仓位条在位', '段六自主深挖有内容', '段七认知迭代有内容',
                  '能力进化模块=2', '模块在本路之后(不错位)'):
        assert rows.get(label) is True, (label, rows.get(label))

    deformed = re.sub(r'<section id="research">.*?</section>',
                      '<section class="evolution"><h2>六 自主拓展 · 能力进化</h2></section>', good, flags=re.S)
    rows_bad = {label: ok for ok, label, _detail in mod.check_page(deformed, d)}
    assert rows_bad.get('本路七段section齐全') is False

    thin = good.replace('<div class="steps">', '<div class="steps-gone">').replace('<div class="cols">', '<div class="cols-gone">')
    rows_thin = {label: ok for ok, label, _detail in mod.check_page(thin, d)}
    assert rows_thin.get('段一量能台阶组件在位') is False
    assert rows_thin.get('段四连板梯队条在位') is False
