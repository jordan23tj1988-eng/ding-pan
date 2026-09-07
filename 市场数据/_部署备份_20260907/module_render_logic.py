# -*- coding: utf-8 -*-
"""module_render_logic.py —— logic 页组件化渲染(2026-08-12, 模板=module_render_auction.py, 优化产业逻辑路)
读数据源 → 机器折叠区三卡(链条深度地图库/中报预增雷达漏斗/荐票历史结算, 数字可回源) + LLM body 原文 → 输出页面 body 片段
用法: python module_render_logic.py 20260812 [--out 路径] [--shell]
铁律: 机器卡数字只来自数据源文件(链条纵深库.json/链条位置_{板块}_{d}.json/中报预增雷达_{d}.json/
      _逻辑荐票结算.jsonl); LLM 区只从 judgment bodies['logic'] 提取原文, 不重写;
      数据缺失=显示"—"/断档标注, 零编造(不补造数字)。
黄金版(7/17)七段: 一荐票卡 二链条深度地图库(机器+LLM) 三逻辑硬度 四前置预期雷达
                  五中报预增雷达 六自主深挖 七认知迭代
★v4新body(8/12起)六段: 一荐票卡 二产业逻辑纯度 三中报预增 四链条纵深 五自主深挖 六认知迭代
  → 有 body 日: body 整段逐字节保真(两种格式都保真, 黄金版形态零插入);
    机器折叠区三卡(默认收起, 不抢叙事位置——★2026-08-12 theme 教训: 机器表卡不能抢占首屏叙事);
  → 无 body 日(如 8/11 晚间管道未产 logic body): 自产事实性 hero + 机器折叠区三卡(当日真实数据) + 断档卡。
★锚名防撞(2026-08-12 cycle 撞锚教训): 机器卡一律 MACHCHAIN/MACHRADAR/MACHHIST, 不与 body 内任何锚撞名。
"""
import re, os, sys, json
from collections import Counter, defaultdict

BASE = r'D:\股票数据\市场数据'
if not os.path.isdir(BASE):
    BASE = [p for p in ('/sessions/*/mnt/股票数据/市场数据',) if os.path.isdir(p)][0] if os.path.isdir('/sessions') else BASE
L = os.path.join(BASE, '_学习')
sys.path.insert(0, BASE)
from logic_pool import load_logic_picks
from _认知库渲染 import r_cog_lib

# ============ 数据契约加载 ============
def load_body(d):
    """LLM 区提取源: judgment_{d}.json bodies['logic']"""
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return ''
    try:
        return json.load(open(p, encoding='utf-8'))['bodies'].get('logic') or ''
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

def load_chain_lib():
    """链条纵深库.json → {链名: {首建,最后更新,位置快照,卡html}}; 缺=空 dict"""
    j = load_json('链条纵深库.json')
    return j if isinstance(j, dict) else {}

def load_settle():
    """_逻辑荐票结算.jsonl → list[dict] (按荐票日倒序; 过滤 null 均收占位条目)"""
    p = os.path.join(L, '_逻辑荐票结算.jsonl')
    if not os.path.exists(p): return []
    out = []
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l: continue
        try:
            j = json.loads(l)
        except Exception:
            continue
        out.append(j)
    out.sort(key=lambda x: str(x.get('荐票日', '')), reverse=True)
    return out

# ============ 通用 HTML 工具 ============
def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _pct(x, digits=1, signed=True):
    """小数→百分数字符串; None→'—'"""
    if x is None: return '—'
    return ('%+.' + str(digits) + 'f%%' if signed else '%.' + str(digits) + 'f%%') % (x * 100)

def _latest_chain_pos(d):
    """当日链条位置文件: 链条位置_{板块}_{d}.json 存在集合; 返回 (最新快照日期, [板块名])"""
    if not os.path.isdir(L): return None, []
    pat = re.compile(r'^链条位置_(.+)_(\d{8})\.json$')
    found = []
    for fn in os.listdir(L):
        m = pat.match(fn)
        if m:
            found.append((m.group(2), m.group(1)))
    cur = [(dd, nm) for dd, nm in found if dd <= str(d)]
    if not cur: return None, []
    latest = max(dd for dd, _ in cur)
    boards = [nm for dd, nm in cur if dd == latest]
    return latest, boards

