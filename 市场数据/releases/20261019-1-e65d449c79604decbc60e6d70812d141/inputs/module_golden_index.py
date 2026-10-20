# -*- coding: utf-8 -*-
"""概览页黄金骨架渲染(唯一真源) —— 2026-09-23 用户拍板: 概览页回归黄金组件体系。

冻结段序(不可由 LLM/总审正文决定增删与顺序):
  一 明日核心观察点       = 跨路筛选 Top5, 用黄金 `.obs` 组件形态逐票渲染
  二 拐点预警 · 命门温度背离 = 三窗触发器(A档) 机器块
  三 五路看牌             = 黄金 `.routes` + 5 条 `.rt` 路读数行
  四 总裁决 · 自主进化      = 六账本(引擎) + 跨路裁决 + 次日验证点
  五/六 自主拓展/认知迭代 · 能力进化 = 部署后处理由 能力进化模块.py 注入(本模块不产)

数据真源 = 页面模型(model)内的机器组件与 claim:
  - CROSSPICK 组件 html: 跨路荐票.py 当日真源(五路候选去重→共振→路内位置→执行期望)
  - IDXLEAD 组件 html: 情绪先行指标.py 三窗触发器(黄金版同套 markup)
  - ENGINEBOOKS 组件 html: 模拟盘引擎净值(数字只出自引擎)
  - claims 指针 /五路裁决/N/* 与 /总裁决/*: 总审当日裁决原文
不读任何额外文件 → 冷冻候选发布(冻结 inputs)与现站渲染同源; 拿不到一律 `—`, 零编造。
"""

import re
from html import escape as _esc
from html import unescape as _unesc

DASH = '—'

# 路序/中文名/目标页, 与黄金版五路看牌同序
ROUTE_META = (
    ('auction', '①竞价', '竞价·时机', 'auction.html'),
    ('lhb', '②席位', '龙虎榜·席位', 'lhb.html'),
    ('theme', '③题材', '题材·主线', 'theme.html'),
    ('logic', '④产逻', '产业·逻辑', 'logic.html'),
    ('limitup', '⑤质量', '涨停·质量', 'limitup.html'),
)
ROUTE_CN = {'auction': '①竞价', 'lhb': '②席位', 'theme': '③题材',
            'logic': '④产逻', 'limitup': '⑤质量'}

# 档位→徽章色(与黄金版 s-ok/s-mid/s-weak 同族)
GRADE_CLS = {'A': 's-ok', 'B': 's-mid', 'C': 's-weak'}

# 段题与副题(冻结): 段序号由 review_pages 统一渲染, 这里只给标题与 hint
SECTION_META = {
    'recommendations': ('明日核心观察点',
                        '跨路筛选: 五路候选去重→共振路数优先→路内位置分→执行期望取前5; 给概率不给指令'),
    'turning': ('拐点预警 · 命门温度背离',
                '三窗触发器(A档)与温度/接力背离; 点进周期页看完整闭环'),
    'routes': ('五路看牌', '五路命门今日读数; 点进各页看完整闭环'),
    'verdict': ('总裁决 · 自主进化', '六账本净值(引擎)+跨路裁决+次日验证点'),
}
GOLDEN_SECTION_IDS = ('recommendations', 'turning', 'routes', 'verdict')
# 段二按黄金版版式并入段一 .rowC 右栏 → 不单独成段(段标记仍在页内, C15 段序不变)。
ABSORBED_SECTIONS = ('turning',)


def _t(html):
    """去标签取纯文本(用于把机器组件里的读数搬进黄金组件槽位)。"""
    txt = re.sub(r'<br\s*/?>', ' ', str(html or ''))
    txt = re.sub(r'<[^>]+>', '', txt)
    txt = _unesc(txt)
    return re.sub(r'\s+', ' ', txt).strip()


def _clip(text, limit):
    text = (text or '').strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for mark in ('；', '。', ';', ' '):
        pos = cut.rfind(mark)
        if pos >= limit * 0.6:
            return cut[:pos] + '…'
    return cut + '…'


def _comp(model, cid):
    for comp in model.get('components', []):
        if comp.get('id') == cid and comp.get('status') == 'ok' and comp.get('html'):
            return comp
    return None


