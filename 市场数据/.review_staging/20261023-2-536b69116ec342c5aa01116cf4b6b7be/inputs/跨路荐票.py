# -*- coding: utf-8 -*-
"""跨路荐票.py {d} —— 概览「Top5 荐票卡」(跨路筛选, 2026-09-11 用户拍板)。

口径(用户拍板=跨路共识优先):
  候选池 = 五路当日候选并集去重 —— ①竞价池(竞价池发出_{d}.json) / ②席位Top5(席位荐票_{d}.json)
           / ③题材荐票(题材荐票_{d}.json) / ④产逻荐票(逻辑荐票_{d}.json 或 五路判断_{d}/logic.json)
           / ⑤涨停质量Top5(涨停质量荐票_{d}.json)
  排序键 = 共振路数(被几路同时选中)降序 → 路内位置分 Σ(6-路内排名) 降序 → 执行期望降序 → 代码升序 → 取5。
  每行标注来源路与该路核心指标(内容贴合每一路的主题与能力)。

★零编造: 每格都回读当日 _学习 产物; 缺失/空仓如实写 — 或「空仓」; 不补数、不凑票、不造票。
★非买入指令: 本卡是跨路筛选后的可操作/可观察清单; 执行口径=各路历史桶均值/滚动值, 非个股预言。
★产物: _学习/跨路荐票_{d}.json(候选池+排名键可审计) + _学习/跨路荐票卡_{d}.html(概览页组件)。
"""
import os, sys, json, glob, re

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')

ROUTE_TAG = {'auction': '①竞价', 'lhb': '②席位', 'theme': '③题材', 'logic': '④产逻', 'limitup': '⑤质量'}
ROUTE_NAME = {'auction': '竞价池', 'lhb': '席位路Top5', 'theme': '题材路荐票', 'logic': '产逻路荐票', 'limitup': '质量路Top5'}


def load(name):
    p = name if os.path.isabs(name) else os.path.join(L, name)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8-sig'))
    except Exception as exc:
        print('  [warn] 读取失败 %s: %s' % (p, exc))
        return None


def _code(x):
    c = str(x.get('代码') or '').strip()
    return c.zfill(6) if c else ''