# ============ 机器区: 链条深度地图库 ============
def r_mach_chain(d):
    """MACHCHAIN 注入: 链条纵深库.json 卡html 直嵌(黄金版717 details.chain 结构, 无 wrapper/h3/tl)
    黄金版段二 = <h2>后直接 <details class="chain"> 平铺; summary b 链名 + chip 状态;
    机器内容只加不删, 快照日期如实标注; 与 body 内 LLM 保鲜版并存互为核对"""
    lib = load_chain_lib()
    if not lib:
        return ''
    cards = ''
    for name, v in lib.items():
        h = v.get('卡html') or ''
        upd = v.get('最后更新') or '—'
        snap = v.get('位置快照') or '—'
        if not h:
            continue
        cards += ('<details class="chain" %s><summary><b>%s</b> <span class="chip cold">快照 %s</span>'
                  '<span class="mut">首建 %s · 位置 %s</span></summary><div class="inner">%s</div></details>\n'
                  % ('open' if cards == '' else '', _esc(name), _esc(upd[4:6] + '-' + upd[6:8] if len(upd) >= 8 else upd),
                     _esc(v.get('首建') or '—'), _esc(os.path.basename(str(snap))), h))
    if not cards:
        return ''
    # 当日链条位置文件最新日期(实测止0716=断更, 如实标注)
    latest, boards = _latest_chain_pos(d)
    pos_txt = ''
    if latest:
        pos_txt = ('<p class="mut" style="margin:4px 0 8px">链条位置快照最新止 %s(%s) · 距 %s 约 %d 个自然日, 位置引用为窗口数据</p>\n'
                   % (_esc(latest[4:6] + '-' + latest[6:8]), '、'.join(_esc(b) for b in boards),
                      _esc(d[4:6] + '-' + d[6:8]), _gap_days(latest, d)))
    head = '%s%s' % (pos_txt, cards)
    return '<!--MACHCHAIN-->\n%s<!--/MACHCHAIN-->\n' % head

def _gap_days(d1, d2):
    """YYYYMMDD 自然日差(粗略: 按月30天, 用于断更标注)"""
    from datetime import date
    try:
        a = date(int(d1[:4]), int(d1[4:6]), int(d1[6:8]))
        b = date(int(d2[:4]), int(d2[4:6]), int(d2[6:8]))
        return (b - a).days
    except Exception:
        return 0

