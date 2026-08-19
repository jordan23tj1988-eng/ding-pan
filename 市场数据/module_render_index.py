# -*- coding: utf-8 -*-
"""module_render_index.py —— index 概览页组件化渲染(2026-08-12, 模板=module_render_cycle.py, 六页模块化收官)
读数据源 → 头部 LLM hero 原文(有 body) / 机器组件区(无 body 断档日, 数字可回源) → 输出页面 body 片段
用法: python module_render_index.py 20260812 [--out 路径] [--shell]
铁律: 机器组件数字只来自数据源文件(_市场温度表.json/_情绪先行指标.json/
      _周期投票台账.jsonl/_周期投票准确率.json);
      LLM 组件只从 judgment bodies['index'] 按物理 h2 边界提取原文, 不重写不重排;
      数据缺失=显示"—"/断档标注, 零编造(不补造数字)。
五板块: 一 明日核心观察点 / 二 五路看牌 / 三 拐点预警 / 四 总裁决 / 五 认知迭代(LLM 原文保真, 认知迭代折叠)
机器区(仅无 body 断档日, 锚点成对, 哨兵核对): <!--IDXTEMP--> 温度总览 / <!--IDXLEAD--> 先行指标 /
  <!--IDXVOTE--> 五路投票
★有 body 日 mach 置空(黄金版形态=hero+五板块直连, 机器数据本就嵌在 LLM hero/kpi 内)
  —— 2026-08-12 用户"为什么改变了我页面的样式"教训, 同 cycle 页处理。
★断档处理(2026-08-12): 8/11 晚间管道未产 index body → 机器三卡照常渲染
      (温度表/先行指标/投票台账 当日真数据), 事实性 hero + 断档卡, 不编造判断。
★h2 边界用物理切块而非固定序号: 黄金版717(7/16) 三拐点预警嵌在 rail 内先于二出现,
  固定序号边界会切空/切错 —— 逐 h2 物理切片保真, 任何 LLM 顺序都原文重现。
"""
import re, os, sys, json

BASE = r'D:\股票数据\市场数据'
if not os.path.isdir(BASE):
    BASE = [p for p in ('/sessions/*/mnt/股票数据/市场数据',) if os.path.isdir(p)][0] if os.path.isdir('/sessions') else BASE
L = os.path.join(BASE, '_学习')

# ============ 数据契约加载 ============
def load_body(d):
    """LLM 组件提取源: judgment_{d}.json bodies['index']"""
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return ''
    try:
        return json.load(open(p, encoding='utf-8'))['bodies'].get('index') or ''
    except Exception:
        return ''

def load_json(name, d=None):
    """按文件名+日期加载 JSON, 缺=返回 None(零编造: 渲染侧显示 —)"""
    fn = name if d is None else name % d
    p = os.path.join(L, fn)
    if not os.path.exists(p): return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