def collect(d):
    """五路候选(按各路自身排序) → {代码: {名称, sources: {route: {...}}}} 和 来源清单文本。"""
    cand = {}
    inv = []

    def add(route, rank, code, name, metric, basis, exe, expect=None):
        if not code:
            return
        e = cand.setdefault(code, dict(代码=code, 名称=name or '—', sources={}))
        if not e.get('名称') or e['名称'] == '—':
            e['名称'] = name or '—'
        e['sources'][route] = dict(排名=rank, 指标=metric, 依据=basis, 执行=exe, 期望值=expect)

    # ①竞价池(池顺序=当日池序) + 竞价分/情景(竞价评分_{d}.json)
    pool = load('竞价池发出_%s.json' % d) or {}
    score = load('竞价评分_%s.json' % d) or {}
    smap = {str(x.get('代码', '')).zfill(6): x for x in (score.get('明细') or [])}
    plist = pool.get('池') or []
    for i, x in enumerate(plist, 1):
        c = _code(x)
        s = smap.get(c) or {}
        metric = ('竞价分%s' % s['竞价分']) if s.get('竞价分') is not None else '—'
        basis = ' · '.join([v for v in [str(x.get('信号') or ''), ('首封%s' % x['首封']) if x.get('首封') else ''] if v]) or '—'
        scen = (s.get('情景') or {}).get('高开0~5') or {}
        exe = ('高开0~5%% %+.2f%%/%.0f%%(n=%s)' % (scen['均涨'], scen['胜率'], scen.get('n'))) if scen.get('均涨') is not None else '—'
        add('auction', i, c, x.get('名称'), metric, basis, exe, scen.get('均涨'))
    inv.append(('auction', len(plist)))

    # ②席位路 Top5
    seat = load('席位荐票_%s.json' % d) or {}
    slist = seat.get('top5') or []
    for i, x in enumerate(slist, 1):
        seats = x.get('席位') or []
        s0 = seats[0] if seats else {}
        basis = '[%s]%s 净买%s万' % (s0.get('档', '?'), str(s0.get('名', ''))[:12], s0.get('净额万')) if s0 else '—'
        if len(seats) > 1:
            basis += ' +%d席位共振' % (len(seats) - 1)
        exe = ('滚执1 %s(n=%s)' % (s0['滚动执1'], s0.get('样本'))) if s0.get('滚动执1') else '—'
        try:
            expect = float(str(s0.get('滚动执1', '')).split('/')[1].rstrip('%'))
        except Exception:
            expect = None
        add('lhb', i, _code(x), x.get('名称'),
            '综合分%s·共振%s' % (x.get('综合分'), x.get('共振')), basis, exe, expect)
    inv.append(('lhb', len(slist)))

    # ③题材路(标的数组; 类型∈荐票/观察)
    th = load('题材荐票_%s.json' % d) or {}
    tlist = (th.get('标的') if isinstance(th, dict) else th) or []  # 容错: 发出版可能是 list 或 dict
    for i, x in enumerate(tlist, 1):
        basis = ' · '.join([v for v in [str(x.get('身位') or ''), str(x.get('题材线') or ''), str(x.get('理由') or '')[:70]] if v]) or '—'
        add('theme', i, _code(x), x.get('名称'), str(x.get('类型') or '—'), basis, '—')
    inv.append(('theme', len(tlist)))

    # ④产逻路(逻辑荐票_{d}.json 优先; 退到 五路判断_{d}/logic.json 的 荐票.标的)
    lg = load('逻辑荐票_%s.json' % d)
    llist = (lg or {}).get('荐票') or []
    if not llist:
        alt = load(os.path.join('五路判断_%s' % d, 'logic.json')) or {}
        llist = ((alt.get('荐票') or {}).get('标的')) or []
    for i, x in enumerate(llist, 1):
        chain = ' · '.join([v for v in [str(x.get('链条') or ''), str(x.get('环节') or '')] if v])
        basis = ' · '.join([v for v in [chain, str(x.get('理由') or '')[:70]] if v]) or '—'
        add('logic', i, _code(x), x.get('名称'), str(x.get('类型') or '—'), basis, '—')
    inv.append(('logic', len(llist)))

    # ⑤涨停质量路 Top5
    q = load('涨停质量荐票_%s.json' % d) or {}
    qlist = q.get('top5') or []
    for i, x in enumerate(qlist, 1):
        hits = x.get('命中规则') or []
        basis = '; '.join(hits) if hits else ('主导: %s' % str(x.get('主导因子') or '—').split('|')[0].strip())
        exe = '执1 %s%%/%+.2f%% · 执2 %s%%/%+.2f%%' % (x.get('预测执1胜率'), x.get('预测执1均涨') or 0.0,
                                                     x.get('预测执2胜率'), x.get('预测执2均涨') or 0.0)
        add('limitup', i, _code(x), x.get('名称'),
            '抓龙率%s%%·分%s' % (x.get('抓龙率'), x.get('质量分')), basis, exe, x.get('预测执2均涨'))
    inv.append(('limitup', len(qlist)))

    # ⑥补源: 交易计划_{路}#buys（= 总审评审所用的正式荐票，与筛选清单同源）
    #   根因: 上面五路读的是各路『荐票榜/Top5』，总审评审读的是『交易计划#buys』，两者不同源；
    #   总审留用但没上荐票榜的票，本卡原先会显示「无跨路来源」。此处只补缺失来源，
    #   同路已有荐票榜来源时保留原来源（不改排名、不重复计数）。
    for r in ('auction', 'lhb', 'theme', 'logic', 'limitup'):
        plan = load('交易计划_%s_%s.json' % (r, d)) or {}
        for i, x in enumerate(plan.get('buys') or [], 1):
            code = _code_from_text(x.get('代码')) or _code(x)
            if not code or (code in cand and r in cand[code]['sources']):
                continue
            w = x.get('权重%')
            if w is None:
                w = x.get('权重')
            gate = str(x.get('buy_gate') or '')
            add(r, 6 + i, code, x.get('名称'),
                '正式荐票%s%%' % (w if w is not None else '—'),
                ('buy_gate: ' + gate[:80]) if gate else '经总审采纳的正式荐票(交易计划#buys)', '—')
            if code in cand and r in cand[code]['sources']:
                cand[code]['sources'][r]['来自计划'] = True
    return cand, inv


def expectation(entry):
    """执行期望(排序第三键): 取各路可核对的均涨数值(竞价=情景桶均涨/席位=滚执1均涨/质量=执2均涨), 无量值→None(排尾)。"""
    vals = [float(s['期望值']) for s in entry['sources'].values() if s.get('期望值') is not None]
    return max(vals) if vals else None