# ============ 机器区: 中报预增雷达漏斗 ============
def r_mach_radar(d):
    """MACHRADAR 注入: 中报预增雷达_{d}.json 漏斗统计 + A共振池Top6(重要度分) obs 卡制
    对齐黄金版717段五: h2 后直接 <div class=card>(b 今晚漏斗 + p 漏斗链) + obs×6
    obs 卡 = obs-nm 名称+mut / obs-pos tag 重要度N·主类 / obs-lab 共振 / obs-lab2 原因;
    无 wrapper/h3/活跃线表格(黄金版无此组件); 缺当日文件 → 返回 ''"""
    r = load_json('中报预增雷达_%s.json', d)
    if not r:
        return ''
    st = r.get('统计') or {}
    def _n(k):
        v = st.get(k)
        return v if isinstance(v, (int, float)) else None
    pre, ex_st, unf, ovl = _n('预告池(净利润·预增扭亏)'), _n('剔ST退N/C'), _n('未发酵候选'), _n('其中概念叠加')
    a_n, b_n, c_n = _n('成色A共振'), _n('成色B概念蹭'), _n('成色C低质')
    filled = _n('已发酵(对照)')
    a_pool = r.get('A共振池(重要度排序)') or []
    fld = ('<div class="card"><b>今晚漏斗(%s刷新)</b><p style="margin:6px 0 0">'
           '预告池(净利润·预增扭亏)%s只 → 剔ST退N/C %s → 未发酵候选%s(r20&lt;15%%且近5日无涨停) → 概念叠加%s → '
           '<b>成色A共振 %s只</b>(B蹭%s/C低质%s留档); 已发酵(对照)%s(预期已兑现r250≥100%%剔%s只)。下面按重要度取前6只:</p></div>\n'
           % (_esc(d[4:6] + '-' + d[6:8]),
              pre if pre is not None else '—', ex_st if ex_st is not None else '—',
              unf if unf is not None else '—', ovl if ovl is not None else '—',
              a_n if a_n is not None else len(a_pool),
              b_n if b_n is not None else '—', c_n if c_n is not None else '—',
              filled if filled is not None else '—', _n('预期已兑现(r250≥100%)') if _n('预期已兑现(r250≥100%)') is not None else '—'))
    def _imp(x):
        if isinstance(x, dict):
            return x.get('重要度分') or x.get('重要度') or 0
        return 0
    top = sorted(a_pool, key=lambda x: -(_imp(x) if isinstance(x, dict) else 0))[:6]
    obs = ''
    for x in top:
        if not isinstance(x, dict): continue
        nm = x.get('名称') or x.get('股票名称') or '—'
        code = x.get('代码') or ''
        imp = x.get('重要度分') or x.get('重要度') or '—'
        cat = x.get('主类') or ''
        typ = x.get('预告类型') or ''
        chg = x.get('变动幅度%') or x.get('预增幅度') or '—'
        r20 = x.get('近20日涨幅%')
        r250 = x.get('r250')
        dh = x.get('距250日高%')
        lines = x.get('叠加线') or x.get('线') or x.get('概念叠加线') or ''
        if isinstance(lines, list):
            lines = '×'.join(str(s) for s in lines)
        words = x.get('成色依据') or x.get('动因词') or ''
        r20_t = ('%s%%' % r20) if isinstance(r20, (int, float)) else '—'
        r250_t = ('%s%%' % r250) if isinstance(r250, (int, float)) else '—'
        dh_t = ('%s%%' % dh) if isinstance(dh, (int, float)) else '—'
        reason = x.get('原因') or x.get('预增摘要') or '—'
        obs += ('<div class="obs"><div class="obs-head"><span class="obs-nm">%s <span class="mut">%s</span></span>'
                '<span class="obs-pos tag">重要度%s%s</span></div>'
                '<div class="obs-watch"><span class="obs-lab">共振</span>%s%s · r20 %s / r250 %s / 距高%s · 线=%s · %s</div>'
                '<div class="obs-rec"><span class="obs-lab2">原因</span>%s</div></div>\n'
                % (_esc(nm), _esc(code), _esc(str(imp)),
                   (' · %s' % _esc(cat)) if cat else '',
                   _esc(str(typ)), _esc(str(chg)), _esc(r20_t), _esc(r250_t), _esc(dh_t),
                   _esc(str(lines)), _esc(str(words))[:120], _esc(str(reason))[:260]))
    return '<!--MACHRADAR-->\n%s%s<!--/MACHRADAR-->\n' % (fld, obs)

