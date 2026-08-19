# -*- coding: utf-8 -*-
"""module_render_cycle.py —— cycle 页组件化渲染(2026-08-12, 模板=module_render_theme.py, 修复周期情绪页)
读数据源 → 头部机器组件区(量能台阶/先行指标/连板梯队/五路投票, 数字可回源) + 黄金版七板块 LLM 原文 → 输出页面 body 片段
用法: python module_render_cycle.py 20260811 [--out 路径] [--shell]
铁律: 机器组件数字只来自数据源文件(_市场温度表.json/_情绪先行指标.json/{d}/zt_pool.csv/
      _周期投票台账.jsonl/_周期投票准确率.json);
      LLM 组件只从 judgment bodies['cycle'] 按边界提取原文, 不重写;
      数据缺失=显示"—"/断档标注, 零编造(不补造数字)。
七板块: 一量能台阶 二先行指标 三情绪五阶段·五路投票 四连板梯队 五攻防 六自主深挖 七认知迭代(LLM 原文保真)
机器区四卡(锚点成对, 哨兵核对): <!--VOLSTEP--> 量能台阶 / <!--LEADIND--> 先行指标 /
  <!--LADDER--> 连板梯队 / <!--MACHVOTE--> 五路投票
  ★锚名= MACHVOTE 而非 VOTEBOARD: 黄金版段三 LLM 手写块自带 <!--VOTEBOARD--> 锚(body 原文保真不动),
  机器卡若同名 → 有 body 日锚起2/止2(7/16 实测撞锚), 哨兵强制唯一会 FAIL。
★断档处理(2026-08-12): 8/11 晚间管道只产 limitup/lhb/theme 三路, cycle body/先行指标/投票缺失
      → 机器卡照常渲染(温度表/zt_pool 8/11 有真数据), 断档源卡头标注"⚠数据截至XX"; LLM 区缺 body → 断档卡,
      不编造判断。有 body 日(如 20260716) → 七板块逐字节保真。
"""
import re, os, sys, json, csv
from collections import Counter
from _认知库渲染 import r_cog_lib

BASE = r'D:\股票数据\市场数据'
if not os.path.isdir(BASE):
    BASE = [p for p in ('/sessions/*/mnt/股票数据/市场数据',) if os.path.isdir(p)][0] if os.path.isdir('/sessions') else BASE
L = os.path.join(BASE, '_学习')

# ============ 数据契约加载 ============
def load_body(d):
    """LLM 组件提取源: judgment_{d}.json bodies['cycle']"""
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return ''
    try:
        return json.load(open(p, encoding='utf-8'))['bodies'].get('cycle') or ''
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

def load_pool(d):
    """{d}/zt_pool.csv → list[dict]; 缺= []"""
    p = os.path.join(BASE, str(d), 'zt_pool.csv')
    if not os.path.exists(p): return []
    try:
        return list(csv.DictReader(open(p, encoding='utf-8-sig')))
    except Exception:
        return []

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

def _h2_seg(body, start_kw, end_kw=None):
    """提取 h2 板块原文(含 h2 标题行), 逐字节保真; end_kw 缺=取到尾部"""
    i = body.find(start_kw)
    if i < 0: return ''
    j = body.find(end_kw, i) if end_kw else -1
    return body[i:j if j > 0 else len(body)]

def _tli_date(tli):
    m = re.search(r'<b>(\d\d-\d\d)</b>', tli)
    if m: return m.group(1)
    m = re.search(r'<b>(\d{4})(\d{2})(\d{2})</b>', tli)
    return ('%s-%s' % (m.group(2), m.group(3))) if m else ''

def _pct(x, digits=0, signed=False):
    """小数→百分数字符串; None→'—'"""
    if x is None: return '—'
    return ('%+.' + str(digits) + 'f%%' if signed else '%.' + str(digits) + 'f%%') % (x * 100)