def _anchored(comp, inner):
    """把黄金组件内容包在机器组件锚区里(锚点必须恰好出现一次, 门禁/哨兵依赖)。"""
    if not comp:
        return inner
    anchors = comp.get('anchors') or []
    return ('<div id="component-' + _esc(comp['id']) + '">'
            + ''.join('<!--' + a + '-->' for a in anchors)
            + inner
            + ''.join('<!--/' + a + '-->' for a in reversed(anchors)) + '</div>')


def _by_pointer(model):
    out = {}
    for c in model.get('claims', []):
        p = c.get('source_pointer') or ''
        if p and p not in out:
            out[p] = c.get('text') or ''
    return out


def _crosspick_rows(html):
    """从跨路荐票卡表里取出每票真源字段(卡片由 跨路荐票.py 直出, 结构稳定)。"""
    rows = []
    for tr in re.findall(r'<tr>(.*?)</tr>', html or '', re.S):
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)
        if len(cells) < 6 or not re.match(r'^\s*\d+\s*$', _t(cells[0])):
            continue
        head = cells[1]
        name = _t(re.search(r'<b[^>]*>(.*?)</b>', head, re.S).group(1)) if '<b' in head else _t(head)
        code_m = re.search(r'<span class="mut">(\d{6})</span>', head)
        conf = cells[2]
        conf_b = _t(re.search(r'<b[^>]*>(.*?)</b>', conf, re.S).group(1)) if '<b' in conf else ''
        pos_m = re.search(r'位置分\s*([0-9.]+)', _t(conf))
        src_html = cells[3]
        src_txt = _t(src_html)
        sources = [ROUTE_CN[k] for k, tag in ROUTE_CN.items() if tag in src_txt]
        rows.append({
            '名称': name,
            '代码': code_m.group(1) if code_m else '',
            '共振': conf_b or DASH,
            '位置分': pos_m.group(1) if pos_m else DASH,
            '来源指标': src_txt,
            '来源路': sources,
            '执行口径': _t(cells[4]),
            '题材归位': _t(cells[5]) or DASH,
        })
    return rows


_AUC_HEAD = re.compile(r'①竞价\s*#?\s*([0-9]+)?\s*([^②③④⑤]*)')


def _obs_card(row, d):
    d_show = d[:4] + '-' + d[4:6] + '-' + d[6:] if len(d) == 8 else d
    head = ('<div class="obs-head"><span class="obs-nm">' + _esc(row['名称'])
            + (' <span class="mut">' + _esc(row['代码']) + '</span>' if row['代码'] else '')
            + '</span><span class="obs-pos tag">' + _esc(str(row['共振'])) + '路共振 · '
            + _esc(row['题材归位']) + '</span></div>')
    watch = ('<div class="obs-watch"><span class="obs-lab">身位</span>位置分'
             + _esc(str(row['位置分'])) + '；' + _esc(_clip(row['来源指标'], 300)) + '</div>')
    rec = ('<div class="obs-rec"><span class="obs-lab2">来源</span>'
           + _esc('、'.join(row['来源路']) if row['来源路'] else DASH)
           + '；执行口径(各路历史桶, 非个股预言)：' + _esc(_clip(row['执行口径'], 200)) + '</div>')
    auc_m = _AUC_HEAD.search(row['来源指标'] or '')
    auc_detail = _clip(_t(auc_m.group(2)), 90) if auc_m else ''
    auc_bucket = ''
    bk = re.search(r'①竞价\s*([^②③④⑤]*)', row['执行口径'] or '')
    if bk:
        auc_bucket = _t(bk.group(1))
    if auc_detail or auc_bucket:
        jj = ('<span class="jjtag">今日竞价池 ' + _esc(d_show) + '</span>'
              + _esc(auc_detail or DASH) + ' — <b class="s-mid">执行桶:'
              + _esc(_clip(auc_bucket, 80) or DASH) + '</b>')
    else:
        jj = ('<span class="jjtag">今日竞价池 ' + _esc(d_show) + '</span>' + DASH
              + '（该票当日不在竞价路候选内）')
    return ('<div class="obs">' + head + watch + rec
            + '<div class="obs-jj">' + jj + '</div></div>')


