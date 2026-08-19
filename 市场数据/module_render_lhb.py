# -*- coding: utf-8 -*-
"""module_render_lhb.py —— lhb 页组件化渲染(2026-08-12, 阶段A推广, 模板=module_render_limitup.py)
读数据源 → 渲染 6 板块 → 输出页面 body 片段
用法: python module_render_lhb.py 20260716 [--out 路径]
铁律: 机器组件数字只来自数据源文件/权威生成器(资金温度.py --card / lhb席位区.py / judgment bodies注入段);
      LLM 组件只从 judgment bodies 按边界提取原文, 不重写
六板块: 一席位综合判断(LLM) 二资金温度FUNDTEMP(机器) 三龙虎榜台账LHBLEDGER(机器注入bodies) 四分档库(机器) 五自主深挖(LLM) 六认知迭代(LLM+折叠)
"""
import re, os, sys, json, subprocess
from _认知库渲染 import r_cog_lib

BASE = r'D:\股票数据\市场数据'
if not os.path.isdir(BASE):
    BASE = [p for p in ('/sessions/*/mnt/股票数据/市场数据',) if os.path.isdir(p)][0] if os.path.isdir('/sessions') else BASE
L = os.path.join(BASE, '_学习')
CD = BASE

# ============ 数据契约加载 ============
def load_body(d):
    """LLM 组件提取源: judgment_{d}.json bodies['lhb']"""
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return ''
    try:
        return json.load(open(p, encoding='utf-8'))['bodies']['lhb']
    except Exception:
        return ''

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

def _card_span(body, kw):
    """定位含 kw 的卡: kw 往前 rfind 最近的 <div class="card 起点 → 配平取整卡。遍历所有 kw 出现位。"""
    for i in [m.start() for m in re.finditer(re.escape(kw), body)]:
        cs = body.rfind('<div class="card', 0, i)
        if cs < 0: continue
        ce = _match_div(body, cs)
        yield body[cs:ce] + ('\n' if body[ce:ce+1] == '\n' else '')

def _body_h2(body, kw):
    """从 bodies 提取 h2 原文(黄金版 h2=LLM 手写含 hint, 逐字节保真)"""
    i = body.find('<h2>%s' % kw)
    if i < 0: return ''
    e = body.find('</h2>', i)
    return body[i:e + 5] if e > 0 else ''

def _wd_python():
    """权威脚本需要 pandas — 用项目 venv (.venv312), 回退当前解释器"""
    for c in (r'D:\股票数据\.venv312\Scripts\python.exe',
              r'D:\股票数据\.venv\Scripts\python.exe'):
        if os.path.exists(c): return c
    return sys.executable

def _env_clean():
    """清代理+PYTHONPATH(四键): Hermes进程注入的cp311 numpy会炸.venv312(py3.12)"""
    return {k: v for k, v in os.environ.items()
            if k not in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'PYTHONPATH')}

# ============ 板块一: 席位荐票 · 综合判断(荐票卡置顶+洞察, 2026-08-13用户拍板) ============
def r_seatcard(body):
    """板块一荐票卡: 当日SEATCARD段(台账日块内提取, 与台账同源;
    结算脚本回填台账日块后, 重渲染自动同步; 缺锚回退读席位荐票卡文件)"""
    s = body.find('<!--SEATCARD-->')
    e = body.find('<!--/SEATCARD-->', s) if s >= 0 else -1
    seg = body[s:e + len('<!--/SEATCARD-->')] if e > s else ''
    if not seg:
        return ''
    lp = body.rfind('<p style="font-weight:700', 0, s)  # 前导标题行(当日席位路Top5荐票…)
    lead = ''
    if lp >= 0:
        le = body.find('</p>', lp)
        if 0 < le < s:
            lead = body[lp:le + 4]
    return lead + chr(10) + seg