def _wan(yi):
    """成交额亿 → 万亿字符串(2位); None→'—'"""
    if yi is None: return '—'
    return ('%.2f' % (yi / 10000.0)).rstrip('0').rstrip('.') if yi >= 10000 else '—'

# 米开量能台阶换算(手册V2 §2.3, A档): 万亿 → (档序, 档名, 副标)
VOL_TIERS = [
    (3.8, '主升2确认', '放量突破'),
    (3.5, '突破压力', '需增量'),
    (3.3, '强修', '量能承接'),
    (3.0, '过渡', '量能中枢'),
    (0.0, '弱修', '缩量分歧'),
]

def vol_tier(w):
    """万亿量能 → (档序,档名,副标); None→None"""
    if w is None: return None
    for th, nm, sub in VOL_TIERS:
        if w >= th:
            return (VOL_TIERS.index((th, nm, sub)), nm, sub)
    return (4, '弱修', '缩量分歧')

def date_gap_note(days):
    """近3日是否连续(相邻间隔<=5自然日); 断档→标注文案"""
    if len(days) < 2: return ''
    from datetime import datetime
    gaps = []
    for a, b in zip(days[-3:][:-1], days[-3:][1:]):
        try:
            gap = (datetime.strptime(b, '%Y%m%d') - datetime.strptime(a, '%Y%m%d')).days
        except Exception:
            gap = 99
        if gap > 5:
            gaps.append('%s~%s 断档' % (a[4:6] + '-' + a[6:8], b[4:6] + '-' + b[6:8]))
    return ' ⚠' + '; '.join(gaps) if gaps else ''

# ============ 机器区: 量能台阶卡 ============
def r_mach_volstep(d):
    """VOLSTEP 卡: 米开量能台阶 5 档 + 近3日量能(dayc) + 断档标注
    数据源: _市场温度表.json 成交额亿(权威); 档位=米开手册换算"""
    t, days = load_temp(d)
    if not t or not days:
        return '<!--VOLSTEP-->\n<div class="card"><p class="mut">量能台阶: 温度表无 %s 及更早数据</p></div>\n<!--/VOLSTEP-->\n' % d
    cur = t[days[-1]]
    w_cur = cur.get('成交额亿')
    tier = vol_tier(w_cur / 10000.0 if w_cur else None)
    steps = ''
    for idx, (th, nm, sub) in enumerate(VOL_TIERS):
        rng = ('≥%.1f' % th) if idx == 0 else ('%.1f~%.1f' % (th, VOL_TIERS[idx - 1][0])) if idx < 4 else '<3.0'
        cur_cls = ' class="step cur"' if tier and tier[0] == idx else ' class="step dim"'
        dayc = ''
        if tier and tier[0] == idx:
            for dd in days[-3:]:
                w = t[dd].get('成交额亿')
                dayc += '<span class="dayc%s">%s %s</span>' % (
                    ' now' if dd == days[-1] else '', dd[5:7] + '-' + dd[7:9], _wan(w))
        steps += ('<div%s><span class="sr">%s</span><span class="sn">%s<small>%s</small></span>'
                  '<span class="sd">%s</span></div>\n'
                  % (cur_cls, rng, nm, sub, dayc))
    zt = cur.get('涨停数'); temp = cur.get('温度'); tf = cur.get('温度档')
    hint = ('量能 %s 万亿落"%s"档%s —— 米开量能台阶换算(手册V2 §2.3 A档, 腾讯替代源); '
            '当日涨停%d/温度%s(%s), 档位与温度档%s联动判读。'
            % (_wan(w_cur), tier[1] if tier else '—', date_gap_note(days),
               zt if zt is not None else -1, temp if temp is not None else -1,
               _esc(tf or '—'), _esc(tf or '—')))
    head = ('<div class="card"><h3 style="margin:0 0 8px">量能台阶 <span class="hint">机器核对 · 米开换算表(手册V2 §2.3) · 温度表权威</span></h3>'
            '<div class="steps">%s</div>'
            '<div class="hint">%s</div></div>\n' % (steps, hint))
    return '<!--VOLSTEP-->\n%s<!--/VOLSTEP-->\n' % head