# ============ 机器区: 荐票历史结算 ============
def r_mach_hist():
    """MACHHIST 卡: _逻辑荐票结算.jsonl 按类型聚合 n/胜率/均收(技能口径: 同类型样本<5须附'样本小不可外推')
    只统计已结算条目(执行均收非 null); 全空=返回 '' 如实缺"""
    rows = load_settle()
    if not rows:
        return ''
    agg = defaultdict(list)
    n_all, win_all, ret_all = 0, 0, 0.0
    for r_ in rows:
        if r_.get('执行均收') is None:
            continue  # 未结算占位条目(技能: 禁止引用)
        typ = r_.get('按类型') or {}
        for t, v in typ.items():
            if isinstance(v, (int, float)):
                agg[t].append(v)
        ws = str(r_.get('执行胜率') or '')
        if '/' in ws:
            try:
                w, n = ws.split('/')
                win_all += int(w); n_all += int(n)
            except Exception:
                pass
        ret_all += r_.get('执行均收') or 0.0
    t_rows = ''
    for t, vs in sorted(agg.items(), key=lambda kv: -len(kv[1])):
        if not vs: continue
        n = len(vs)
        avg = sum(vs) / n
        warn = ' <span class="mut">样本小不可外推</span>' if n < 5 else ''
        t_rows += ('<div class="trow"><div class="tr1"><span class="tnm">%s</span><span class="tct">n=%d</span>'
                   '<span class="%s">均收%s</span>%s</div></div>\n'
                   % (_esc(t), n, 'ok' if avg >= 0 else 'warn', _pct(avg / 100.0, 2), warn))
    if not t_rows:
        return ''
    head = ('<div class="card"><h3 style="margin:0 0 8px">荐票历史结算 <span class="hint">机器核对 · _逻辑荐票结算.jsonl · 按类型聚合(结算口径)</span></h3>'
            '<p style="margin:4px 0 8px" class="mut">已结算 n=%d · 执行胜率 %d/%d · 执行均收 %s</p>'
            '<div class="tl">%s</div></div>\n'
            % (len([r_ for r_ in rows if r_.get('执行均收') is not None]),
               win_all, n_all, _pct(ret_all / max(len([r_ for r_ in rows if r_.get('执行均收') is not None]), 1) / 100.0, 2), t_rows))
    return '<!--MACHHIST-->\n%s<!--/MACHHIST-->\n' % head

# ============ 机器折叠区组合 ============
def r_mach_fold(d):
    """三卡收进 details.chain 默认收起(不抢叙事位置; theme 8/12 教训)"""
    cards = [c for c in (r_mach_chain(d), r_mach_radar(d), r_mach_hist()) if c]
    if not cards:
        return ''
    chips = '<span class="chip">%d卡</span>' % len(cards)
    mach = ('<details class="chain"><summary><b>机器数据源</b> %s '
            '<span class="mut">链条地图/预增雷达/荐票结算数字核对层 · 展开查看 · 判断以正文为准</span></summary>'
            '<div class="inner">\n%s</div></details>\n' % (chips, ''.join(cards)))
    return mach

# ============ LLM 区: body 整段保真 ============
def build_components(d):
    """对齐 module_render_limitup/auction.build_components 接口(S3 组件快照回归 init/check 用)
    C1 链条深度地图库 / C2 中报预增雷达漏斗 / C3 荐票历史结算
    结构每日稳定(tagsig 不变), 数据每日变(content 变); 快照基准日=20260716(黄金版同日)"""
    def _strip(s):
        return ((s or '').replace('<!--MACHCHAIN-->', '').replace('<!--/MACHCHAIN-->', '')
                .replace('<!--MACHRADAR-->', '').replace('<!--/MACHRADAR-->', '')
                .replace('<!--MACHHIST-->', '').replace('<!--/MACHHIST-->', ''))
    return {
        'C1': _strip(r_mach_chain(d)),
        'C2': _strip(r_mach_radar(d)),
        'C3': _strip(r_mach_hist()),
        '_days': [str(d)],
        '_body': '',
    }

def r_gap_card(d):
    """当日无 logic body → 断档卡(事实陈述, 不编造判断)"""
    return ('<div class="card" style="border-color:rgba(255,95,86,.35)"><b>⚠ 当日未产产业逻辑复盘 body</b>'
            '<p style="margin:6px 0 0">%s 晚间管道未产 judgment bodies.logic, 判断板块(荐票卡/产业逻辑纯度/中报预增/链条纵深/自主深挖/认知迭代)当日无内容。'
            '机器数据(链条深度地图库/中报预增雷达/荐票历史结算)已按数据源如实渲染, 见上方折叠区。</p></div>\n' % d)

