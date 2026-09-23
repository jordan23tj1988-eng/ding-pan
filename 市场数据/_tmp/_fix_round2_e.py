# -*- coding: utf-8 -*-
"""round2d 续: review_pages 跳过被并入的段(段二) —— 精确匹配版。"""
from pathlib import Path

p = Path('D:/股票数据/市场数据/review_pages.py')
t = p.read_text(encoding='utf-8')
done = []

old = """        golden_bodies = _golden_index.build(model, d,
                                           env_basis=str((_zj_env or {}).get('环境加权依据') or ''))
        _want = [s['id'] for s in render_sections]"""
new = """        golden_bodies = _golden_index.build(model, d,
                                           env_basis=str((_zj_env or {}).get('环境加权依据') or ''))
        # 段二(拐点预警)按黄金版版式并入段一 .rowC 右栏 → 不再单独成段渲染。
        _absorbed = tuple(getattr(_golden_index, 'ABSORBED_SECTIONS', ()))
        _want = [s['id'] for s in render_sections if s['id'] not in _absorbed]"""
assert t.count(old) == 1, 'build 调用点'
t = t.replace(old, new); done.append('build 调用点 _absorbed')

old = """    for number, s in zip('一二三四五六七', render_sections):
        body += '<section id="' + e(s["id"]) + '"><h2>' + number + ' ' + e(s["title"]) + '</h2>'"""
new = """    for number, s in zip('一二三四五六七', render_sections):
        if GOLDEN_INDEX_ON and s['id'] in _absorbed:
            continue  # 已并入段一右栏(黄金版 .rowC 版式), 标题随卡在右栏内
        body += '<section id="' + e(s["id"]) + '"><h2>' + number + ' ' + e(s["title"]) + '</h2>'"""
assert t.count(old) == 1, '循环'
t = t.replace(old, new); done.append('循环跳过被并入段')

old = """    GOLDEN_INDEX_ON = (route in GOLDEN_INDEX_ROUTES
                       and tuple(x['id'] for x in model['sections']) == GOLDEN_INDEX_SECTIONS)"""
new = """    GOLDEN_INDEX_ON = (route in GOLDEN_INDEX_ROUTES
                       and tuple(x['id'] for x in model['sections']) == GOLDEN_INDEX_SECTIONS)
    _absorbed = ()  # 黄金骨架中被并入其它段的段(仅 GOLDEN_INDEX_ON 时可能非空)"""
assert t.count(old) == 1, 'GOLDEN_INDEX_ON'
t = t.replace(old, new); done.append('_absorbed 默认值')

p.write_text(t, encoding='utf-8', newline='\n')
print('\n'.join('OK  ' + d for d in done))