# ============ 机器区: 先行指标卡 ============
def r_mach_leadind(d):
    """LEADIND 卡: 近20日涨停数_净柱状(SVG) + 当日读数(晋级/核按钮/溢价/触发器)
    数据源: _情绪先行指标.json; 断档(当日无)→ 卡头标注 + 读数—"""
    t, days = load_lead(d)
    if not t or not days:
        return '<!--LEADIND-->\n<div class="card"><p class="mut">先行指标: 数据源缺失</p></div>\n<!--/LEADIND-->\n' % d
    cur = t[days[-1]]
    has_cur = (str(days[-1]) == str(d))
    stale = '' if has_cur else ' <span class="warn">⚠ 当日未产, 数据截至 %s</span>' % (days[-1][4:6] + '-' + days[-1][6:8])
    # --- SVG 柱状(近20日 涨停数_净) ---
    w20 = days[-20:]
    maxv = max((t[x].get('晋级') or {}).get('涨停数_净') or 0 for x in w20) or 1
    n = len(w20)
    W, H, X0 = 880, 196, 46
    bw = min(21.3, (W - X0 - 20) / max(n, 1) - 8)
    bars = ''
    for i, dd in enumerate(w20):
        v = (t[dd].get('晋级') or {}).get('涨停数_净')
        if v is None:
            bars += ('<rect x="%.1f" y="8" width="%.1f" height="164" rx="1.5" fill="#2a2e3d"/>'
                     % (X0 + i * (bw + 8) + 4, bw))
            continue
        h = max(3.0, 164.0 * v / maxv)
        y = 172 - h
        bars += ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1.5" fill="#4a5666"/>'
                 '<text x="%.1f" y="%.1f" font-size="8" fill="#6b7683" text-anchor="middle">%d</text>'
                 % (X0 + i * (bw + 8) + 4, y, bw, h, X0 + i * (bw + 8) + 4 + bw / 2, y - 3, v))
    svg = ('<svg viewBox="0 0 880 196" style="width:100%%;height:auto;display:block">'
           '<line x1="46" y1="172" x2="866" y2="172" stroke="#3a3f46"/>'
           '<line x1="46" y1="112.5" x2="866" y2="112.5" stroke="#8a6d2f" stroke-dasharray="4 4" stroke-width="0.8"/>'
           '<text x="866" y="109.5" font-size="8.5" fill="#8a6d2f" text-anchor="end">1进2率10%%=接力冰点参考线</text>'
           '%s</svg>' % bars)
    # --- 当日读数 ---
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
    head = ('<div class="card"><h3 style="margin:0 0 8px">情绪先行指标 · 近20日 <span class="hint">(脚本段A档 · 情绪先行指标.py --card · 当日温度 %s%s)</span></h3>'
            '<p class="mut" style="margin:0 0 6px">口径: THS 涨停池(无ST) · 晋级率基准=THS 最近前一交易日(8/10池缺→按8/7) · 与梯队卡 zt_pool 全口径并存为体系既有设计</p>'
            '%s'
            '<table class="p2"><tr><th class="l">指标</th><th>口径</th><th>读数</th></tr>%s</table>'
            '<p style="margin:8px 0 4px"><b>触发器</b></p><ul class="obs-watch" style="margin:0;padding-left:18px">%s</ul></div>\n'
            % (('温度 %s·%s' % (_esc(str(t.get('温度'))), _esc(str(t.get('温度档'))))) if (t.get('温度') is not None) else '—',
               stale, svg, rows, trig))
    return '<!--LEADIND-->\n%s<!--/LEADIND-->\n' % head