def _rec2obs(seg):
    """2026-08-15 修复: 观察卡自造 rec-card(无CSS→文字裸奔) → 黄金版 .obs 组件(有CSS)
    参照 convert_812_body_component.py 的 rec-card→obs 转换(变更总账#319 已定规范),
    零编造: 只搬字不改数字; rec-title 拆 obs-nm+obs-pos tag, rec-his→obs-watch(历史对照),
    rec-why→obs-watch(理由); 解析失败保真返回原样"""
    def _conv(m):
        inner = m.group(1)
        tm = re.search(r'<div class="rec-title">(.*?)<span class="tag">(.*?)</span></div>', inner, re.S)
        if not tm:
            return m.group(0)
        nm = tm.group(1).strip()
        tag = tm.group(2).strip()
        his = re.search(r'<div class="rec-his">(.*?)</div>', inner, re.S)
        why = re.search(r'<div class="rec-why">(.*)', inner, re.S)  # rec-why 是末元素, 闭合 </div> 被外层正则消费, 故匹配到 inner 末尾
        obs = ('<div class="obs"><div class="obs-head">'
               '<span class="obs-nm">%s</span><span class="obs-pos tag">%s</span></div>' % (nm, tag))
        if his:
            obs += '<div class="obs-watch"><span class="obs-lab">历史对照</span>%s</div>' % his.group(1).strip()
        if why:
            obs += '<div class="obs-watch"><span class="obs-lab">理由</span>%s</div>' % why.group(1).strip()
        obs += '</div>'
        return obs
    return re.sub(r'<div class="rec-card">(.*?)</div></div>', _conv, seg, flags=re.S)

def r_judge(body):
    """C1.1: h2一 + SEATCARD荐票表 + body板块一原文(SEATCARD段后→h2二前, 含洞察(agent)卡)
    荐票卡=第一项(用户2026-08-13拍板, 对齐limitup格式: 荐票卡→本路洞察)
    ★2026-08-17 修复: rest 区间曾从 h2一后一直取到 FUNDTEMP 锚, 而 body 契约漂移时
    SEATCARD 段(荐票表)与 LLM 手写 h2二 都落在这个区间内 → 与置顶荐票卡重复、
    与机器资金温度卡 h2二 撞车(页面出现两个相同荐票卡+两个'二 资金温度'标题)。
    现修正: rest 从 SEATCARD 段结束处起取(置顶卡已含荐票表, 不重复), 到 h2二/FUNDTEMP 前止
    (h2二 由机器卡权威提供, LLM 手写 h2二 丢弃)"""
    i = body.find('<h2>一')
    if i < 0: return ''
    e = body.find('</h2>', i)
    if e < 0: return body[i:]
    h = body[i:e + 5]
    j = body.find('<!--FUNDTEMP-->', i)
    if j < 0:
        j = body.find('<h2>二', i)
    if j < 0:
        j = body.find('<!--LHBLEDGER-->', i)
    if j < 0:
        _m = re.search(r'<h2>', body[e + 5:])
        j = e + 5 + _m.start() if _m else -1
    # ★2026-08-17: rest 起点跳过 SEATCARD 段(置顶荐票卡已含, 防重复)
    s_end = body.find('<!--/SEATCARD-->', i)
    rest_start = (s_end + len('<!--/SEATCARD-->')) if s_end > 0 else e + 5
    # ★2026-08-17: rest 终点截到 h2二 前(LLM 手写 h2二 与机器卡撞车, 丢弃)
    j2 = body.find('<h2>二', rest_start, j if j > 0 else len(body))
    if j2 >= 0:
        j = j2
    rest = _rec2obs(body[rest_start:j if j > 0 else len(body)])
    sc = r_seatcard(body)
    return h + chr(10) + sc + chr(10) + rest

# ============ 板块二b: 契约外板块二保真(2026-08-13 修复"丢失3个组件") ============
def r_sec2_preserve(body):
    """body 的 h2二→h2三 段: 契约内=资金温度(机器卡覆盖, 返回空);
    契约外(如 8/13 agent 写的'席位动向全景')=保真返回, 插到机器卡前防内容丢失"""
    i = body.find('<h2>二')
    if i < 0:
        return ''
    e = body.find('</h2>', i)
    h2txt = body[i:e]
    if '资金温度' in h2txt:
        return ''
    nxt = body.find('<h2>三', i)
    return body[i:nxt if nxt > 0 else len(body)]

def _renum_h2(page):
    """按出现顺序重编号 h2 前缀(一二三...): 兼容 body 契约漂移(板块增减后编号自动顺延)"""
    nums = '一二三四五六七八九'
    idx = [0]
    def repl(m):
        if idx[0] >= len(nums):
            return m.group(0)
        n = nums[idx[0]]
        idx[0] += 1
        return '<h2>%s %s</h2>' % (n, m.group(2))
    return re.sub(r'<h2>([一二三四五六七八九]) (.+?)</h2>', repl, page)