def load_temp(d):
    """_市场温度表.json → (dict by date, 当日 None 可)"""
    t = load_json('_市场温度表.json')
    if not t: return None, None
    days = sorted(k for k in t if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
    return t, days

def load_lead(d):
    """_情绪先行指标.json → (dict by date, 当日 None 可)"""
    t = load_json('_情绪先行指标.json')
    if not t: return None, None
    days = sorted(k for k in t if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
    return t, days

def load_votes(d):
    """_周期投票台账.jsonl → 最新一日(d<=目标) 主判+五路投票; 无= (None,None)"""
    p = os.path.join(L, '_周期投票台账.jsonl')
    if not os.path.exists(p): return None, None
    rows = []
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l: continue
        try:
            j = json.loads(l)
        except Exception:
            continue
        if str(j.get('d', '')) <= str(d):
            rows.append(j)
    if not rows: return None, None
    rows.sort(key=lambda x: x['d'])
    last = rows[-1]
    return last.get('d'), last

def load_acc():
    return load_json('_周期投票准确率.json') or {}

# ============ 通用 HTML 工具 ============
def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _match_div(s, start):
    """返回从 start 处 <div 开始的配平 </div> 结束位置(容错)"""
    depth = 0
    for m in re.finditer(r'<div\b|</div>', s[start:]):
        if m.group() == '</div>':
            depth -= 1
            if depth == 0: return start + m.end()
        else:
            depth += 1
    return len(s)

def _pct(x, digits=0, signed=False):
    """小数→百分数字符串; None→'—'"""
    if x is None: return '—'
    return ('%+.' + str(digits) + 'f%%' if signed else '%.' + str(digits) + 'f%%') % (x * 100)

def _wan(yi):
    """成交额亿 → 万亿字符串(2位); None→'—'"""
    if yi is None: return '—'
    return ('%.2f' % (yi / 10000.0)).rstrip('0').rstrip('.') if yi >= 10000 else '—'

def _tli_date(tli):
    m = re.search(r'<b>(\d\d-\d\d)</b>', tli)
    if m: return m.group(1)
    m2 = re.search(r'<div class="d">\s*(\d{4}-\d{2}-\d{2})', tli)
    if m2: return m2.group(1)[5:]
    return ''

# ============ 机器区: 温度总览卡(仅断档日) ============
def r_mach_temp(d):
    """IDXTEMP 卡: 当日温度/档位/涨停/跌停/炸板率/量能 + 近5日走势(温度表权威)
    数据源: _市场温度表.json; 断档(当日无)→ 卡头标注 + 读数—"""
    t, days = load_temp(d)
    if not t or not days:
        return '<!--IDXTEMP-->\n<div class="card"><p class="mut">温度总览: 温度表无 %s 及更早数据</p></div>\n<!--/IDXTEMP-->\n' % d
    cur = t[days[-1]]
    has_cur = (str(days[-1]) == str(d))
    stale = '' if has_cur else ' <span class="warn">⚠ 当日未产, 数据截至 %s</span>' % (days[-1][4:6] + '-' + days[-1][6:8])
    # 近5日 mini 走势(温度+涨停)
    w5 = days[-5:]
    mini = ''
    for dd in w5:
        v = t[dd]
        temp = v.get('温度')
        zt = v.get('涨停数')
        mini += ('<span class="dayc%s">%s %s°/%s只</span>' % (
            ' now' if dd == days[-1] else '', dd[5:7] + '-' + dd[7:9],
            temp if temp is not None else '—', zt if zt is not None else '—'))
    temp = cur.get('温度'); tf = cur.get('温度档')
    zt = cur.get('涨停数'); dt = cur.get('跌停数')
    zb = cur.get('炸板率'); w = cur.get('成交额亿')
    ladder = cur.get('梯队') or {}
    ladder_txt = ''
    if ladder:
        parts = []
        for lv in sorted((int(k) for k in ladder), reverse=True):
            parts.append('%d板%d只' % (lv, ladder[str(lv)]))
        ladder_txt = ' · 梯队: ' + ' '.join(parts)
    rows = ('<tr><td class="l">情绪温度</td><td>%s · 档位 %s%s</td></tr>\n'
            '<tr><td class="l">涨停/跌停</td><td>%s / %s · 炸板率 %s</td></tr>\n'
            '<tr><td class="l">量能</td><td>%s 万亿</td></tr>\n'
            '<tr><td class="l">连板梯队</td><td>%s</td></tr>\n'
            % (temp if temp is not None else '—', _esc(tf or '—'), stale,
               zt if zt is not None else '—', dt if dt is not None else '—',
               _pct(zb, 1) if zb is not None else '—', _wan(w),
               ladder_txt or '—'))
    head = ('<div class="card"><h3 style="margin:0 0 8px">温度总览 <span class="hint">机器核对 · 市场温度表权威</span></h3>'
            '<p class="mut" style="margin:0 0 6px">近5日: %s</p>'
            '<table class="p2"><tr><th class="l">指标</th><th>读数</th></tr>%s</table></div>\n'
            % (mini or '—', rows))
    return '<!--IDXTEMP-->\n%s<!--/IDXTEMP-->\n' % head

# ============ 机器区: 先行指标卡(仅断档日) ============
def r_mach_lead(d):
    """IDXLEAD 卡: 当日晋级/核按钮/昨停溢价/三窗触发器(先行指标权威)
    数据源: _情绪先行指标.json; 断档(当日无)→ 卡头标注 + 读数—"""
    t, days = load_lead(d)
    if not t or not days:
        return '<!--IDXLEAD-->\n<div class="card"><p class="mut">先行指标: 数据源缺失</p></div>\n<!--/IDXLEAD-->\n'
    cur = t[days[-1]]
    has_cur = (str(days[-1]) == str(d))
    stale = '' if has_cur else ' <span class="warn">⚠ 当日未产, 数据截至 %s</span>' % (days[-1][4:6] + '-' + days[-1][6:8])
    jd = cur.get('晋级') or {}
    hb = cur.get('核按钮') or {}
    pm = cur.get('昨日涨停溢价') or {}
    tr = cur.get('触发器') or []
    trig = ''.join('<li>%s</li>' % _esc(x) for x in tr) or '<li class="mut">三窗均未触发(冰点<25/过热≥85/溢价连负3日)</li>'
    rows = ('<tr><td class="l">晋级</td><td>涨停数_净 %s · 首板%s / 二连板%s / 三连板%s</td><td>1进2率 %s · 2进3率 %s · 高度晋级率 %s</td></tr>\n'
            '<tr><td class="l">核按钮</td><td>昨日涨停 %s</td><td>核按钮率 %s</td></tr>\n'
            '<tr><td class="l">昨停溢价</td><td>样本 %s</td><td>执行均收 %s · 胜率 %s · 大面率 %s</td></tr>\n'
            % (jd.get('涨停数_净', '—'), jd.get('首板', '—'), jd.get('二连板', '—'), jd.get('三连板', '—'),
               _pct(jd.get('一进二率'), 1), _pct(jd.get('二进三率'), 1), _pct(jd.get('高度晋级率'), 1),
               hb.get('昨日涨停数', '—'), _pct(hb.get('核按钮率'), 1),
               pm.get('样本', '—'),
               ('%+.2f%%' % pm['执行均收']) if pm.get('执行均收') is not None else '—',
               _pct(pm.get('执行胜率'), 1), _pct(pm.get('大面率'), 1)))
    head = ('<div class="card"><h3 style="margin:0 0 8px">情绪先行指标 <span class="hint">机器核对 · 情绪先行指标.py 权威%s</span></h3>'
            '<table class="p2"><tr><th class="l">指标</th><th>口径</th><th>读数</th></tr>%s</table>'
            '<p style="margin:8px 0 4px"><b>触发器</b></p><ul class="obs-watch" style="margin:0;padding-left:18px">%s</ul></div>\n'
            % (stale, rows, trig))
    return '<!--IDXLEAD-->\n%s<!--/IDXLEAD-->\n' % head

# ============ 机器区: 五路投票卡(仅断档日) ============
ROUTE_LABEL = [('auction', '①竞价'), ('lhb', '②席位'), ('theme', '③题材'),
               ('logic', '④产逻'), ('limitup', '⑤质量')]

def r_mach_vote(d):
    """IDXVOTE 卡: 台账最新主判 + 五路投票(同意/分歧 + stage·direction + 置信 + 准确率)
    数据源: _周期投票台账.jsonl + _周期投票准确率.json
    断档(当日无台账行)→ 标注截至日, 仍显示最新一日投票(来源如实)"""
    vd, v = load_votes(d)
    if not v:
        return '<!--IDXVOTE-->\n<div class="card"><p class="mut">五路投票: 台账为空</p></div>\n<!--/IDXVOTE-->\n'
    stale = '' if vd == str(d) else ' <span class="warn">⚠ 当日未产, 投票截至 %s</span>' % (vd[4:6] + '-' + vd[6:8])
    zp = v.get('主判') or {}
    votes = v.get('votes') or {}
    acc = load_acc()
    cards = ''
    agree_n = 0
    for rk, rl in ROUTE_LABEL:
        vt = votes.get(rk) or {}
        if not vt:
            cards += ('<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#5c6674">%s <br>无票</div>\n' % rl)
            continue
        sd = vt.get('stage', '—'); dd = vt.get('direction', '—')
        agree = (dd == zp.get('direction'))
        if agree: agree_n += 1
        mark = '<span style="color:#4caf7d">同意</span>' if agree else '<span style="color:#e56060">分歧</span>'
        a = acc.get(rk) or {}
        at = ('%d/%d' % (a.get('hits', 0), a.get('n', 0))) if a else '—'
        cards += ('<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#d8dee9">%s %s<br>'
                  '<b style="color:#d8dee9">%s·%s</b><br><span style="color:#5c6674">置信%.2f·准确率%s</span></div>\n'
                  % (rl, mark, _esc(sd), _esc(dd), vt.get('confidence') or 0, at))
    zp_txt = ('<div style="font-size:11px;letter-spacing:2px;color:#d9a441;font-family:monospace">五路周期投票 · 主判=%s·%s%s</div>'
              % (_esc(zp.get('stage', '—')), _esc(zp.get('direction', '—')), stale))
    note = ('<div style="margin-top:8px;color:#5c6674;font-size:11px">%d/%d 路与主判同向 · 分歧未达阈值(当日≥3/5或加权≥0.60复议; 连续3日≥2路同向重做) · '
            '次日A档三指标Δ客观结算, 准确率定话语权 · ★一致率长期>0.8=回声室警示(evidence须私有数据)</div>'
            % (agree_n, len(ROUTE_LABEL)))
    head = ('<div style="margin:10px 0;padding:12px 14px;background:#14171e;border:1px solid #2a2f3a;border-radius:10px">\n'
            '%s\n<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">\n%s</div>\n%s\n</div>\n'
            % (zp_txt, cards, note))
    return '<!--IDXVOTE-->\n%s<!--/IDXVOTE-->\n' % head

# ============ LLM 区: 五板块原文(逐字节保真, 物理 h2 切块) ============
def split_h2(body):
    """按物理位置切 h2 板块: 返回 [(h2_标题原文含h2标签, 板块内容)] 列表
    ★黄金版717(7/16): 三拐点预警嵌在观察点 rowC rail 内(先于二出现),
      固定序号边界(<h2>一→<h2>二)会切错 → 物理切片保真, 顺序=LLM 当日实际书写顺序"""
    segs = []
    for m in re.finditer(r'<h2\b', body):
        segs.append(m.start())
    if not segs:
        return [('', body)]
    out = []
    for i, s in enumerate(segs):
        e = segs[i + 1] if i + 1 < len(segs) else len(body)
        out.append((body[s:], body[s:e]))
    return out

def r_obs_llm(seg):
    """板块一 观察点: 原文保真(含 rowC/rail 结构, 不动 LLM 手写布局)"""
    return seg

def r_llm(seg):
    """任意 h2 板块原文逐字节保真"""
    return seg

def r_cog(body, first_h2_pos):
    """板块五 认知迭代: 最后一个 h2 起 → 尾; 模拟 _fold_tl(最新1条外露+其余折叠)
    仅当 tl 用 <div class="tl"> 包裹且 ≥2 条才折叠; 单条/裸 tli(8/12 格式)原样保真"""
    h5 = body.find('<h2>五')
    if h5 < 0:
        # 无"五"标题: 最后一个 h2 起 → 尾
        segs = [m.start() for m in re.finditer(r'<h2\b', body)]
        if not segs: return ''
        h5 = segs[-1]
    seg = body[h5:]
    head_end = seg.find('</h2>')
    if head_end < 0: return seg
    head = seg[:head_end + 5]
    rest = seg[head_end + 5:]
    p = rest.find('<div class="tl">')
    if p < 0:
        return seg  # 无 tl 包裹(8/12 裸 tli) → 原文
    e = _match_div(rest, p)
    tl = rest[p:e]
    if tl.count('<div') != tl.count('</div>'):
        return seg  # 不平衡不折, 防切坏
    ds = re.findall(r'<div class="d">([0-9][0-9-]+)', tl)
    if len(ds) < 2:
        ds = re.findall(r'<div class="tli[^"]*">\s*<b>([0-9-]{4,5})', tl)
    if len(ds) < 2 or 'tlfold' in rest[max(0, p - 160):p]:
        return seg
    inner = tl[len('<div class="tl">'):-len('</div>')]
    items = []; k = 0; prefix = ''; trailing = ''
    while True:
        mq = re.compile(r'<div class="tli[^"]*">').search(inner, k)
        q = mq.start() if mq else -1
        if q < 0:
            trailing = inner[k:]; break
        if not items: prefix = inner[k:q]
        e2 = _match_div(inner, q)
        items.append(inner[q:e2]); k = e2
    if len(items) < 2:
        return seg
    # 按日期降序(最新在上, 同日保持原序)
    def _dt(it):
        m = re.search(r'<div class="d">\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', it)
        if m: return m.group(1)
        m2 = re.search(r'<b>([0-9]{2}-[0-9]{2})', it)
        return '0000-' + m2.group(1) if m2 else '0000-00-00'
    items = sorted(items, key=_dt, reverse=True)
    first = '<div class="tl">' + prefix + items[0] + '</div>'
    rest_items = ''.join(items[1:])
    fold = ('<details class="chain tlfold"><summary><b>更早的认知迭代</b> '
            + '<span class="chip">' + str(len(items) - 1) + '条</span> <span class="mut">' + ds[-1] + ' ~ ' + ds[1] + '</span></summary>'
            + '<div class="inner"><div class="tl">' + rest_items + trailing + '</div></div></details>')
    return head + rest[:p] + first + fold + rest[e:]

def r_master(d):
    """2026-08-15 Master 板块: 读总审.json 4字段(综合深挖/线索跟踪/指派清单/认知迭代)机器渲染
    单一真源=总审.json; 概览页 Master 综合板块 = 4子块(用 .card/.tl 组件, index 无表格组件)"""
    zj = load_json('总审_%s.json' % d)
    if not zj:
        return ''
    dig = zj.get('综合深挖') or []
    tracks = zj.get('线索跟踪') or []
    assigns = zj.get('指派清单') or []
    cog = zj.get('认知迭代') or []
    if not (dig or tracks or assigns or cog):
        return ''  # 旧总审.json 无 4 字段 → 不渲染 Master 板块(保真)
    out = ['<h2>五 Master 综合<span class="hint">总审升级: 综合深挖 · 线索跟踪 · 指派清单 · 认知迭代</span></h2>']
    if dig:
        out.append('<div class="card"><b>综合深挖</b>')
        for x in dig:
            if isinstance(x, dict):
                out.append('<p style="margin:6px 0 0"><b>%s</b>：%s</p>' % (
                    _esc(str(x.get('主题', '—'))), _esc(str(x.get('深挖结论', '—')))))
        out.append('</div>')
    if tracks:
        out.append('<div class="card"><b>线索跟踪看板</b>')
        for t in tracks:
            if isinstance(t, dict):
                out.append('<p style="margin:6px 0 0">[<span class="mut">%s</span>] <span class="mut">%s</span> <b>%s</b> <span class="chip">%s</span> · %s</p>' % (
                    _esc(str(t.get('线索ID', '—'))), _esc(str(t.get('来源路', '—'))), _esc(str(t.get('内容', '—'))),
                    _esc(str(t.get('状态', '—'))), _esc(str(t.get('下次验证点', '—')))))
        out.append('</div>')
    if assigns:
        out.append('<div class="card"><b>指派清单</b>')
        for a in assigns:
            if isinstance(a, dict):
                out.append('<p style="margin:6px 0 0">[<span class="mut">%s</span>] → <b>%s</b>：%s <span class="chip">%s</span></p>' % (
                    _esc(str(a.get('指派ID', '—'))), _esc(str(a.get('指派给', '—'))),
                    _esc(str(a.get('深挖任务', '—'))), _esc(str(a.get('状态', '—')))))
        out.append('</div>')
    if cog:
        _items = [c for c in cog if isinstance(c, dict)]
        def _mtli(c):
            return '<div class="tli"><div class="d"><b>%s</b></div><div class="h">%s</div><div class="b">%s</div></div>' % (
                d, _esc(str(c.get('认知点', '—'))), _esc(str(c.get('依据', '—'))))
        if len(_items) >= 2:
            _tlis = _mtli(_items[0]) + ('<details class="chain tlfold"><summary><b>更早的认知迭代</b> %d条</summary><div class="inner">' % (len(_items) - 1)) + ''.join(_mtli(c) for c in _items[1:]) + '</div></details>'
        else:
            _tlis = _mtli(_items[0]) if _items else ''
        out.append('<div class="tl">%s</div>' % _tlis)
    return '\n'.join(out)

def r_gap_card(d):
    """当日无 index body → 断档卡(事实陈述, 不编造判断)"""
    return ('<div class="card" style="border-color:rgba(255,95,86,.35)"><b>⚠ 当日未产概览复盘 body</b>'
            '<p style="margin:6px 0 0">%s 晚间管道未产 judgment bodies.index, 判断板块(明日观察点/五路看牌/拐点预警/总裁决/认知迭代)当日无内容。'
            '机器数据(温度总览/先行指标/五路投票)已按数据源如实渲染, 见上方折叠区。</p></div>\n' % d)

# ============ 拼装器 ============
def build_page(d):
    """LLM 五板块原文(有 body, 物理 h2 切块保真, 认知迭代折叠) 或 断档卡(无 body)
    2026-08-15: Master 板块插在"总裁决"后; 总审含认知迭代时收编 index body 的"五" """
    body = load_body(d)
    if not body:
        return r_gap_card(d)
    master = r_master(d)
    _zj = load_json('总审_%s.json' % d)
    master_has_cog = bool(_zj and (_zj.get('认知迭代') or []))  # 总审认知迭代字段非空才收编
    segs = split_h2(body)
    out = []
    master_done = False
    for i, (h2raw, seg) in enumerate(segs):
        is_last = (i == len(segs) - 1)
        # 五 认知迭代板块: 收编(总审有认知迭代) 或 折叠
        if '认知迭代' in seg[:40]:
            if not master_done and master:
                out.append(master); master_done = True
            if master_has_cog:
                continue  # 收编: 总审认知迭代替代 index body 的"五"
            out.append(r_cog(seg, -1))
            continue
        out.append(seg)
        # 四 总裁决 之后插入 Master 板块
        if '总裁决' in seg[:40] and master and not master_done:
            out.append(master); master_done = True
    # fallback: 无"总裁决"板块 → Master 板块放末尾
    if master and not master_done:
        out.append(master)
    return ''.join(out)

def build_page_full(d, paper_block=''):
    """完整页 body(头部区 + 机器数据折叠区(仅断档日) + 模拟盘看板 + 五板块) → S2 接线用
    头部区(bodies 开头 hero/kpi/stance, 含竞价兑现卡)LLM 手写逐字节保真(有 body);
    无 body → 自产事实性头部(日期+断档提示), 不编造判断。
    机器区三卡收进 details.chain 折叠(默认收起) — 仅无 body 断档日兜底;
    有 body 日机器区置空(黄金版形态=hero+五板块直连, 同 cycle 2026-08-12 教训)。
    锚点(IDXTEMP/IDXLEAD/IDXVOTE/PAPERTRADE)成对保留供哨兵核对"""
    body = load_body(d)
    if body:
        segs = [m.start() for m in re.finditer(r'<h2\b', body)]
        i2 = segs[0] if segs else -1
        if i2 > 0:
            head = body[:i2]
            if not head.endswith('\n'): head += '\n'
        else:
            head = body if body.endswith('\n') else body + '\n'
    else:
        head = ('<div class="rowA">\n<div class="hero"><div class="kick">Index · 总判断 · 截至 %s 收盘</div>'
                '<h1>概览页 · %s 复盘未产, 数据断档如实呈现</h1>'
                '<p>机器数据(温度总览/先行指标/五路投票)按数据源渲染; 判断板块缺 body 不编造。</p>'
                '<div class="stance"><span class="pill warn">状态 · <b class="s-weak">复盘断档</b></span></div></div>\n</div>\n'
                % (d[4:6] + '-' + d[6:8], d[4:6] + '-' + d[6:8]))
    mach = ''.join([r_mach_temp(d), r_mach_lead(d), r_mach_vote(d)])
    if body:
        mach = ''
    elif mach.strip():
        chips = '<span class="chip">%d卡</span>' % mach.count('class="card"')
        mach = ('<details class="chain"><summary><b>机器数据源</b> %s '
                '<span class="mut">温度/先行指标/投票数字核对层 · 展开查看 · 判断以当日复盘为准</span></summary>'
                '<div class="inner">\n%s</div></details>\n' % (chips, mach))
    paper = ''
    if paper_block:
        paper = '<!--PAPERTRADE-->\n' + paper_block + '<!--/PAPERTRADE-->\n'
    return head + mach + paper + build_page(d)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '20260811'
    page = build_page_full(d)
    print('=== index 模块化渲染 @%s ===' % d)
    print('整页 body: %d KB | 卡%d 表%d 折叠%d h2:%d | 断档卡:%s' % (
        len(page) // 1024, page.count('class="card"'), page.count('<table'),
        page.count('<details'), len(re.findall(r'<h2>', page)),
        '⚠' in page and '未产' in page))
    print('机器锚: IDXTEMP=%s IDXLEAD=%s IDXVOTE=%s | h2 板块数=%d' % (
        page.count('<!--IDXTEMP-->') >= 1 and page.count('<!--/IDXTEMP-->') >= 1,
        page.count('<!--IDXLEAD-->') >= 1 and page.count('<!--/IDXLEAD-->') >= 1,
        page.count('<!--IDXVOTE-->') >= 1 and page.count('<!--/IDXVOTE-->') >= 1,
        len(re.findall(r'<h2\b', page))))
    if '--shell' in sys.argv:
        # 独立页面完整套壳: 从 SITE 全站页解析提取 shell(防编码乱码+组件缺失)
        site = os.path.join(os.path.dirname(os.path.abspath(__file__)), '复盘', '盯盘台')
        shell_src = os.path.join(site, 'index.html')
        if not os.path.isfile(shell_src):
            shell_src = os.path.join(site, 'lhb.html')
        shell = open(shell_src, encoding='utf-8').read()
        paper = os.path.join(L, '_模拟盘', 'master', '看板_%s.html' % d)
        paper_block = ''
        if os.path.isfile(paper):
            paper_block = open(paper, encoding='utf-8').read()
            print('PAPERTRADE看板已嵌入:', os.path.basename(paper))
        else:
            print('⚠ 无看板_%s.html, PAPERTRADE留空锚' % d)
        page = build_page_full(d, paper_block)
        ib = shell.find('<body'); jb = shell.find('>', ib) + 1 if ib > 0 else len(shell)
        iw = shell.find('<div class="wrap">') if '<div class="wrap">' in shell else -1
        if iw > 0:
            body_end = shell.find('</body>')
            tail = shell[shell.rfind('<script', 0, body_end):body_end] if shell.rfind('<script', 0, body_end) > 0 else ''
            page = shell[:jb] + '\n' + shell[jb:iw] + '<div class="wrap">\n' + page + '\n</div>\n' + tail + '</body></html>'
        else:
            page = shell[:jb] + '\n' + page + '</body></html>'
        print('已套壳: navbar=%s wrap=%s tail_script=%s' % (
            'class="navbar"' in page, '<div class="wrap">' in page, 'gsap' in page))
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    if out:
        open(out, 'w', encoding='utf-8').write(page)
        print('已写出:', out)