# ============ 机器区: 连板梯队卡 ============
def r_mach_ladder(d):
    """LADDER 卡: 连板分布柱(最高板→首板) + 最高板个股 + 与温度表梯队互证
    数据源: {d}/zt_pool.csv(权威) 缺→温度表梯队"""
    pool = load_pool(d)
    t, days = load_temp(d)
    cur = t[days[-1]] if days else None
    ladder = None
    if pool:
        ladder = Counter()
        for r in pool:
            try:
                lb = int(float(r.get('连板数', 1) or 1))
            except Exception:
                lb = 1
            ladder[lb] += 1
        src_note = '涨停池 %d 只(zt_pool全口径,含ST)' % len(pool)
    elif cur and cur.get('梯队'):
        ladder = Counter({int(k): v for k, v in cur['梯队'].items()})
        src_note = '温度表梯队(zt_pool缺失)'
    else:
        return '<!--LADDER-->\n<div class="card"><p class="mut">连板梯队: 涨停池缺失</p></div>\n<!--/LADDER-->\n'
    mx = max(ladder.values()) or 1
    hi = max(ladder.keys())
    cols = ''
    for lv in sorted(ladder.keys(), reverse=True):
        v = ladder[lv]
        cls = ' class="col hotc"' if lv == hi else ' class="col"'
        cols += ('<div%s><i style="height:%d%%"></i><b>%d</b><span>%d板</span></div>\n'
                 % (cls, max(4, int(100.0 * v / mx)), v, lv))
    # 最高板个股
    top_nm, top_extra = '—', ''
    if pool:
        top = max(pool, key=lambda r: (int(float(r.get('连板数', 1) or 1)), str(r.get('涨停统计', ''))))
        top_nm = str(top.get('名称', '—'))
        top_extra = '%s(%s,%s首封)' % (_esc(top.get('所属行业', '—') or '—'),
                                       _esc(top.get('涨停统计', '—') or '—'),
                                       _esc(str(top.get('首次封板时间', '')) or '—'))
    zb = cur.get('炸板率')
    zt = cur.get('涨停数')
    mz = '温度表涨停%d只%s' % (zt, (' · 炸板率%0.1f%%' % (zb * 100)) if zb is not None else '') if zt is not None else ''
    first_n = ladder.get(1, 0)
    total = sum(ladder.values())
    sub = ('<div class="colsub"><span>最高%d板=%s %s</span>'
           '<span>腰部: 2板%d只 / 3板%d只 / 4板+%d只</span>'
           '<span>首板%d占%d%% · %s</span></div>\n'
           % (hi, top_nm, top_extra, ladder.get(2, 0), ladder.get(3, 0),
              sum(v for k, v in ladder.items() if k >= 4), first_n,
              int(100.0 * first_n / total) if total else 0, src_note))
    head = ('<div class="card"><h3 style="margin:0 0 8px">连板梯队 <span class="hint">机器核对 · 涨停池连板数分布(%s)</span></h3>'
            '<div class="cols">%s</div>%s'
            '<p style="margin:6px 0 0" class="mut">%s</p></div>\n'
            % (src_note, cols, sub, mz))
    return '<!--LADDER-->\n%s<!--/LADDER-->\n' % head

# ============ 机器区: 五路投票卡 ============
ROUTE_LABEL = [('auction', '①竞价'), ('lhb', '②席位'), ('theme', '③题材'),
               ('logic', '④产逻'), ('limitup', '⑤质量')]

def r_mach_vote(d):
    """VOTEBOARD 卡: 台账最新主判 + 五路投票(同意/分歧 + stage·direction + 置信 + 准确率)
    数据源: _周期投票台账.jsonl + _周期投票准确率.json
    断档(当日无台账行)→ 标注截至日, 仍显示最新一日投票(来源如实)"""
    vd, v = load_votes(d)
    if not v:
        return '<!--VOTEBOARD-->\n<div class="card"><p class="mut">五路投票: 台账为空</p></div>\n<!--/VOTEBOARD-->\n'
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
    head = ('<!--MACHVOTE--><div style="margin:10px 0;padding:12px 14px;background:#14171e;border:1px solid #2a2f3a;border-radius:10px">\n'
            '%s\n<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">\n%s</div>\n%s\n</div><!--/MACHVOTE-->\n'
            % (zp_txt, cards, note))
    return head

