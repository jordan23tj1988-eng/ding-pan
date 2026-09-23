# -*- coding: utf-8 -*-
"""2026-09-23 第2轮(续): 段二拐点预警按黄金版版式并入段一 .rowC 右栏。

黄金版717 实测版式(唯一基准):
  <h2>一 明日核心观察点…</h2>
  <div class="rowC"><div>…Top5 .obs 卡…</div>
    <aside class="rail"><div class="card">
      <h2 style="margin:0 0 2px;font-size:15px">拐点预警·命门温度背离</h2>
      三窗触发器(A档) pills + 点评
    </div></aside></div>
契约 CSS 已有 .rowC{grid-template-columns:1fr 340px} 与 .rail, 无需新增样式。
"""
from pathlib import Path

root = Path('D:/股票数据/市场数据')
p = root / 'module_golden_index.py'
t = p.read_text(encoding='utf-8')
done = []

# 1) 段二: 卡内自带标题(黄金版 rail 卡 h2), 内容不变
old = """def turning_block(model, d, env_basis=''):
    \"\"\"段二: 拐点预警 = 三窗触发器机器块(黄金版同套 markup) + 总审环境加权依据点评。"""
new = """def turning_block(model, d, env_basis=''):
    \"\"\"段二: 拐点预警 = 三窗触发器机器块(黄金版同套 markup) + 总审环境加权依据点评。

    版式(2026-09-23 用户指正 图3「和黄金版不一样」): 与黄金版一致地嵌在段一
    .rowC 的右栏(<aside class="rail">)内, 卡内自带 15px 小标题——所以本段不再
    单独成段(见 ABSORBED_SECTIONS), 段标记随卡一起放在右栏里。"""
assert t.count(old) == 1
t = t.replace(old, new)
done.append('turning_block docstring')

old = """    body = '<div class="card">' + (lead or ('<p class="mut">三窗触发器当日缺失：' + DASH + '</p>'))"""
new = """    body = ('<div class="card"><h2 style="margin:0 0 2px;font-size:15px">'
            '二 拐点预警 · 命门温度背离</h2>'
            + (lead or ('<p class="mut">三窗触发器当日缺失：' + DASH + '</p>')))"""
assert t.count(old) == 1
t = t.replace(old, new)
done.append('turning_block 卡内标题')

# 2) 段一: 包 .rowC, 右栏放置段二(含段标记)
old = """def recommendations_block(model, d):
    \"\"\"段一: 明日核心观察点 = 跨路筛选 Top5, 黄金 .obs 形态。\"\"\"
    comp = _comp(model, 'CROSSPICK')
    body = ''"""
new = """def recommendations_block(model, d, env_basis=''):
    \"\"\"段一: 明日核心观察点 = 跨路筛选 Top5(.obs 卡) + 右栏嵌段二 拐点预警。

    黄金版版式: <div class="rowC"><div>主栏</div><aside class="rail">拐点卡</aside></div>。
    段二段标记(<!--GOLDEN-INDEX:turning-->)随卡在右栏内, 保证哨兵C15段序核对仍成立。
    \"\"\"
    comp = _comp(model, 'CROSSPICK')
    body = ''"""
assert t.count(old) == 1
t = t.replace(old, new)
done.append('recommendations_block 签名')

old = """    else:
        body += ('<div class="card"><b>当日跨路荐票未产出</b><p class="mut">五路候选跨路筛选卡缺失: '
                 + DASH + '</p></div>')
    return _anchored(comp, body)"""
new = """    else:
        body += ('<div class="card"><b>当日跨路荐票未产出</b><p class="mut">五路候选跨路筛选卡缺失: '
                 + DASH + '</p></div>')
    rail = ('<aside class="rail"><!--GOLDEN-INDEX:turning-->'
            + turning_block(model, d, env_basis) + '<!--/GOLDEN-INDEX:turning--></aside>')
    return _anchored(comp, '<div class="rowC"><div>' + body + '</div>' + rail + '</div>')"""
assert t.count(old) == 1
t = t.replace(old, new)
done.append('recommendations_block rowC+rail')