# ============ 板块一荐票卡(统一表格样式, 2026-08-13用户拍板) ============
def _match_div(s, start):
    """返回从 start 处 <div 开始的配平 </div> 结束位置(容错)"""
    depth = 0
    for m in re.finditer(r'<div\b|</div>', s[start:]):
        if m.group() == '</div>':
            depth -= 1
            if depth == 0:
                return start + m.end()
        else:
            depth += 1
    return len(s)

def _tli_date(tli):
    m = re.search(r'<b>(\d\d-\d\d)</b>', tli)
    if m: return m.group(1)
    m = re.search(r'<b>(\d{4})(\d{2})(\d{2})</b>', tli)
    return ('%s-%s' % (m.group(2), m.group(3))) if m else ''

def r_cog(body, d=None):
    """logic 认知段重装配(2026-08-16 方案A): 保留当日 tli 平铺, 丢弃 body 手写历史 tli(日期<d),
    历史统一由 r_cog_lib('logic', d) 从认知库注入(零编造回源)。整段 body 保真, 仅认知段历史切换数据源。"""
    if not d:
        return body
    sec = body.find('id="p6"')
    if sec < 0:
        sec = body.find('<h2>六 认知迭代')
        if sec < 0:
            return body
        s0 = sec
    else:
        s0 = body.rfind('<section', 0, sec)
        if s0 < 0:
            s0 = sec
    e0 = body.find('</section>', sec)
    if e0 < 0:
        e0 = len(body)
    seg = body[s0:e0]
    h2s = seg.find('<h2>')
    h2e = seg.find('</h2>', h2s) + len('</h2>') if h2s >= 0 else 0
    head = seg[:h2e]
    ts = seg.find('<div class="tl">', h2e)
    items = []
    if ts >= 0:
        te = _match_div(seg, ts)
        tl = seg[ts:te]
        for m in re.finditer(r'<div class="tli(?:\s[^>]*)?">', tl):
            en = _match_div(tl, m.start())
            if en > m.start():
                items.append(tl[m.start():en])
    today = '%s-%s' % (d[4:6], d[6:8])
    items = [t for t in items if _tli_date(t) >= today]
    tl_block = '<div class="tl">%s</div>' % ''.join(items) if items else ''
    hist = r_cog_lib('logic', d)
    return body[:s0] + head + '\n' + tl_block + hist + body[e0:]

def _strip_obs(seg, rec_codes=None):
    """逐卡剔除 <div class="obs">...</div>(配平嵌套div)。
    rec_codes 非空: 只剔除代码∈rec_codes 的荐票 obs 卡(荐票表已表达), 保留观察级 obs 卡;
    rec_codes 空/None: 全部保留(空仓/仅观察, 观察级是判断内容)。"""
    if not rec_codes:
        return seg
    out = []
    i = 0
    while True:
        s = seg.find('<div class="obs">', i)
        if s < 0:
            out.append(seg[i:])
            break
        out.append(seg[i:s])
        e = _match_div(seg, s)
        r = _parse_obs_row(seg[s:e])
        code = (r[1] or '').zfill(6) if r else ''
        if code not in rec_codes:
            out.append(seg[s:e])
        i = e
    return ''.join(out)

def _strip_card(seg, kw):
    """剔除含 kw 的 card(洞察卡搬移防重复用)"""
    out = seg
    while True:
        i = out.find(kw)
        if i < 0:
            break
        cs = out.rfind('<div class="card', 0, i)
        if cs < 0:
            break
        ce = _match_div(out, cs)
        out = out[:cs] + out[ce:]
    return out