def recommendations_block(model, d, env_basis=''):
    """段一: 明日核心观察点 = 跨路筛选 Top5(.obs 卡) + 右栏嵌段二 拐点预警。

    黄金版版式: <div class="rowC"><div>主栏</div><aside class="rail">拐点卡</aside></div>。
    段二段标记(<!--GOLDEN-INDEX:turning-->)随卡在右栏内, 保证哨兵C15段序核对仍成立。
    """
    comp = _comp(model, 'CROSSPICK')
    body = ''
    if comp:
        hint = re.search(r'<div class="hint">(.*?)</div>', comp['html'], re.S)
        if hint:
            body += '<div class="hint">' + hint.group(1) + '</div>'
        rows = _crosspick_rows(comp['html'])
        if rows:
            body += ''.join(_obs_card(r, d) for r in rows)
        else:
            body += ('<div class="card"><b>当日跨路荐票卡解析失败</b><p class="mut">'
                     '组件存在但未取到候选行, 如实标 ' + DASH + ', 不推测。</p></div>')
    else:
        body += ('<div class="card"><b>当日跨路荐票未产出</b><p class="mut">五路候选跨路筛选卡缺失: '
                 + DASH + '</p></div>')
    rail = ('<aside class="rail"><!--GOLDEN-INDEX:turning-->'
            + turning_block(model, d, env_basis) + '<!--/GOLDEN-INDEX:turning--></aside>')
    return _anchored(comp, '<div class="rowC"><div>' + body + '</div>' + rail + '</div>')


def turning_block(model, d, env_basis=''):
    """段二: 拐点预警 = 三窗触发器机器块(黄金版同套 markup) + 总审环境加权依据点评。

    版式(2026-09-23 用户指正 图3「和黄金版不一样」): 与黄金版一致地嵌在段一
    .rowC 的右栏(<aside class="rail">)内, 卡内自带 15px 小标题——所以本段不再
    单独成段(见 ABSORBED_SECTIONS), 段标记随卡一起放在右栏里。

    2026-09-23 用户指正: 与黄金版不一致(缺点评段)。点评真源 = 总审 JSON「环境加权依据」
    (由 review_pages 传入; 该字段在概览 claim 导入时被有意跳过, 故这里显式取用)。
    总审未产出 -> 如实写 `—`, 不代写、不美化。"""
    comp = _comp(model, 'IDXLEAD')
    lead = comp['html'] if comp else ''
    body = ('<div class="card"><h2 style="margin:0 0 2px;font-size:15px">'
            '二 拐点预警 · 命门温度背离</h2>'
            + (lead or ('<p class="mut">三窗触发器当日缺失：' + DASH + '</p>')))
    note = (env_basis or '').strip()
    body += ('<p style="margin:8px 0 0">' + _esc(note) + '</p>' if note
             else '<p class="mut" style="margin:8px 0 0">环境加权依据（总审）：' + DASH + '</p>')
    body += '</div>'
    return _anchored(comp, body)


def routes_block(model, d):
    """段三: 五路看牌 = 黄金 .routes + 每路一条 .rt 行(档位/置信度/裁决/荐票核验)。"""
    ptr = _by_pointer(model)
    rows = ''
    for i, (code, cn, name, href) in enumerate(ROUTE_META):
        grade = ptr.get('/五路裁决/%d/档位' % i) or DASH
        conf = ptr.get('/五路裁决/%d/置信度' % i) or DASH
        reason = ptr.get('/五路裁决/%d/裁决理由' % i) or ''
        verdict = ptr.get('/五路裁决/%d/裁决' % i) or ''
        picks = ptr.get('/五路裁决/%d/荐票核验' % i) or ''
        detail = _clip(reason, 130)
        tail = ' · '.join(x for x in ('裁决' + verdict if verdict else '', picks) if x)
        rows += ('<a class="rt" href="' + _esc(href) + '"><span class="rtn">'
                 + '%02d / 第%s路' % (i + 1, '一二三四五'[i]) + '</span><span class="rtm">' + _esc(name)
                 + '</span><b class="rtt ' + GRADE_CLS.get(grade, 's-mid') + '">' + _esc(grade)
                 + '档 · ' + _esc(str(conf)) + '</b><span class="rtd">' + _esc(detail or DASH)
                 + ('<br>' + _esc(tail) if tail else '') + '</span></a>')
    return '<div class="routes">' + rows + '</div>'


