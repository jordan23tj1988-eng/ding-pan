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


def recommendations_block(model, d):
    """段一: 明日核心观察点 = 跨路筛选 Top5, 黄金 .obs 形态。"""
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
    return _anchored(comp, body)


def turning_block(model, d):
    """段二: 拐点预警 = 三窗触发器机器块(黄金版同套 markup) + 总审环境加权依据。"""
    comp = _comp(model, 'IDXLEAD')
    ptr = _by_pointer(model)
    lead = comp['html'] if comp else ''
    para = ptr.get('/环境加权依据') or ''
    body = '<div class="card">' + (lead or ('<p class="mut">三窗触发器当日缺失：' + DASH + '</p>'))
    if para:
        body += '<p style="margin:8px 0 0">' + _esc(para) + '</p>'
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


def build(model, d):
    """返回 {section_id: 黄金骨架 html}; 只覆盖黄金四段, 能力进化两段由部署后处理注入。"""
    out = {
        'recommendations': recommendations_block(model, d),
        'turning': turning_block(model, d),
        'routes': routes_block(model, d),
        'verdict': verdict_block(model, d),
    }
    # 段标记: 哨兵C15/契约自检/回归测试靠它确认"黄金骨架在场且段序不变"。
    return {k: '<!--GOLDEN-INDEX:%s-->%s<!--/GOLDEN-INDEX:%s-->' % (k, v, k) for k, v in out.items()}


def contract_sections():
    """契约 sections 用的 (id, title) 列表 —— 骨架冻结, 与 SECTION_META 同源。"""
    return [{'id': sid, 'title': SECTION_META[sid][0]} for sid in GOLDEN_SECTION_IDS]