# ============ LLM 区: 七板块原文(逐字节保真) ============
def r_vol(body):  return _h2_seg(body, '<h2>一', '<h2>二')
def r_lead(body): return _h2_seg(body, '<h2>二', '<h2>三')
def r_stage(body):return _h2_seg(body, '<h2>三', '<h2>四')
def r_ladder_llm(body): return _h2_seg(body, '<h2>四', '<h2>五')
def r_attack(body):return _h2_seg(body, '<h2>五', '<h2>六')
def r_scan(body): return _h2_seg(body, '<h2>六', '<h2>七')

def r_cog(body, d=None):
    """板块七 认知迭代: h2七 → 尾; 模拟 _fold_tl(最新1条外露+其余折叠)
    ★2026-08-16: d 给定时丢弃 body 手写历史 tli(日期<d), 历史统一由 r_cog_lib 从认知库提供"""
    h7 = body.find('<h2>七')
    if h7 < 0: return ''
    head = body[h7:body.find('</h2>', h7) + 5] if body.find('</h2>', h7) > 0 else body[h7:]
    ts = body.find('<div class="tl">', h7)
    if ts < 0: return head
    te = _match_div(body, ts)
    seg = body[ts:te]
    items = []
    for m in re.finditer(r'<div class="tli(?:\s[^>]*)?">', seg):
        en = _match_div(seg, m.start())
        if en >= len(seg): break
        items.append(seg[m.start():en])
    if not items: return head
    newest = items[0]
    rest = items[1:]
    if d:
        today = '%s-%s' % (d[4:6], d[6:8])
        rest = [t for t in rest if _tli_date(t) >= today]
    out = head + '\n<div class="tl">%s</div>' % newest
    if rest:
        out += ('<details class="chain tlfold"><summary><b>当日更多认知</b> '
                '<span class="chip">%d条</span> <span class="mut">%s ~ %s</span></summary>'
                '<div class="inner"><div class="tl">%s</div></div></details>\n'
                % (len(rest), _tli_date(rest[-1]), _tli_date(rest[0]), ''.join(rest)))
    return out

def r_gap_card(d):
    """当日无 cycle body → 断档卡(事实陈述, 不编造判断)"""
    return ('<div class="card" style="border-color:rgba(255,95,86,.35)"><b>⚠ 当日未产周期情绪复盘 body</b>'
            '<p style="margin:6px 0 0">%s 晚间管道未产 judgment bodies.cycle, 判断板块(情绪阶段/攻防/自主深挖/认知迭代)当日无内容。'
            '机器数据(量能台阶/先行指标/连板梯队/五路投票)已按数据源如实渲染, 见上方折叠区。</p></div>\n' % d)

# ============ 拼装器 ============
def build_page(d):
    """LLM 七板块原文(有 body) 或 断档卡(无 body)"""
    body = load_body(d)
    if not body:
        return r_gap_card(d)
    return ''.join([r_vol(body), r_lead(body), r_stage(body),
                    r_ladder_llm(body), r_attack(body), r_scan(body), r_cog(body, d) + r_cog_lib('cycle', d)])

