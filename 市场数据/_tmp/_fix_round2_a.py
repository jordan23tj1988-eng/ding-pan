# -*- coding: utf-8 -*-
"""2026-09-23 用户5点指正 —— 定点修复(只动概览路由)。

1 走马灯缺失        -> module_golden_index.ticker_html + review_pages 注入
2 删两组件          -> 机器数据核对层(machfold) / 本页阅读(page-map) 概览不产
3 obs卡缺股票名      -> review_publish v4.4 去噪CSS 对概览放行 .obs-nm/.obs-lab
4 拐点预警对齐黄金   -> 段二补 总审环境加权依据 点评(黄金卡形态)
5 来源审计折叠下线   -> 概览不产 audit-fold; 证据留痕不动
额外: 概览h1 机器串「index路·20260922」-> 总审「一句话」; hero 情绪档 pill 取温度档
"""
from pathlib import Path
import io, sys

root = Path('D:/股票数据/市场数据')
edits = []

def patch(path, old, new, count=1, label=''):
    p = root / path
    t = p.read_text(encoding='utf-8')
    n = t.count(old)
    assert n == count, f'{label}: 期望{count}处, 实测{n}处 -> {path}'
    t = t.replace(old, new)
    p.write_text(t, encoding='utf-8', newline='\n')
    edits.append(f'{path} :: {label}')

# ============ A. module_golden_index.py ============
G = 'module_golden_index.py'

patch(G,
'''def turning_block(model, d):
    """段二: 拐点预警 = 三窗触发器机器块(黄金版同套 markup) + 总审环境加权依据。"""
    comp = _comp(model, 'IDXLEAD')
    ptr = _by_pointer(model)
    lead = comp['html'] if comp else ''
    para = ptr.get('/环境加权依据') or ''
    body = '<div class="card">' + (lead or ('<p class="mut">三窗触发器当日缺失：' + DASH + '</p>'))
    if para:
        body += '<p style="margin:8px 0 0">' + _esc(para) + '</p>'
    body += '</div>'
    return _anchored(comp, body)''',
'''def turning_block(model, d, env_basis=''):
    """段二: 拐点预警 = 三窗触发器机器块(黄金版同套 markup) + 总审环境加权依据点评。

    2026-09-23 用户指正: 与黄金版不一致(缺点评段)。点评真源 = 总审 JSON「环境加权依据」
    (由 review_pages 传入; 该字段在概览 claim 导入时被有意跳过, 故这里显式取用)。
    总审未产出 -> 如实写 `—`, 不代写、不美化。"""
    comp = _comp(model, 'IDXLEAD')
    lead = comp['html'] if comp else ''
    body = '<div class="card">' + (lead or ('<p class="mut">三窗触发器当日缺失：' + DASH + '</p>'))
    note = (env_basis or '').strip()
    body += ('<p style="margin:8px 0 0">' + _esc(note) + '</p>' if note
             else '<p class="mut" style="margin:8px 0 0">环境加权依据（总审）：' + DASH + '</p>')
    body += '</div>'
    return _anchored(comp, body)''',
1, 'turning_block 黄金形态+点评')

patch(G,
'''def build(model, d):
    """返回 {section_id: 黄金骨架 html}; 只覆盖黄金四段, 能力进化两段由部署后处理注入。"""
    out = {
        'recommendations': recommendations_block(model, d),
        'turning': turning_block(model, d),''',
'''def build(model, d, env_basis=''):
    """返回 {section_id: 黄金骨架 html}; 只覆盖黄金四段, 能力进化两段由部署后处理注入。"""
    out = {
        'recommendations': recommendations_block(model, d),
        'turning': turning_block(model, d, env_basis),''',
1, 'build 透传 env_basis')