def _parse_obs_row(seg):
    """解析单张obs卡 → (名称, 代码, 类型, 逻辑, 历史对照); 失败返回None(零编造)"""
    try:
        ns = seg.find('class="obs-nm">')
        if ns < 0:
            return None
        nm_rest = seg[ns + len('class="obs-nm">'):]
        depth = 1  # obs-nm 自身的 span 已开启, 内嵌 mut span 需配对后闭合
        end = -1
        for m in re.finditer(r'<span|</span>', nm_rest):
            if m.group() == '</span>':
                depth -= 1
                if depth == 0:
                    end = m.start()
                    break
            else:
                depth += 1
        raw = nm_rest[:end] if end > 0 else nm_rest
        code = ''
        mcode = re.search(r'<span class="mut">([^<]+)</span>', raw)
        if mcode:
            code = mcode.group(1).strip()
            name = re.sub(r'<span class="mut">.*?</span>', '', raw, flags=re.S).strip()
        else:
            name = raw.strip()
        typ = re.search(r'class="obs-pos[^"]*">([^<]+)<', seg)
        typ = typ.group(1).strip() if typ else ''
        w = re.search(r'<div class="obs-watch">(.*?)</div>', seg, re.S)
        logic = re.sub(r'<[^>]+>', '', w.group(1)).strip() if w else ''
        r_ = re.search(r'<div class="obs-rec">(.*?)</div>', seg, re.S)
        hist = re.sub(r'<[^>]+>', '', r_.group(1)).strip() if r_ else ''
        if not name:
            return None
        return (name, code, typ, logic, hist)
    except Exception:
        return None

def r_reco_table(d, body, picks, src):
    """板块一荐票表: picks=load_logic_picks 荐票类型标的(新契约 logic判断 优先, 旧契约 逻辑荐票 fallback);
    picks 非空 → 荐票表; picks 空 + src 有(新契约明确空仓) → 返回空串(结论卡+观察级obs卡由 seg2 保留);
    src 无(旧日期无发出版) → 从 body obs 卡解析兜底(兼容黄金版, 如实hint 不编造)"""
    if picks:
        rows = []
        for i, x in enumerate(picks, 1):
            nm = _esc(str(x.get('名称', '')))
            code = _esc(str(x.get('代码', '')))
            typ = _esc(str(x.get('类型') or '荐票'))
            chain = _esc(str(x.get('链条', '')))
            link = _esc(str(x.get('环节', '')))
            reason = _esc(str(x.get('理由', '')))
            hist = _esc(str(x.get('历史对照', '')))
            rows.append(('<tr><td>%d</td>'
                         '<td style="white-space:nowrap"><b>%s</b><br><span class="mut">%s</span></td>'
                         '<td style="white-space:nowrap"><b>%s</b></td>'
                         '<td style="word-break:break-word">%s%s%s</td>'
                         '<td style="word-break:break-word"><span class="mut" style="font-size:11px">%s</span></td></tr>')
                        % (i, nm, code, typ,
                           ('[%s] ' % chain) if chain else '',
                           ('·%s ' % link) if link else '',
                           reason, hist))
        hint = ('<div class="hint">发出版不可覆盖(%s(发出版)); 荐票=兑现逻辑可结算化≠确认; 结算=兑现口径</div>' % src)
        table = ('<div class="card"><table style="table-layout:fixed;width:100%%"><colgroup>'
                 '<col style="width:24px"><col style="width:104px"><col style="width:80px"><col><col style="width:170px"></colgroup>'
                 '<tr><th>#</th><th>标的</th><th>类型</th><th>逻辑(链条·环节·理由)</th><th>同类历史</th></tr>%s</table></div>' % ''.join(rows))
        return table + chr(10) + hint
    if src:
        return ''
    # src 无 → 旧日期 obs 兜底(兼容黄金版 7/16 等无发出版的 body)
    rows = []
    obs_rows = []
    p1, p2 = body.find('<h2>一'), body.find('<h2>二', body.find('<h2>一') + 5)
    zone = body[p1:p2 if p2 > 0 else len(body)]
    for m in re.finditer(r'<div class="obs">', zone):
        e = _match_div(zone, m.start())
        obs_rows.append(zone[m.start():e])
    for i, seg in enumerate(obs_rows, 1):
        r = _parse_obs_row(seg)
        if not r:
            continue
        name, code, typ, logic, hist = r
        rows.append(('<tr><td>%d</td>'
                     '<td style="white-space:nowrap"><b>%s</b><br><span class="mut">%s</span></td>'
                     '<td style="white-space:nowrap">%s</td>'
                     '<td style="word-break:break-word">%s</td>'
                     '<td style="word-break:break-word"><span class="mut" style="font-size:11px">%s</span></td></tr>')
                    % (i, _esc(name), _esc(code), _esc(typ), _esc(logic), _esc(hist)))
    if not rows:
        return ('<div class="card" style="border-color:rgba(255,95,86,.35)"><b>⚠ 荐票发出版缺失</b>'
                '<p style="margin:6px 0 0">发出版文件不存在且body无荐票卡——荐票表如实空缺(零编造)。</p></div>')
    hint = ('<div class="hint">⚠ 发出版缺失(当晚未落盘)——以下表格由agent手写obs卡照转, '
            '如实呈现待补产; 结算口径不变(兑现口径)</div>')
    table = ('<div class="card"><table style="table-layout:fixed;width:100%%"><colgroup>'
             '<col style="width:24px"><col style="width:104px"><col style="width:80px"><col><col style="width:170px"></colgroup>'
             '<tr><th>#</th><th>标的</th><th>类型</th><th>逻辑(链条·环节·理由)</th><th>同类历史</th></tr>%s</table></div>' % ''.join(rows))
    return table + chr(10) + hint

