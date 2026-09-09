# -*- coding: utf-8 -*-
"""module_render_auction.py —— auction 页组件化渲染(2026-08-12, 模板=module_render_cycle.py, 修复竞价路)
读数据源 → 机器区三卡(竞价选股池/昨池结算/信号胜率库, 数字可回源) + LLM body 原文 → 输出页面 body 片段
用法: python module_render_auction.py 20260811 [--out 路径] [--shell]
铁律: 机器卡数字只来自数据源文件(竞价评分_{d}.json/竞价池发出_{d}.json/竞价池结算_{d}.json/
      _竞价池结算.jsonl/_市场温度表.json/黄金版段四静态库原文);
      LLM 区只从 judgment bodies['auction'] 提取原文, 不重写;
      数据缺失=显示"—"/断档标注, 零编造(不补造数字)。
六段(2026-08-16 改六段对齐其他路): 一竞价选股池(SCORECARD机器锚) 二今日竞价温度
                  三昨日池(POOLLEDGER机器锚) 四信号胜率追踪(MACHSIG机器卡) 五自主深挖 六认知迭代
★2026-08-16 竞价路改六段: 盘中竞价强势(原★今晨闸门/★今晨初读两段)移出竞价页→盘中作战页,
  渲染时清理历史八段 body 残留的闸门/初读段(含空锚), 早盘脚本不再注入 judgment auction。
  → 有 body 日: body 整段保真(先清理闸门/初读段), 机器卡注入空锚;
  → 无 body 日(晚间管道未产 auction body): 自产事实性 hero + 机器折叠区三卡(当日真实数据) + 断档卡。
★锚名防撞(2026-08-12 cycle 撞锚教训): 黄金版 body 自带 <!--SCORECARD-->/<!--POOLLEDGER--> 锚
  (LLM原文保真不动), 机器折叠区卡若同名 → 有 body 日锚起2/止2 哨兵强制唯一 FAIL
  → 机器卡改名 MACHSCORE/MACHPOOL/MACHSIG。
"""
import re, os, sys, json, csv
from collections import Counter
from _认知库渲染 import r_cog_lib, inject_into_section

BASE = r'D:\股票数据\市场数据'
if not os.path.isdir(BASE):
    BASE = [p for p in ('/sessions/*/mnt/股票数据/市场数据',) if os.path.isdir(p)][0] if os.path.isdir('/sessions') else BASE
L = os.path.join(BASE, '_学习')
GOLDEN = r'D:\黄金对照版717\auction.html'   # 黄金版段四(信号胜率库)静态原文提取源; 库 20260716 重算后未变, 保真=当前真实状态

# ============ 数据契约加载 ============
def load_body(d):
    """LLM 区提取源: judgment_{d}.json bodies['auction']"""
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return ''
    try:
        return json.load(open(p, encoding='utf-8'))['bodies'].get('auction') or ''
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

def load_发出(d):
    """竞价池发出_{d}.json → dict or None (发出版冻结名单, 零后视镜确定性池)"""
    return load_json('竞价池发出_%s.json', d)

def load_评分(d):
    """竞价评分_{d}.json → dict or None (评分卡: 竞价分/主导因子/情景桶值/闸门预标)"""
    return load_json('竞价评分_%s.json', d)

def load_结算(d):
    """竞价池结算_{d}.json → dict or None (明细含 T1高开/执行收益/判定)"""
    return load_json('竞价池结算_%s.json', d)

def load_结账():
    """_竞价池结算.jsonl → list[dict] (历史汇总, 过滤未结算占位条目: 执行胜率0/0 或 均收null)"""
    p = os.path.join(L, '_竞价池结算.jsonl')
    if not os.path.exists(p): return []
    out = []
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l: continue
        try:
            j = json.loads(l)
        except Exception:
            continue
        if j.get('执行胜率') in ('0/0', None) and j.get('执行均收') is None:
            continue  # 未结算占位条目(技能: 禁止引用)
        if j.get('执行均收') is None:
            continue
        out.append(j)
    out.sort(key=lambda x: str(x.get('池日', '')), reverse=True)
    return out

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

def _pct(x, digits=1, signed=True):
    """小数→百分数字符串; None→'—'"""
    if x is None: return '—'
    return ('%+.' + str(digits) + 'f%%' if signed else '%.' + str(digits) + 'f%%') % (x * 100)

def _f1(x):
    """数值→1位小数字符串; None→'—'"""
    if x is None: return '—'
    return ('%+.1f' % x)