patch(G,
'''def contract_sections():''',
'''def ticker_html(model, d):
    """概览走马灯 = 黄金版同款条带(kpi 真源 + 三窗机器块 + 五路裁决档位)。

    铁律: 每一条都来自当日已留档读数, 取不到的项直接不出条(不写 `—` 占位、不编造)。
    """
    kp = list(model.get('kpis') or [])

    def slot(i):
        return kp[i] if len(kp) > i else {}

    def sub_of(k, pat):
        m = re.search(pat, _t(k.get('sub') or ''))
        return m.group(1) if m else ''

    facts = []
    vol = slot(1)
    if vol.get('display'):
        trend = sub_of(vol, r'(连\\d+日[^（(·,，]*)')
        note = ' · '.join(x for x in (_t(vol.get('chip') or ''), trend) if x)
        facts.append('量能 <b class="a">%s万亿</b>%s'
                     % (_esc(vol['display']), '(%s)' % _esc(note) if note else ''))
    zt = slot(2)
    if zt.get('display'):
        m = re.match(r'^(\\d+)/(\\d+)$', _t(zt['display']))
        if m:
            facts.append('涨停 <b class="u">%s</b> / 跌停 <b class="d">%s</b>' % (m.group(1), m.group(2)))
        zb = sub_of(zt, r'(炸板\\d+只·炸板率[\\d.]+%)')
        if zb:
            facts.append('炸板 <b>%s</b>' % _esc(zb.replace('炸板', '', 1).replace('炸板率', '率', 1)))
    ladder = _t((_comp(model, 'IDXTEMP') or {}).get('html') or '')
    m = re.search(r'(\\d+)板(\\d+)只', ladder)
    if m:
        facts.append('最高 <b class="u">%s板</b>' % m.group(1))
    jj = slot(3)
    if jj.get('display'):
        yest = sub_of(jj, r'昨([\\d.]+%)')
        facts.append('1进2率 <b class="a">%s</b>%s'
                     % (_esc(_t(jj['display'])), '(昨%s→)' % _esc(yest) if yest else ''))
    temp = slot(0)
    if temp.get('display'):
        chip = (_t(temp.get('chip') or '').split(' ') or [''])[0]
        facts.append('情绪温度 <b class="a">%s</b>%s'
                     % (_esc(_t(temp['display'])), '(%s)' % _esc(chip) if chip else ''))
    lead = (_comp(model, 'IDXLEAD') or {}).get('html') or ''
    label = '❄冰点进攻窗'
    m = re.search(r'>([❄☢♨][^<]{0,8}·(?:触发|亮))<', lead)
    if m:
        facts.append('三窗 <b class="a">%s</b>' % _esc(m.group(1)))
    else:
        states = re.findall(r'>([❄☢♨][^<]*·[灭—])<', lead)
        if states:
            facts.append('三窗 <b class="d">%s</b>' % _esc(' '.join(states)))
    ptr = _by_pointer(model)
    routes = []
    for i, (_code, cn, _name, _href) in enumerate(ROUTE_META):
        grade = ptr.get('/五路裁决/%d/档位' % i)
        conf = ptr.get('/五路裁决/%d/置信度' % i)
        if grade:
            routes.append('%s%s%s' % (cn[1:], _esc(str(grade)), _esc(str(conf or ''))))
    if routes:
        facts.append('五路 <b class="a">%s</b>' % ' · '.join(routes))
    return ''.join('<span>' + f + '</span>' for f in facts)


def contract_sections():''',
1, 'ticker_html 新增')

# ============ B. review_publish.py (v4.4 去噪CSS 概览放行票名) ============
P = 'review_publish.py'
patch(P,
'''    css = ('.claim-head:not(.cgrp-head),.citem .citem-tag,.claim-proof .proof-label,'
           '.obs-head .obs-nm,.obs-watch>.obs-lab{display:none}'
           '.claim-anchor-bank,.claim-anchor-text,.audit-anchor-bank{display:none}')''',
'''    css = ('.claim-head:not(.cgrp-head),.citem .citem-tag,.claim-proof .proof-label,'
           '.obs-head .obs-nm,.obs-watch>.obs-lab{display:none}'
           '.claim-anchor-bank,.claim-anchor-text,.audit-anchor-bank{display:none}')
    # 概览页(黄金骨架)例外: 黄金版 .obs 卡头部本来就是「名称+代码」与「身位」标签,
    # 这两条去噪规则会把票名吃掉(2026-09-23 用户指正「图2没有对应的股票名称」)。
    # 只对 index 放行, 其余路去噪口径不变。
    css_index = ('.claim-head:not(.cgrp-head),.citem .citem-tag,.claim-proof .proof-label'
                 '{display:none}'
                 '.claim-anchor-bank,.claim-anchor-text,.audit-anchor-bank{display:none}')''',
1, 'css_index 定义')

patch(P,
'''            if marker not in page:
                page = page.replace('</head>', '<style ' + marker + '>' + css + '</style></head>', 1)''',
'''            if marker not in page:
                _css = css_index if route == 'index' else css
                page = page.replace('</head>', '<style ' + marker + '>' + _css + '</style></head>', 1)''',
1, 'css 按路选择')

print('\n'.join('OK  ' + e for e in edits))