# ============ 板块二: 资金温度 FUNDTEMP(机器·权威生成器) ============
def r_fundtemp(d):
    """C2.1 机器: 板块二全卡 = 资金温度.py --card 权威生成器(含h2二+hint+SVG+表+FUNDTEMP锚, 黄金版逐字节)
    数据: _席位动向/*.csv 全序列(截至d, 零后视镜)"""
    try:
        subprocess.run([_wd_python(), os.path.join(CD, '资金温度.py'), '--card', d],
                       capture_output=True, timeout=180, check=True,
                       env=_env_clean())
    except Exception as ex:
        print('!!!资金温度.card 调用失败:', ex)
        return ''
    p = os.path.join(L, '资金温度卡_%s.html' % d)
    if not os.path.exists(p): return ''
    return open(p, encoding='utf-8').read()  # card 文件已含尾换行, 不再补

# ============ 板块三: 龙虎榜台账 LHBLEDGER(机器注入bodies, 整段保真) ============
def r_ledger(body):
    """C3.1 机器+LLM: bodies <!--LHBLEDGER--> 注入后整段(h2三 到 h2四), 逐字节保真
    模拟 _fold_ledger: bodies 无 foldarchive 且含 >1 日块 → 更早存档折叠(黄金版同构)
    ★2026-08-13: LLM漏写h2三 → 从LHBLEDGER锚起提取+机器补标题(防台账整段丢失)"""
    ls = body.find('<h2>三')
    le = -1
    if ls < 0:
        anchor = body.find('<!--LHBLEDGER-->')
        if anchor < 0: return ''
        le = body.find('<h2>四', anchor)
        seg = '<h2>三 龙虎榜台账 · 逐日</h2>\n' + body[anchor:le if le > 0 else len(body)]
    else:
        le = body.find('<h2>四', ls)
        seg = body[ls:le if le > 0 else len(body)]
    # ★2026-08-13: 当日日块SEATCARD段(含前导p)已在板块一展示 → 台账内移除防重复(历史日块不动)
    s1 = seg.find('<!--SEATCARD-->')
    if s1 >= 0:
        e1 = seg.find('<!--/SEATCARD-->', s1)
        if e1 > s1:
            lp = seg.rfind('<p style="font-weight:700', 0, s1)
            if lp >= 0:
                le2 = seg.find('</p>', lp)
                if 0 < le2 < s1:
                    seg = seg[:lp] + seg[e1 + len('<!--/SEATCARD-->'):]
    if 'foldarchive' not in seg:
        o1 = seg.find('<details class="chain" open>')
        if o1 >= 0:
            d2 = seg.find('<details class="chain">', o1 + 10)
            if d2 > 0:
                newest = seg[:d2]
                rest = seg[d2:]
                rest_clean = rest.replace('<!--/LHBLEDGER-->', '').rstrip('\r\n')
                dts = re.findall(r'<summary><b>([^<]+)</b>', rest_clean)
                arch = ('<details class="chain foldarchive"><summary><b>更早存档</b> <span class="chip">%d条</span> <span class="mut">%s ~ %s</span></summary>'
                        '<div class="inner">%s</div></details><!--/LHBLEDGER-->\n'
                        % (len(re.findall(r'<details class="chain">', rest_clean)),
                           dts[-1] if dts else '', dts[0] if dts else '', rest_clean))
                seg = newest + arch
    return seg

# ============ 板块四: 席位分档库(机器·权威生成器) ============
def r_lib(d):
    """C4.1 机器: 分档库固定段 = lhb席位区.py {d} 权威产物(_学习/席位分档库.html)
    数据: _席位分档.json(rank产出) + _席位动向/{d}.csv"""
    try:
        subprocess.run([_wd_python(), os.path.join(CD, 'lhb席位区.py'), d],
                       capture_output=True, timeout=180, check=True,
                       env=_env_clean())
    except Exception as ex:
        print('!!!lhb席位区 调用失败:', ex)
        return ''
    p = os.path.join(L, '席位分档库.html')
    if not os.path.exists(p): return ''
    return open(p, encoding='utf-8').read() + '\n'

# ============ 板块五: 自主深挖 · 席位孵化(LLM) ============
def _panel2card(seg):
    """2026-08-15 修复: lhb 五段自造 panel(无CSS→4段落裸奔) → 黄金版 card 组件(有CSS)
    对齐 limitup 五段结构: <div class="card"><b>标题</b><p>正文</p></div>; 零编造只搬字"""
    m = re.search(r'<div class="panel">(.*?)</div>', seg, re.S)
    if not m:
        return seg
    inner = m.group(1)
    cards = []
    for pm in re.finditer(r'<p>(.*?)</p>', inner, re.S):
        pc = pm.group(1)
        bm = re.match(r'\s*<b>(.*?)</b>\s*(.*)', pc, re.S)
        if bm:
            title = bm.group(1).strip().rstrip('：:')
            bd = bm.group(2).strip()
            cards.append('<div class="card"><b>%s</b><p style="margin:6px 0 0">%s</p></div>' % (title, bd))
        else:
            cards.append('<div class="card">%s</div>' % pc)
    return seg[:m.start()] + '\n'.join(cards) + seg[m.end():]