# 3) ABSORBED_SECTIONS 常量 + build 不再单独成段
old = """GOLDEN_SECTION_IDS = ('recommendations', 'turning', 'routes', 'verdict')"""
new = """GOLDEN_SECTION_IDS = ('recommendations', 'turning', 'routes', 'verdict')
# 段二按黄金版版式并入段一 .rowC 右栏 → 不单独成段(段标记仍在页内, C15 段序不变)。
ABSORBED_SECTIONS = ('turning',)"""
assert t.count(old) == 1
t = t.replace(old, new)
done.append('ABSORBED_SECTIONS')

old = """def build(model, d, env_basis=''):
    \"\"\"返回 {section_id: 黄金骨架 html}; 只覆盖黄金四段, 能力进化两段由部署后处理注入。\"\"\"
    out = {
        'recommendations': recommendations_block(model, d),
        'turning': turning_block(model, d, env_basis),
        'routes': routes_block(model, d),
        'verdict': verdict_block(model, d),
    }"""
new = """def build(model, d, env_basis=''):
    \"\"\"返回 {section_id: 黄金骨架 html}; 只覆盖黄金四段, 能力进化两段由部署后处理注入。

    ABSORBED_SECTIONS 里的段不单独返回(其内容与段标记已在其它段内), 调用方需跳过该段。
    \"\"\"
    out = {
        'recommendations': recommendations_block(model, d, env_basis),
        'routes': routes_block(model, d),
        'verdict': verdict_block(model, d),
    }"""
assert t.count(old) == 1
t = t.replace(old, new)
done.append('build 去 turning')

p.write_text(t, encoding='utf-8', newline='\n')

# ---- review_pages.py: 跳过被并入的段 ----
p = root / 'review_pages.py'
t = p.read_text(encoding='utf-8')

old = """        golden_bodies = _golden_index.build(model, d, env_basis=_env_basis)
        _want = [s['id'] for s in render_sections]"""
new = """        golden_bodies = _golden_index.build(model, d, env_basis=_env_basis)
        # 段二(拐点预警)按黄金版版式并入段一 .rowC 右栏 → 不再单独成段渲染。
        _absorbed = tuple(getattr(_golden_index, 'ABSORBED_SECTIONS', ()))
        _want = [s['id'] for s in render_sections if s['id'] not in _absorbed]"""
assert t.count(old) == 1, 'golden build 调用点未匹配'
t = t.replace(old, new)
done.append('review_pages 段冗余剔除')

old = """    for number, s in zip('一二三四五六七', render_sections):
        body += '<section id="' + e(s["id"]) + '"><h2>' + number + ' ' + e(s["title"]) + '</h2>'"""
new = """    for number, s in zip('一二三四五六七', render_sections):
        if GOLDEN_INDEX_ON and s['id'] in _absorbed:
            continue  # 已并入段一右栏(黄金版版式), 标题随卡在右栏内
        body += '<section id="' + e(s["id"]) + '"><h2>' + number + ' ' + e(s["title"]) + '</h2>'"""
assert t.count(old) == 1, 'render_sections 循环未匹配'
t = t.replace(old, new)
done.append('review_pages 循环跳过')

# _absorbed 默认值(非黄金骨架路由)
old = """    GOLDEN_INDEX_ON = (route in GOLDEN_INDEX_ROUTES
                       and tuple(x['id'] for x in model['sections']) == GOLDEN_INDEX_SECTIONS)"""
new = """    GOLDEN_INDEX_ON = (route in GOLDEN_INDEX_ROUTES
                       and tuple(x['id'] for x in model['sections']) == GOLDEN_INDEX_SECTIONS)
    _absorbed = ()  # 黄金骨架里被并入其它段的段(仅 GOLDEN_INDEX_ON 时可能非空)"""
assert t.count(old) == 1, 'GOLDEN_INDEX_ON 未匹配'
t = t.replace(old, new)
done.append('review_pages _absorbed 默认')

p.write_text(t, encoding='utf-8', newline='\n')

print('\n'.join('OK  ' + d for d in done))