def build_page_full(d, paper_block=''):
    """完整页 body(头部区 + 机器数据折叠区 + 模拟盘看板 + 七板块) → S2 接线用
    头部区(bodies 开头 hero/kpi/stance)LLM 手写逐字节保真(有 body);
    无 body → 自产事实性头部(日期+断档提示), 不编造判断。
    机器区四卡收进 details.chain 折叠(默认收起) — 对齐 lhb/theme 验收基准:
      首屏=头部→模拟盘看板→七板块叙事流, 机器数字作核对层展开可见。
    锚点(VOLSTEP/LEADIND/LADDER/VOTEBOARD/PAPERTRADE)成对保留供哨兵核对"""
    body = load_body(d)
    if body:
        i2 = body.find('<h2>一')
        if i2 > 0:
            head = body[:i2]
            if not head.endswith('\n'): head += '\n'
        else:
            head = ''
    else:
        head = ('<div class="hero"><div class="kick">Cycle · 周期与情绪 · 截至 %s 收盘</div>'
                '<h1>周期情绪页 · %s 复盘未产, 数据断档如实呈现</h1>'
                '<p>机器数据(量能台阶/先行指标/连板梯队/五路投票)按数据源渲染; 判断板块缺 body 不编造。</p>'
                '<div class="stance"><span class="pill warn">状态 · <b class="s-weak">复盘断档</b></span></div></div>\n'
                % (d[4:6] + '-' + d[6:8], d[4:6] + '-' + d[6:8]))
    mach = ''.join([r_mach_volstep(d), r_mach_leadind(d), r_mach_ladder(d), r_mach_vote(d)])
    # ★2026-08-12 用户"为什么改变了我页面的样式": 黄金版 cycle 形态=hero+七板块直连,
    # 机器数据本就嵌在 LLM 七板块内(段一量能/段二先行指标/段三投票), 独立折叠区属我引入的样式改动。
    # → 有 body 日 mach 置空(黄金版形态); 折叠区仅无 body 断档日兜底(此时无黄金版对照)。
    if body:
        mach = ''
    elif mach.strip():
        chips = '<span class="chip">%d卡</span>' % mach.count('class="card"')
        mach = ('<details class="chain"><summary><b>机器数据源</b> %s '
                '<span class="mut">量能/先行指标/梯队/投票数字核对层 · 展开查看 · 判断以七板块为准</span></summary>'
                '<div class="inner">\n%s</div></details>\n' % (chips, mach))
    paper = ''
    if paper_block:
        paper = '<!--PAPERTRADE-->\n' + paper_block + '<!--/PAPERTRADE-->\n'
    return head + mach + paper + build_page(d)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '20260811'
    page = build_page_full(d)
    print('=== cycle 模块化渲染 @%s ===' % d)
    print('整页 body: %d KB | 卡%d 表%d 折叠%d h2:%d | 断档卡:%s' % (
        len(page) // 1024, page.count('class="card"'), page.count('<table'),
        page.count('<details'), len(re.findall(r'<h2>', page)),
        '⚠' in page and '未产' in page))
    print('机器锚: VOLSTEP=%s LEADIND=%s LADDER=%s MACHVOTE=%s | LLM 板块: 一二三四五六七=%s' % (
        page.count('<!--VOLSTEP-->') >= 1 and page.count('<!--/VOLSTEP-->') >= 1,
        page.count('<!--LEADIND-->') >= 1 and page.count('<!--/LEADIND-->') >= 1,
        page.count('<!--LADDER-->') >= 1 and page.count('<!--/LADDER-->') >= 1,
        page.count('<!--MACHVOTE-->') >= 1 and page.count('<!--/MACHVOTE-->') >= 1,
        ''.join('1' if k in page else '0' for k in
                ('<h2>一', '<h2>二', '<h2>三', '<h2>四', '<h2>五', '<h2>六', '<h2>七'))))
    if '--shell' in sys.argv:
        # 独立页面完整套壳: 从 SITE 全站页解析提取 shell(防编码乱码+组件缺失)
        site = os.path.join(os.path.dirname(os.path.abspath(__file__)), '复盘', '盯盘台')
        shell_src = os.path.join(site, 'cycle.html')
        if not os.path.isfile(shell_src):
            shell_src = os.path.join(site, 'lhb.html')
        shell = open(shell_src, encoding='utf-8').read()
        paper = os.path.join(L, '_模拟盘', 'cycle', '看板_%s.html' % d)
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