def verdict_block(model, d):
    """段四: 总裁决 = 六账本(引擎) + 跨路裁决卡(总审原文) + 次日验证点。"""
    books = _comp(model, 'ENGINEBOOKS')
    if books:
        body = _anchored(books, books['html'])
    else:
        body = '<div class="card"><b>六账本</b><p class="mut">当日引擎净值缺失：' + DASH + '</p></div>'
    ptr = _by_pointer(model)
    grade = ptr.get('/总裁决/档位') or DASH
    conf = ptr.get('/总裁决/置信度') or DASH
    conclusion = ptr.get('/总裁决/结论') or ''
    split = ptr.get('/总裁决/分歧裁决') or ''
    checks = [v for k, v in ptr.items() if re.match(r'^/总裁决/次日验证点/\d+$', k)]
    checks = [_clip(x, 220) for x in checks]
    card = ('<div class="card"><b>总裁决 · <span class="' + GRADE_CLS.get(grade, 's-mid') + '">'
            + _esc(grade) + '档</span> <span class="hint">置信度 ' + _esc(str(conf))
            + '/100(评分,未校准)</span></b>')
    card += '<p style="margin:6px 0 0">' + _esc(conclusion)
    if conclusion.endswith('。'):
        card = card[:-1]  # 结论已自带句号时不重复
    card += '</p>'
    if split:
        card += '<p class="mut" style="margin:6px 0 0">分歧裁决：' + _esc(split) + '</p>'
    if checks:
        card += ('<b style="display:block;margin-top:8px">次日验证点(明晚校准, 不美化)</b><ul>'
                 + ''.join('<li>' + _esc(x) + '</li>' for x in checks) + '</ul>')
    card += '</div>'
    return body + card


def build(model, d, env_basis=''):
    """返回 {section_id: 黄金骨架 html}; 只覆盖黄金四段, 能力进化两段由部署后处理注入。

    ABSORBED_SECTIONS 里的段不单独返回(其内容与段标记已在其它段内), 调用方需跳过该段。
    """
    out = {
        'recommendations': recommendations_block(model, d, env_basis),
        'routes': routes_block(model, d),
        'verdict': verdict_block(model, d),
    }
    # 段标记: 哨兵C15/契约自检/回归测试靠它确认"黄金骨架在场且段序不变"。
    return {k: '<!--GOLDEN-INDEX:%s-->%s<!--/GOLDEN-INDEX:%s-->' % (k, v, k) for k, v in out.items()}


def ticker_html(model, d):
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
        trend = sub_of(vol, r'(连\d+日[^（(·,，]*)')
        note = ' · '.join(x for x in (_t(vol.get('chip') or ''), trend) if x)
        facts.append('量能 <b class="a">%s万亿</b>%s'
                     % (_esc(vol['display']), '(%s)' % _esc(note) if note else ''))
    zt = slot(2)
    if zt.get('display'):
        m = re.match(r'^(\d+)/(\d+)$', _t(zt['display']))
        if m:
            facts.append('涨停 <b class="u">%s</b> / 跌停 <b class="d">%s</b>' % (m.group(1), m.group(2)))
        zb = sub_of(zt, r'(炸板\d+只·炸板率[\d.]+%)')
        if zb:
            facts.append('炸板 <b>%s</b>' % _esc(zb.replace('炸板', '', 1).replace('炸板率', '率', 1)))
    ladder = _t((_comp(model, 'IDXTEMP') or {}).get('html') or '')
    m = re.search(r'(\d+)板(\d+)只', ladder)
    if m:
        facts.append('最高 <b class="u">%s板</b>' % m.group(1))
    jj = slot(3)
    if jj.get('display'):
        yest = sub_of(jj, r'昨([\d.]+%)')
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


def contract_sections():
    """契约 sections 用的 (id, title) 列表 —— 骨架冻结, 与 SECTION_META 同源。"""
    return [{'id': sid, 'title': SECTION_META[sid][0]} for sid in GOLDEN_SECTION_IDS]