def _code_from_text(s):
    """'002474 榕基软件' → '002474'（总审筛选清单的票字段是人读串）。"""
    m = re.search(r'(\d{6})', str(s or ''))
    return m.group(1) if m else ''


def master_gate(d):
    """★总审筛选清单门禁(唯一真源): 只让总审『留』的票进榜，『剔』的不进榜。
    返回 (gate, info)。gate=None 表示无门禁（总审缺失/无筛选清单），此时不过滤但显式登记，
    不得把「核不了」说成「通过了」。留数=0 属合法空仓，不递补、不凑票。"""
    a = load('总审_%s.json' % d) or {}
    sc = a.get('筛选清单') or {}
    gate = {}
    for r in (sc.get('明细') or []):
        code = _code_from_text(r.get('票'))
        if not code:
            continue
        gate[code] = {'名称': re.sub(r'\d{6}', '', str(r.get('票') or '')).strip() or code,
                      '裁决': r.get('留/剔') or '—',
                      '建议权重%': r.get('建议权重%'),
                      '原因': r.get('原因') or ''}
    info = {'来源': '总审_%s.json#筛选清单' % d,
            '并集数': sc.get('并集数'), '留数': sc.get('留数'), '剔数': sc.get('剔数'),
            '留用合计权重%': sc.get('留用合计权重%'),
            '筛选说明': str(sc.get('筛选说明') or '')[:200]}
    if not gate:
        info['状态'] = 'unavailable:总审无筛选清单'
        return None, info
    info['状态'] = 'applied'
    return gate, info


def build(d):
    global load_cache
    cand, inv = collect(d)
    q = load('涨停质量荐票_%s.json' % d) or {}
    load_cache = {'limitup': {_code(x): x for x in (q.get('top5') or [])}}
    for c, e in cand.items():
        e['共振'] = len(e['sources'])
        e['位置分'] = sum(max(0, 6 - s['排名']) for s in e['sources'].values())
        e['执行期望'] = expectation(e)
    gate, ginfo = master_gate(d)
    for c, e in cand.items():
        g = (gate or {}).get(c)
        e['总审裁决'] = (g or {}).get('裁决') or ('未列入' if gate is not None else '—')
    rows = sorted(cand.values(), key=lambda x: (-x['共振'], -x['位置分'],
                                                -(x['执行期望'] if x['执行期望'] is not None else -9e9), x['代码']))
    if gate is None:
        kept = rows
    else:
        # ★主名单 = 总审『留』（唯一真源）；跨路共识只作排序键，不得自我增删名单。
        #   这里改的根因：跨路候选池来自各路『荐票Top5』，与总审评审用的『交易计划#buys』不同源，
        #   若只做交集过滤，总审留用但不在荐票Top5的票会被静默丢掉（20261023 实测丢 3 只）。
        by_code = {x['代码']: x for x in rows}
        kept = []
        for code, g in gate.items():
            if g['裁决'] != '留':
                continue
            src = by_code.get(code)
            if src is None:
                kept.append({'代码': code, '名称': g.get('名称') or code, 'sources': {},
                             '共振': 0, '位置分': 0, '执行期望': None,
                             '总审裁决': '留', '总审建议权重%': g.get('建议权重%'),
                             '缺跨路来源': True})
            else:
                x = dict(src)
                x['总审建议权重%'] = g.get('建议权重%')
                kept.append(x)
        kept.sort(key=lambda x: (-x['共振'],
                                 -(x['总审建议权重%'] if x.get('总审建议权重%') is not None else -1),
                                 -x['位置分'],
                                 -(x['执行期望'] if x['执行期望'] is not None else -9e9), x['代码']))
    ginfo['被剔出榜'] = [
        {'代码': x['代码'], '名称': x['名称'], '原权重%': gate[x['代码']].get('建议权重%'),
         '原因': (gate[x['代码']].get('原因') or '')[:180]}
        for x in rows if gate is not None and x['总审裁决'] == '剔']
    ginfo['未列入候选池'] = [c for c in (gate or {}) if c not in cand]
    return kept[:5], rows, inv, ginfo