def _f2(x):
    """数值→2位小数字符串(结算均收用, 对齐黄金版'1.56%'); None→'—'"""
    if x is None: return '—'
    return ('%+.2f' % x)

# ============ 机器区: 竞价选股池评分卡 ============
def _factor_short(f):
    """主导因子 '封单比=<0.5%(+8.4,桶均涨0.89%,n=271)' → '封单比=<0.5%'"""
    m = re.match(r'^([^=]+)=([^,(]+)', str(f))
    return (m.group(1) + '=' + m.group(2)) if m else str(f)[:24]

def r_mach_score(d):
    """MACHSCORE 卡: 竞价选股池(评分表 or 发出版确定性名单回退)
    源1=竞价评分_{d}.json 明细(黄金版段一表格同构: 标的/信号/竞价分/主导因子/若低开/若高开0~5/若高开≥5)
    源2(无评分)=竞价池发出_{d}.json 确定性名单(代码/名称/首封/连板/信号/封单比/炸板)
    都无 → None(折叠区省略该卡)"""
    sc = load_评分(d)
    if sc and sc.get('明细'):
        tmp = sc.get('温度')
        ttxt = '%s' % tmp if tmp is not None else '—'
        head = ('<b>%s竞价池评分(%d只,温度%s·%s)</b> <span class="mut">%s</span>'
                % (d[4:6] + '-' + d[6:8], len(sc['明细']), ttxt,
                   _esc(str(sc.get('温度档', '—'))),
                   _esc(str(sc.get('口径', ''))[:120])))
        rows = ''
        for r in sc['明细']:
            s = r.get('信号') or '—'
            zb = r.get('炸板')
            sig = '%s·炸%d' % (s, zb) if zb else s
            fbr = r.get('封单比')
            sig2 = ('封%0.2f%%' % fbr) if isinstance(fbr, (int, float)) else '封—'
            scn = r.get('情景') or {}
            lo = scn.get('低开') or {}
            mid = scn.get('高开0~5') or {}
            hi = scn.get('高开≥5') or {}
            def cell(dic):
                if not dic: return '<td style="white-space:nowrap">—</td>'
                return '<td style="white-space:nowrap">%s/%s</td>' % (_f1(dic.get('均涨')), dic.get('胜率', '—'))
            facs = r.get('主导因子') or []
            fac = '、'.join(_factor_short(f) for f in facs[:2]) or '—'
            rows += ('<tr><td><b>%s</b><br><span class="mut">%s</span></td>'
                     '<td>%s<br><span class="mut">%s</span></td>'
                     '<td style="white-space:nowrap"><b>%s</b></td>'
                     '<td>%s</td>%s%s'
                     '<td style="white-space:nowrap" class="dC">%s/%s弃</td></tr>\n'
                     % (_esc(r.get('名称', '—')), _esc(r.get('代码', '')), _esc(sig), _esc(sig2),
                        _f1(r.get('竞价分')), _esc(fac),
                        cell(lo), cell(mid),
                        _f1(hi.get('均涨')), hi.get('胜率', '—')))
        tail = '<p style="margin:6px 0 0" class="mut">闸门: 高开≥5%%历史必弃; 桶均值非个股预言, 池原样追开盘非alpha。</p>'
        card = ('<!--MACHSCORE-->\n<div class="card">%s'
                '<table style="table-layout:fixed"><colgroup><col style="width:15%%"><col style="width:17%%">'
                '<col style="width:9%%"><col style="width:20%%"><col style="width:13%%"><col style="width:13%%"><col style="width:13%%"></colgroup>'
                '<tr><th>标的</th><th>信号</th><th>竞价分</th><th>主导因子</th><th>若低开</th><th>若高开0~5</th><th>若高开≥5</th></tr>%s</table>%s</div>\n<!--/MACHSCORE-->\n'
                % (head, rows, tail))
        return card
    fc = load_发出(d)
    if fc and fc.get('池'):
        t, _ = load_temp(d)
        cur = None
        if t:
            days = sorted(k for k in t if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
            if days: cur = t[days[-1]]
        ttxt = ''
        if cur:
            tmp = cur.get('温度')
            ttxt = '温度%s·%s' % (tmp, cur.get('温度档')) if tmp is not None else '温度档%s' % cur.get('温度档')
        head = ('<b>%s竞价池发出(%d只,发出版冻结名单%s)</b> <span class="mut">%s</span>'
                % (d[4:6] + '-' + d[6:8], len(fc['池']), ('·' + ttxt) if ttxt else '',
                   _esc(str(fc.get('口径', ''))[:120])))
        rows = ''
        for r in fc['池']:
            fbr = r.get('封单比')
            rows += ('<tr><td><b>%s</b><br><span class="mut">%s</span></td>'
                     '<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n'
                     % (_esc(r.get('名称', '—')), _esc(r.get('代码', '')),
                        _esc(r.get('信号', '—')), _esc(str(r.get('首封', '—'))),
                        _esc(str(r.get('连板', '—'))),
                        ('%0.2f%%' % fbr) if isinstance(fbr, (int, float)) else '—',
                        _esc(str(r.get('炸板', '—')))))
        card = ('<!--MACHSCORE-->\n<div class="card">%s'
                '<table><tr><th>名称</th><th>信号</th><th>首封</th><th>连板</th><th>封单比</th><th>炸板</th></tr>%s</table>'
                '<p style="margin:6px 0 0" class="mut">无竞价评分文件(晚间管道未产), 显示发出版确定性名单; 明晨按9:25实开走闸门: 高开≥5%%历史必弃。</p></div>\n<!--/MACHSCORE-->\n'
                % (head, rows))
        return card
    return None

# ============ 机器区: 昨池结算台账 ============
def r_mach_pool(d):
    """MACHPOOL 卡: 昨日池终结算台账
    源1=竞价池结算_{d}.json 明细(最新日展开: 标的/信号/T1高开/执行收益/判定)
    源2=_竞价池结算.jsonl 历史汇总(更早折叠, 占位条目已过滤)
    都无 → None"""
    # 最新池日 = 扫描最新结算文件(结算文件按池日命名; 复盘日 d ≠ 最新池日, 2026-08-15 修复)
    _pf = sorted(f for f in os.listdir(L) if f.startswith('竞价池结算_') and f.endswith('.json'))
    latest = _pf[-1].replace('竞价池结算_', '').replace('.json', '') if _pf else d
    cur = load_结算(latest)
    hist = load_结账()
    if cur is None and not hist:
        return None
    if cur:
        det = cur.get('明细') or []
        sum_ = cur.get('汇总') or {}
        rows = ''
        for r in det:
            ok = '✓封' if r.get('次日封板') else '✗败'
            cl = 'color:#4caf7d' if r.get('次日封板') else 'color:#e56060'
            hi_ = r.get('T1高开')
            rows += ('<tr><td><b>%s</b><br><span class="mut">%s</span></td>'
                     '<td>%s</td><td>%s</td><td>%s</td>'
                     '<td style="white-space:nowrap">%s</td><td style="white-space:nowrap">%s</td>'
                     '<td style="white-space:nowrap;%s">%s</td></tr>\n'
                     % (_esc(r.get('名称', '—')), _esc(r.get('代码', '')),
                        _esc(r.get('信号', '—')), _esc(str(r.get('首封', '—'))),
                        _esc(str(r.get('连板', '—'))),
                        _f1(hi_) + '%', _f1(r.get('执行收益')) + '%', cl,
                        _esc(str(r.get('判定', ok)))))
        main = ('<details class="chain" open><summary><b>%s池终结算</b> <span class="chip">最新</span> '
                '<span class="mut">池%d只 · 封板%s · 胜率%s · 均收%s</span></summary><div class="inner">'
                '<div class="card"><table><tr><th>标的</th><th>信号</th><th>首封</th><th>连板</th><th>T1高开</th><th>执行收益</th><th>判定</th></tr>%s</table></div></div></details>\n'
                % (latest[4:6] + '-' + latest[6:8], len(det),
                   _esc(str(sum_.get('次日封板', '—'))), _esc(str(sum_.get('执行胜率', '—'))),
                   _f2(sum_.get('执行均收')) + '%', rows))
    else:
        main = ''
    older = [h for h in hist if str(h.get('池日', '')) != str(latest)]
    if older:
        rows = ''
        for h in older:
            rows += ('<tr><td><b>%s</b></td><td>池%d只</td><td>封板%s</td><td>胜率%s</td><td>均收%s</td></tr>\n'
                     % (h['池日'][4:6] + '-' + h['池日'][6:8], h.get('池家数', '—'),
                        _esc(str(h.get('次日封板', '—'))), _esc(str(h.get('执行胜率', '—'))),
                        _f1(h.get('执行均收')) + '%'))
        fold = ('<details class="chain foldarchive"><summary><b>更早存档</b> <span class="chip">%d条</span> '
                '<span class="mut">%s ~ %s</span></summary><div class="inner">'
                '<div class="card"><table><tr><th>池日</th><th>家数</th><th>次日封板</th><th>执行胜率</th><th>执行均收</th></tr>%s</table></div></div></details>\n'
                % (len(older), older[-1]['池日'][4:6] + '-' + older[-1]['池日'][6:8],
                   older[0]['池日'][4:6] + '-' + older[0]['池日'][6:8], rows))
    else:
        fold = ''
    card = ('<!--MACHPOOL-->\n<div class="hint">台账式归档:最新结算展开,历史折叠(只加不删);数据=竞价池结算_{d}.json/_竞价池结算.jsonl(脚本产出,agent不改数)。池=发出版冻结名单,执行口径=T+1开→T+1收。</div>%s%s<!--/MACHPOOL-->\n' % (main, fold))
    return card

# ============ 机器区: 信号胜率库(黄金版段四静态原文) ============
def r_mach_sig():
    """MACHSIG 卡: 四 竞价信号胜率追踪
    数据源=黄金版717 auction.html 段四原文(一年分桶库 n=2905, 20260716 重算后未变;
    静态库保真=当前真实状态, chip 明示重算日; 不重造表格避免多源映射错位)"""
    try:
        g = open(GOLDEN, encoding='utf-8').read()
    except Exception:
        return None
    i4 = g.find('<h2>四')
    i5 = g.find('<h2>五')
    if i4 < 0 or i5 < 0 or i5 < i4:
        return None
    seg = g[i4:i5]
    return '<!--MACHSIG-->\n%s<!--/MACHSIG-->\n' % seg

# ============ 组件化接口(S3 组件快照回归, 2026-08-12): 机器组件区, 结构每日稳定 ============
def _c1_temp(d):
    """C1 温度卡: .gauge 组件(组件规范#7) + 涨停/炸板/最高板/量能读数
    结构每日稳定(tagsig 不变): 缺数据时显示 '—' 但标签序列保留"""
    t, days = load_temp(d)
    cur = t[days[-1]] if days else None
    tmp = cur.get('温度') if cur else None
    dg = cur.get('温度档') if cur else None
    gv = ('%s' % tmp) if tmp is not None else '—'
    pct = tmp if isinstance(tmp, (int, float)) else 0.0
    gmark = '<i class="gmark" style="left:%s%%"></i>' % min(100.0, max(0.0, pct))
    seg = ('<div class="gauge"><div class="gv">%s <span class="mut">%s</span></div>'
           '<div class="gtrack">%s</div>'
           '<div class="gl"><span>冰点</span><span>偏冷</span><span>中性</span><span>偏热</span><span>过热</span></div></div>\n'
           % (gv, _esc(str(dg)) if dg else '—', gmark))
    zt = cur.get('涨停数') if cur else None
    zb = cur.get('炸板率') if cur else None
    gb = cur.get('最高板') if cur else None
    lj = cur.get('成交额亿') if cur else None
    s = lambda x: ('%s' % x) if x is not None else '—'
    kv = ('<div class="kv"><div class="l">涨停</div><div class="v">%s</div></div>\n'
          '<div class="kv"><div class="l">炸板率</div><div class="v">%s</div></div>\n'
          '<div class="kv"><div class="l">最高板</div><div class="v">%s</div></div>\n'
          '<div class="kv"><div class="l">量能</div><div class="v">%s亿</div></div>\n'
          % (s(zt), ('%.1f%%' % (zb * 100)) if isinstance(zb, (int, float)) else '—',
             s(gb), s(lj)))
    return '<div class="card"><b>当日温度</b>\n' + seg + kv + '</div>\n'

def build_components(d):
    """对齐 module_render_limitup.build_components 接口(S3 组件快照回归 init/check 用)
    C1 评分表(段一 SCORECARD) / C2 结算(段三 POOLLEDGER) / C3 信号库(段四 MACHSIG)
    结构=黄金版同构(标签结构特征一致), 数据每日变(content 变); 快照基准日=20260716(黄金版同日)"""
    def _strip(s):
        for a in ('MACHPOOL', 'MACHSCORE', 'MACHSIG'):
            s = (s or '').replace('<!--%s-->' % a, '').replace('<!--/%s-->' % a, '')
        return s
    return {
        'C1': _strip(r_mach_score(d)),
        'C2': _strip(r_mach_pool(d)),
        'C3': _strip(r_mach_sig()),
        '_days': [str(d)],
        '_body': '',
    }

# ============ LLM 区 ============
def r_gap_card(d):
    """当日无 auction body → 断档卡(事实陈述, 不编造判断)"""
    return ('<div class="card" style="border-color:rgba(255,95,86,.35)"><b>⚠ 当日未产竞价复盘 body</b>'
            '<p style="margin:6px 0 0">%s 晚间管道未产 judgment bodies.auction, 判断板块(荐票/竞价全景/高标承接/自主深挖/认知迭代)当日无内容。'
            '机器数据(竞价选股池/昨池结算/信号胜率库)已按数据源如实渲染, 见上方折叠区。</p></div>\n' % d)

# ============ 拼装器 ============
def _dig2card(seg):
    """2026-08-15: auction 五段自造 dig/dig-card(无CSS→文字裸奔) → 黄金版 card(有CSS), 对齐 lhb 五段"""
    def _conv(m):
        bm = re.match(r'\s*<b>(.*?)</b>\s*<span>(.*?)</span>\s*', m.group(1), re.S)
        if not bm:
            return m.group(0)
        return ('<div class="card"><b>%s</b><p style="margin:6px 0 0">%s</p></div>'
                % (bm.group(1).strip(), bm.group(2).strip()))
    return re.sub(r'<div class="dig-card">(.*?)</div>', _conv, seg, flags=re.S)


def _iter2tl(seg, d):
    """2026-08-15: auction 六段自造 iter/iter-card(无CSS) → 黄金版 tl 时间线(有CSS), 对齐 lhb 六段"""
    def _conv(m):
        bm = re.match(r'\s*<b>(.*?)</b>\s*<span>(.*?)</span>\s*', m.group(1), re.S)
        if not bm:
            return m.group(0)
        return ('<div class="tli"><div class="d"><b>%s</b></div>'
                '<div class="h">%s</div><div class="b">%s</div></div>'
                % (d, bm.group(1).strip(), bm.group(2).strip()))
    seg = re.sub(r'<div class="iter-card">(.*?)</div>', _conv, seg, flags=re.S)
    return seg.replace('<div class="iter">', '<div class="tl">')


def build_page_full(d, paper_block=''):
    """完整页 body → S2 接线用
    有 body 日: body 整段逐字节保真(黄金版形态零插入; body 自带 SCORECARD/POOLLEDGER 机器锚=历史注入产物)
    无 body 日: 自产事实性 hero(日期+断档提示, 禁旧日期) + 机器折叠区三卡(当日真实数据, MACHSCORE/MACHPOOL/MACHSIG) + 断档卡
    锚点(PAPERTRADE 等)成对保留供哨兵核对"""
    body = load_body(d)
    paper = ''
    if paper_block:
        paper = '<!--PAPERTRADE-->\n' + paper_block + '<!--/PAPERTRADE-->\n'
    if body:
        out = body
        # ★2026-08-16 竞价路改六段: 盘中竞价强势(★今晨闸门/★今晨初读)移出竞价页→盘中作战页
        #   历史八段 body 残留的闸门/初读段(含空锚)在此清理, 不再显示。
        out = re.sub(r'<section[^>]*>\s*<h2[^>]*>★今晨闸门.*?</section>\s*', '', out, flags=re.S)
        out = re.sub(r'<section[^>]*>\s*<h2[^>]*>★今晨初读.*?</section>\s*', '', out, flags=re.S)
        out = re.sub(r'<h2[^>]*>★今晨闸门.*?</h2>\s*<!--MACHGATE-->.*?<!--/MACHGATE-->', '', out, flags=re.S)
        out = re.sub(r'<h2[^>]*>★今晨初读.*?</h2>\s*<!--MACHREAD-->.*?<!--/MACHREAD-->', '', out, flags=re.S)
        # ★S2(2026-08-12 补): 机器卡注入——body 里管道预留空锚
        #   <!--SCORECARD-->(评分表) <!--POOLLEDGER-->(结算)
        #   空锚=注入点→填对应机器卡(去MACH锚名防哨兵撞锚); POOLLEDGER 无锚(补跑body)=尾部追加;
        #   锚内有内容(7/16黄金版原文历史注入卡)=保真铁律, 一律不动。
        inj = [('SCORECARD', r_mach_score(d)), ('MACHSIG', r_mach_sig()),
               ('POOLLEDGER', r_mach_pool(d))]
        for an, fn in inj:
            card = fn or ''
            if not card:
                continue
            card = card.replace('<!--SCORECARD-->', '').replace('<!--/SCORECARD-->', '')
            for a in ('MACHPOOL', 'MACHSCORE', 'MACHSIG'):
                card = card.replace('<!--%s-->' % a, '').replace('<!--/%s-->' % a, '')
            if an == 'MACHSIG':
                # r_mach_sig=黄金版段四原文(含自身h2); body 段六已带 h2 → 注入去 h2 防双标题
                card = re.sub(r'<h2.*?</h2>', '', card, flags=re.S)
            s = out.find('<!--%s-->' % an)
            if s >= 0:
                e = out.find('<!--/%s-->' % an, s)
                if e > s:
                    if an == 'POOLLEDGER':
                        # 台账式归档: 始终用 r_mach_pool(最新+更早存档)覆盖历史注入的逐日折叠(2026-08-15)
                        out = out[:s] + '<!--%s-->' % an + card + out[e:]
                    elif not out[s + len('<!--%s-->' % an):e].strip():
                        out = out[:s] + '<!--%s-->' % an + card + out[e:]
            elif an == 'POOLLEDGER' and 'MACHPOOL' not in out and 'POOLLEDGER' not in out:
                out = out.rstrip('\n') + '\n<!--POOLLEDGER-->' + card + '<!--/POOLLEDGER-->\n'
        if not out.endswith('\n'):
            out += '\n'
        if paper:
            i2 = out.find('<h2>一')
            if i2 > 0:
                out = out[:i2] + paper + out[i2:]
            else:
                out = out + paper
        out = inject_into_section(_iter2tl(_dig2card(out), d), 'auction', d)
        return out
    head = ('<div class="rowA"><div class="hero"><div class="kick">Auction · 竞价命门 · 第1路 · 截至 %s 收盘</div>'
            '<h1>竞价页 · %s 复盘未产, 数据断档如实呈现</h1>'
            '<p>机器数据(竞价选股池/昨池结算/信号胜率库)按数据源渲染; 判断板块缺 body 不编造。</p>'
            '<div class="stance"><span class="pill warn">状态 · <b class="s-weak">复盘断档</b></span></div></div></div>\n'
            % (d[4:6] + '-' + d[6:8], d[4:6] + '-' + d[6:8]))
    cards = [c for c in (_c1_temp(d), r_mach_score(d), r_mach_pool(d), r_mach_sig()) if c]
    mach = ''
    if cards:
        chips = '<span class="chip">%d卡</span>' % len(cards)
        mach = ('<details class="chain"><summary><b>机器数据源</b> %s '
                '<span class="mut">温度/竞价池/结算/信号库数字核对层 · 展开查看 · 判断以复盘为准</span></summary>'
                '<div class="inner">\n%s</div></details>\n' % (chips, ''.join(cards)))
    return head + mach + paper + r_gap_card(d)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '20260811'
    page = build_page_full(d)
    print('=== auction 模块化渲染 @%s ===' % d)
    print('整页 body: %d KB | 卡%d 表%d 折叠%d h2:%d | 断档卡:%s' % (
        len(page) // 1024, page.count('class="card"'), page.count('<table'),
        page.count('<details'), len(re.findall(r'<h2>', page)),
        '⚠' in page and '未产' in page))
    print('机器锚: MACHSCORE=%s MACHPOOL=%s MACHSIG=%s | body保真:%s' % (
        page.count('<!--MACHSCORE-->') == 1 and page.count('<!--/MACHSCORE-->') == 1,
        page.count('<!--MACHPOOL-->') == 1 and page.count('<!--/MACHPOOL-->') == 1,
        page.count('<!--MACHSIG-->') == 1 and page.count('<!--/MACHSIG-->') == 1,
        '<div class="rowA">' in page))
    if '--shell' in sys.argv:
        # 独立页面完整套壳: 从 SITE 全站页解析提取 shell(防编码乱码+组件缺失)
        site = os.path.join(BASE, '复盘', '盯盘台')
        shell_src = os.path.join(site, 'auction.html')
        if not os.path.isfile(shell_src):
            shell_src = os.path.join(site, 'lhb.html')
        shell = open(shell_src, encoding='utf-8').read()
        paper = os.path.join(L, '_模拟盘', 'auction', '看板_%s.html' % d)
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