def r_insight(body):
    """提取"洞察(agent)"卡原文(bodies 任意位置→搬至荐票卡下方); 无=空(如实)"""
    i = body.find('洞察(agent)')
    if i < 0:
        return ''
    cs = body.rfind('<div class="card', 0, i)
    if cs < 0:
        return ''
    ce = _match_div(body, cs)
    return body[cs:ce] + (chr(10) if body[ce:ce + 1] == chr(10) else '')

# ============ 拼装器 ============
def build_page_full(d, paper_block=''):
    """完整页 body → S2 接线用
    有 body 日(黄金版七段骨架, convert_812_body_golden_logic.py 重建):
        body 整段保真 + 机器空锚注入(MACHCHAIN→段二链条库 / MACHRADAR→段五中报预增;
        锚内有内容=历史注入卡, 保真铁律不动) + PAPERTRADE 看板(插 h2一 前)
    无 body 日: 自产事实性 hero(日期+断档提示, 禁旧日期) + 机器折叠区三卡(当日真实数据) + 断档卡
    锚点(MACHCHAIN/MACHRADAR/MACHHIST/PAPERTRADE)成对保留供哨兵核对"""
    body = load_body(d)
    paper = ''
    if paper_block:
        paper = '<!--PAPERTRADE-->\n' + paper_block + '<!--/PAPERTRADE-->\n'
    if body:
        out = body.rstrip('\n') + '\n'
        # ★2026-08-16 方案A: 认知段历史从手写切换认知库注入(整段保真, 仅历史折叠区数据源切换)
        out = r_cog(out, d)
        # ★2026-08-13 用户拍板: 板块一重组=荐票卡(表格)第一项 + 洞察(agent) + 剩余(obs卡剔除)
        # ★2026-08-14 方案B: 荐票表只渲染"荐票"类型(load_logic_picks), 观察级 obs 卡保留
        _picks, _src = load_logic_picks(d, L)
        _rec_codes = set(str(x.get('代码', '')).zfill(6) for x in _picks if x.get('代码'))
        i1 = out.find('<h2>一')
        if i1 >= 0:
            e1 = out.find('</h2>', i1)
            i2 = out.find('<h2>二', i1)
            seg = out[e1 + 5:i2 if i2 > 0 else len(out)]
            seg2 = _strip_card(_strip_obs(seg, _rec_codes), '洞察(agent)')
            head = _strip_card(out[:e1 + 5], '洞察(agent)')
            out = head + '\n' + r_reco_table(d, body, _picks, _src) + r_insight(body) + seg2 + (out[i2:] if i2 > 0 else '')
        # ★S2(2026-08-12 补, 对齐 auction): 机器卡注入——body 里管道预留空锚
        #   <!--MACHCHAIN-->(链条深度地图库) <!--MACHRADAR-->(中报预增雷达)
        #   空锚=注入点→填对应机器卡(卡自身 MACH 锚剥掉防哨兵撞锚);
        #   锚内有内容(7/16黄金版原文历史注入卡)=保真铁律, 一律不动。
        inj = [('MACHCHAIN', r_mach_chain(d)), ('MACHRADAR', r_mach_radar(d))]
        for an, fn in inj:
            card = fn or ''
            if not card:
                continue
            for a in ('MACHCHAIN', 'MACHRADAR', 'MACHHIST'):
                card = card.replace('<!--%s-->' % a, '').replace('<!--/%s-->' % a, '')
            s = out.find('<!--%s-->' % an)
            if s >= 0:
                e = out.find('<!--/%s-->' % an, s)
                if e > s and not out[s + len('<!--%s-->' % an):e].strip():
                    out = out[:s] + '<!--%s-->' % an + card + out[e:]
        if not out.endswith('\n'):
            out += '\n'
        if paper:
            i2 = out.find('<h2>一')
            if i2 > 0:
                out = out[:i2] + paper + out[i2:]
            else:
                out = out + paper
        return out
    head = ('<div class="rowA"><div class="hero"><div class="kick">Logic · 产业逻辑 · 第4路 · 截至 %s 收盘</div>'
            '<h1>产业逻辑页 · %s 复盘未产, 数据断档如实呈现</h1>'
            '<p>机器数据(链条深度地图库/中报预增雷达/荐票历史结算)按数据源渲染; 判断板块缺 body 不编造。</p>'
            '<div class="stance"><span class="pill warn">状态 · <b class="s-weak">复盘断档</b></span></div></div></div>\n'
            % (d[4:6] + '-' + d[6:8], d[4:6] + '-' + d[6:8]))
    mach = r_mach_fold(d)
    mach_open = ''
    if mach:
        # 无 body 日: 折叠区改为展开(唯一内容来源)
        mach_open = mach.replace('<details class="chain"><summary><b>机器数据源</b>',
                                 '<details class="chain" open><summary><b>机器数据源</b>')
    return head + mach_open + paper + r_gap_card(d)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '20260812'
    page = build_page_full(d)
    print('=== logic 模块化渲染 @%s ===' % d)
    print('整页 body: %d KB | 卡%d 表%d 折叠%d h2:%d | 断档卡:%s' % (
        len(page) // 1024, page.count('class="card"'), page.count('<table'),
        page.count('<details'), len(re.findall(r'<h2>', page)),
        '⚠' in page and '未产' in page))
    print('机器锚: MACHCHAIN=%s MACHRADAR=%s MACHHIST=%s | body保真:%s' % (
        page.count('<!--MACHCHAIN-->') == 1 and page.count('<!--/MACHCHAIN-->') == 1,
        page.count('<!--MACHRADAR-->') == 1 and page.count('<!--/MACHRADAR-->') == 1,
        page.count('<!--MACHHIST-->') == 1 and page.count('<!--/MACHHIST-->') == 1,
        '<div class="rowA">' in page))
    if '--shell' in sys.argv:
        # 独立页面完整套壳: 从 SITE 全站页解析提取 shell(防编码乱码+组件缺失)
        site = os.path.join(BASE, '复盘', '盯盘台')
        shell_src = os.path.join(site, 'logic.html')
        if not os.path.isfile(shell_src):
            shell_src = os.path.join(site, 'lhb.html')
        shell = open(shell_src, encoding='utf-8').read()
        paper = os.path.join(L, '_模拟盘', 'logic', '看板_%s.html' % d)
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