def render(d, top5, allrows, inv, ginfo=None):
    import html as H

    temp = load('_市场温度表.json') or {}
    t = temp.get(d) or {}
    audit = load('总审_%s.json' % d) or {}
    verdict = audit.get('总裁决') or {}

    # 环境行(全部回读当日真源, 缺失不编)
    env_bits = []
    if t.get('温度') is not None:
        env_bits.append('温度%s(%s)' % (t['温度'], t.get('温度档') or '—'))
    if t.get('涨停数') is not None:
        env_bits.append('涨停%s·炸板%s·跌停%s' % (t.get('涨停数'), t.get('炸板数'), t.get('跌停数')))
    if verdict.get('档位'):
        env_bits.append('总裁决%s档: %s' % (verdict['档位'], str(verdict.get('结论') or '')[:46]))
    env = '环境: ' + ' · '.join(env_bits) if env_bits else '环境: —'

    src_bits = []
    for r, n in inv:
        if r in ('theme', 'logic') and n == 0:
            j = load(('题材荐票_%s.json' % d) if r == 'theme' else ('逻辑荐票_%s.json' % d))
            state = '空仓' if j is not None else '无当日产出'
            if r == 'logic' and j is None and load(os.path.join('五路判断_%s' % d, 'logic.json')) is not None:
                state = '空仓'
            src_bits.append('%s %s' % (ROUTE_TAG[r], state))
        else:
            src_bits.append('%s %d只' % (ROUTE_TAG[r], n))
    multi = [x for x in allrows if x['共振'] >= 2]
    src_line = '候选来源: ' + ' · '.join(src_bits) + '；共振≥2: %d只；去重后候选%d只' % (len(multi), len(allrows))

    rows = []
    for i, x in enumerate(top5, 1):
        seg = []
        for r in ('auction', 'lhb', 'theme', 'logic', 'limitup'):
            s = x['sources'].get(r)
            if not s:
                continue
            tag = '正式荐票' if s.get('来自计划') else ('#%d' % s['排名'])
            seg.append('<b>%s</b> %s %s<br><span class="mut">%s</span>' % (
                H.escape(ROUTE_TAG[r]), tag, H.escape(str(s['指标'])), H.escape(str(s['依据'])[:110])))
        exes = []
        for r in ('auction', 'lhb', 'limitup'):
            s = x['sources'].get(r)
            if s and s.get('执行') and s['执行'] != '—':
                exes.append('<span class="mut">%s</span> %s' % (H.escape(ROUTE_TAG[r]), H.escape(str(s['执行']))))
        exe_html = '<br>'.join(exes) if exes else '<span class="mut">— 该路无执行口径</span>'
        if not seg:
            seg = ['<span class="mut">该票不在五路候选Top5（候选源=各路荐票榜），由总审筛选清单直接留用'
                   '（建议权重%s%%）；本卡不替它编来源指标。</span>'
                   % (x.get('总审建议权重%') if x.get('总审建议权重%') is not None else '—')]
        if x.get('缺跨路来源'):
            res_cell = '<b>总审</b><br><span class="mut">无跨路共振</span>'
        else:
            res_cell = ('<b>%d</b><br><span class="mut">位置分%d%s</span>'
                        % (x['共振'], x['位置分'],
                           ('·建议%s%%' % x['总审建议权重%']) if x.get('总审建议权重%') is not None else ''))
        theme = '—'
        ql = load_cache.get('limitup', {}).get(x['代码']) or {}
        if ql.get('大方向'):
            theme = ql['大方向']
        if (not theme or theme == '—') and x['sources'].get('lhb'):
            zj = load('席位荐票_%s.json' % d) or {}
            seat_row = next((y for y in (zj.get('top5') or []) if _code(y) == x['代码']), None)
            if seat_row and seat_row.get('题材'):
                theme = seat_row['题材']
        rows.append('<tr><td>%d</td>'
                    '<td style="white-space:nowrap"><b>%s</b><br><span class="mut">%s</span></td>'
                    '<td style="white-space:nowrap">%s</td>'
                    '<td style="word-break:break-word">%s</td>'
                    '<td style="word-break:break-word">%s</td>'
                    '<td style="white-space:nowrap">%s</td></tr>' % (
                        i, H.escape(str(x['名称'])), x['代码'], res_cell,
                        '<br>'.join(seg), exe_html, H.escape(str(theme))))

    if rows:
        table = ('<div class="card"><table style="table-layout:fixed;width:100%">'
                 '<colgroup><col style="width:26px"><col style="width:104px"><col style="width:74px">'
                 '<col><col style="width:176px"><col style="width:88px"></colgroup>'
                 '<tr><th>#</th><th>标的</th><th>共振·位置</th><th>来源路核心指标与判据</th>'
                 '<th>执行口径(T+1开买·各路历史值)</th><th>题材/归位</th></tr>' + ''.join(rows) + '</table></div>')
    elif allrows and (ginfo or {}).get('状态') == 'applied':
        table = ('<div class="card"><b>— 总审留用为空（合法空仓）</b><br><span class="mut">'
                 '候选池 %d 只全部被总审剔除或未列留用名单，本卡不递补、不凑票。</span></div>' % len(allrows))
    else:
        table = '<div class="card"><b>— 跨路候选池为空</b><br><span class="mut">五路当日均无候选(空仓/无产出), 本卡不凑票。</span></div>'

    ginfo = ginfo or {}
    gate_txt = ''
    if ginfo.get('状态') == 'applied':
        cut = '、'.join('%s %s' % (x['名称'], x['代码']) for x in (ginfo.get('被剔出榜') or []))
        gate_txt = ('总审门禁 applied: 并集%s→留%s(剔%s 不放进榜)%s%s' % (
            ginfo.get('并集数'), ginfo.get('留数'), ginfo.get('剔数'),
            (' · 留用合计 %s%%' % ginfo.get('留用合计权重%')) if ginfo.get('留用合计权重%') is not None else '',
            ('；已剔: ' + cut) if cut else ''))
    else:
        gate_txt = ('总审门禁 %s → 本卡按原始跨路共识排序, 未与总审筛选对齐, 仅作参考'
                    % (ginfo.get('状态') or 'unavailable'))

    hint1 = ('<div class="hint">★筛选口径: 总审筛选清单(唯一真源, 只让「留」进榜) → 五路候选去重 → '
             '共振路数(被几路同时选中)优先 → 路内位置分 → 执行期望 → 取前5; 每行标注来源路与该路核心指标。%s</div>'
             % H.escape(env))
    hint2 = '<div class="hint">%s</div>' % H.escape(src_line)
    hint_gate = '<div class="hint">%s</div>' % H.escape(gate_txt)
    hint3 = ('<div class="hint">本卡为跨路筛选后最值得操作/观察的清单, 非买入指令; '
             '执行口径=各路历史桶均值/滚动值(非个股预言), 缺口径的路如实标 —。</div>')
    return ('<!--CROSSPICK-->' + hint1 + hint_gate + table + hint2 + hint3 + '<!--/CROSSPICK-->')