def r_scan(body):
    """C5.1 LLM: 板块五整段(h2五 清单应答卡 + obs块) 原文提取, 逐字节保真
    2026-08-15 修复: 自造 panel(无CSS) → card 组件(对齐limitup五段)"""
    i = body.find('<h2>五')
    if i < 0: return ''
    nxt = body.find('<h2>六', i)
    seg = body[i:nxt if nxt > 0 else len(body)]
    return _panel2card(seg)

# ============ 板块六: 我的认知迭代(LLM+折叠) ============
def _tli_date(tli):
    m = re.search(r'<b>(\d\d-\d\d)</b>', tli)
    if m: return m.group(1)
    m = re.search(r'<b>(\d{4})(\d{2})(\d{2})</b>', tli)
    return ('%s-%s' % (m.group(2), m.group(3))) if m else ''

def r_cog(body, d=None):
    """C6.1 机器+折叠: 认知时间线(最新1条外露 + 其余 tlfold 折叠)
    模拟 _fold_tl: bodies 里 div.tl 含全部 tli, 拆出 → 最新外露 + 其余包 tlfold
    ★2026-08-16: d 给定时丢弃 body 手写历史 tli(日期<d), 历史统一由 r_cog_lib 从认知库提供
    2026-08-13 修复: (1) tli 截取从 seg.find('</div>') 改为 _match_div 配平(修复
    嵌套 tli 截断致内容丢失+闭合标签错位); (2) 无 tl 结构时 fallback 保留 h2 后原文
    (LLM 偶发 card 结构, 逐字节保真原则)"""
    h6 = body.find('>六 我的认知迭代')
    if h6 < 0: return ''
    ts = body.find('<div class="tl">', h6)
    if ts < 0:
        # fallback: 无 tl 时间线(LLM 用 card 等结构) → 保留 h2 后原文
        tail = body[h6:]
        i_end = tail.find('</h2>')
        return tail[i_end + 5:].strip() if i_end >= 0 else ''
    te = _match_div(body, ts)
    seg = body[ts:te]
    items = []
    for m in re.finditer(r'<div class="tli(?:\s[^>]*)?">', seg):
        en = _match_div(seg, m.start())
        if en >= len(seg): break
        items.append(seg[m.start():en])
    if not items: return ''
    newest = items[0]
    rest = items[1:]
    if d:
        today = '%s-%s' % (d[4:6], d[6:8])
        rest = [t for t in rest if _tli_date(t) >= today]
    out = '<div class="tl">%s</div>' % newest
    if rest:
        out += ('<details class="chain tlfold"><summary><b>当日更多认知</b> '
                '<span class="chip">%d条</span> <span class="mut">%s ~ %s</span></summary>'
                '<div class="inner"><div class="tl">%s</div></div></details>\n'
                % (len(rest), _tli_date(rest[-1]), _tli_date(rest[0]), ''.join(rest)))
    return out

# ============ 拼装器(无逻辑 concat) ============
def build_components(d):
    """组件 dict(快照回归/隔离性验证用): C1席位综合判断 C2资金温度 C3台账 C4分档库 C5自主深挖 C6认知迭代"""
    body = load_body(d)
    return {
        'C1': r_judge(body),
        'C2': r_fundtemp(d),
        'C3': r_ledger(body),
        'C4': (_body_h2(body, '四 ') or '<h2>四 席位分档库</h2>') + '\n' + r_lib(d),
        'C5': r_scan(body),
        'C6': (_body_h2(body, '六 ') or '<h2>六 我的认知迭代</h2>') + '\n' + r_cog(body, d) + r_cog_lib('lhb', d),
    }

def assemble_lhb(plates):
    return ''.join(plates)

def build_page(d):
    """拼装完整 lhb 页 body(不含 shell/不含 PAPERTRADE 锚点) → 供 S2 接线
    ★PAPERTRADE 大坑(limitup S2 两轮踩中): 不能输出锚点, 模拟盘引擎走 hero 定位插入"""
    body = load_body(d)
    plates = [
        r_judge(body),             # 板块一: 含 h2 一 (LLM bodies 原文)
        r_sec2_preserve(body),     # 契约外板块二保真(如席位动向全景; 资金温度态返回空)
        r_fundtemp(d),             # 板块二: 含 h2 二 + FUNDTEMP 锚 (权威生成器)
        r_ledger(body),            # 板块三: 含 h2 三 (bodies 注入段 + foldarchive)
        (_body_h2(body, '四 ') or '<h2>四 席位分档库</h2>') + '\n' + r_lib(d),  # 板块四: h2四(LLM) + 分档库(机器)
        r_scan(body),              # 板块五: 含 h2 五 (LLM bodies 原文)
        (_body_h2(body, '六 ') or '<h2>六 我的认知迭代</h2>') + '\n' + r_cog(body, d) + r_cog_lib('lhb', d),  # 板块六
    ]
    page = assemble_lhb(plates)
    if r_sec2_preserve(body):      # 有契约外板块插入 → h2 编号按顺序重排
        page = _renum_h2(page)
    return page

def build_page_full(d):
    """完整页 body(头部区 + 六板块) → S2 接线用
    头部区(bodies 开头 rowA/hero/kick/h1/导语/stance/kpi)从 bodies 提取(LLM 手写, 逐字节保真);
    不含 PAPERTRADE 锚点(模拟盘引擎 inject 走 hero 定位, S2 文档★大坑)"""
    body = load_body(d)
    head = ''
    i2 = body.find('<h2>一')
    if i2 > 0:
        head = body[:i2] + '\n'
    return head + build_page(d)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '20260716'
    page = build_page_full(d)
    print('=== lhb 模块化渲染 @%s ===' % d)
    print('整页 body: %d KB | 卡%d 表%d 折叠%d h2:%d' % (
        len(page) // 1024, page.count('class="card"'), page.count('<table'),
        page.count('<details'), len(re.findall(r'<h2>', page))))
    print('板块锚: FUNDTEMP=%s LHBLEDGER=%s SEATCARD=%s PAPERTRADE=%s' % (
        '<!--FUNDTEMP-->' in page, '<!--LHBLEDGER-->' in page or '<!--/LHBLEDGER-->' in page,
        page.count('<!--SEATCARD-->'), '<!--PAPERTRADE-->' in page))
    if '--shell' in sys.argv:
        # 独立页面完整套壳: head+body开标签 + navbar导航 + <div class="wrap">(960px居中)
        # + 尾部动画脚本 — 从 SITE 全站页解析提取, 防浏览器默认编码乱码+组件缺失+页面全宽
        shell = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '复盘', '盯盘台', 'lhb.html'), encoding='utf-8').read()
        ib = shell.find('<body'); jb = shell.find('>', ib) + 1 if ib > 0 else len(shell)
        iw = shell.find('<div class="wrap">') if '<div class="wrap">' in shell else -1
        if iw > 0:
            # 显式 wrap 闭合(不依赖 rfind('</div>') 猜测 — ★2026-08-14 修复: 对齐 module_render_theme.py
            # 2026-08-12 的同款修复。旧写法 rfind('</div>')+len 会把 wrap 闭合 </div> 切掉,
            # 导致页面 div 开201/闭200 差1; 且 --shell 递归套壳时旧页尾部已漂移, 会自传播。
            body_end = shell.find('</body>')
            tail = shell[shell.rfind('<script', 0, body_end):body_end] if shell.rfind('<script', 0, body_end) > 0 else ''
            page = shell[:jb] + '\n' + shell[jb:iw] + '<div class="wrap">\n' + page + '\n</div>\n' + tail + '</body></html>'
        else:
            page = shell[:jb] + '\n' + page + '</body></html>'
        # PAPERTRADE 模拟盘看板: 有看板_{d}.html 则嵌入(引擎成品, 位置=h2一前), 无则留空锚
        L = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_学习')
        paper = os.path.join(L, '_模拟盘', 'lhb', '看板_%s.html' % d)
        pb = page.find('<h2>一')
        if pb > 0:
            if os.path.isfile(paper):
                block = '<!--PAPERTRADE-->\n' + open(paper, encoding='utf-8').read() + '\n<!--/PAPERTRADE-->\n'
                page = page[:pb] + block + page[pb:]
                print('PAPERTRADE看板已嵌入:', os.path.basename(paper))
            else:
                page = page[:pb] + '<!--PAPERTRADE-->\n<!--/PAPERTRADE-->\n' + page[pb:]
                print('⚠ 无看板_%s.html, PAPERTRADE留空锚' % d)
        print('已套壳: navbar=%s wrap=%s tail_script=%s' % (
            'class="navbar"' in page, '<div class="wrap">' in page, 'gsap' in page))
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    if out:
        open(out, 'w', encoding='utf-8').write(page)
        print('已写出:', out)