def main(d):
    top5, allrows, inv, ginfo = build(d)
    html = render(d, top5, allrows, inv, ginfo)
    out = dict(日期=d, 路='cross', 荐票源='概览·跨路筛选(v2 总审门禁→跨路共识)',
               口径='总审筛选清单(只让「留」进榜)→五路候选去重→共振路数→路内位置分Σ(6-排名)→执行期望→代码序→取5; 零编造, 缺失标—; 非买入指令',
               总审门禁=ginfo,
               来源清单=[{'路': r, '路名': ROUTE_NAME[r], '候选数': n} for r, n in inv],
               候选池=[{'代码': x['代码'], '名称': x['名称'], '共振': x['共振'], '位置分': x['位置分'],
                        '执行期望': x['执行期望'], '总审裁决': x.get('总审裁决'),
                        '来源': {r: dict(s) for r, s in x['sources'].items()}} for x in allrows],
               top5=[x['代码'] for x in top5])
    jp = os.path.join(L, '跨路荐票_%s.json' % d)
    cp = os.path.join(L, '跨路荐票卡_%s.html' % d)
    if os.path.isfile(cp):
        old = open(cp, encoding='utf-8').read()
        if old != html:
            print('  [note] 跨路荐票卡_%s.html 已存在且内容变化 → 按当日产物重写(幂等, 由当日真源决定)' % d)
    json.dump(out, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(cp, 'w', encoding='utf-8').write(html)
    print('%s 跨路Top5(候选%d只, 共振≥2 %d只):' % (d, len(allrows), len(out['top5'])))
    for i, x in enumerate(top5, 1):
        print('  %d %s %s 共振%d 位置分%d 来源%s | %s' % (
            i, x['名称'], x['代码'], x['共振'], x['位置分'],
            ','.join(ROUTE_TAG[r] for r in ('auction', 'lhb', 'theme', 'logic', 'limitup') if r in x['sources']),
            (x['执行期望'] if x['执行期望'] is not None else '—')))
    print('  写入: %s / %s' % (os.path.basename(jp), os.path.basename(cp)))
    return out


load_cache = {}
if __name__ == '__main__':
    import datetime
    main(sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime('%Y%m%d'))
