# -*- coding: utf-8 -*-
"""module_render_limitup.py —— limitup 页组件化渲染（阶段A试点, 2026-08-11）
读数据源 → 渲染 6 板块 33 组件 → 输出组件片段 dict
用法: python module_render_limitup.py 20260716 [--out 路径]
设计: 板块(h2)=组合器(固定顺序拼组件); 组件=叶子渲染函数(独立数据契约, 无共享状态)
铁律: 机器组件数字只来自数据源文件; LLM 组件只从 judgment bodies 按边界提取原文, 不重写
"""
import re, os, sys, json, subprocess
from _认知库渲染 import r_cog_lib

BASE = 'D:\\股票数据\\市场数据'
if not os.path.isdir(BASE):
    BASE = [p for p in ('/sessions/*/mnt/股票数据/市场数据',) if os.path.isdir(p)][0] if os.path.isdir('/sessions') else BASE
L = os.path.join(BASE, '_学习')
CD = BASE  # 子进程工作目录/脚本目录

# ============ 数据契约加载 ============
def load_recommend(d):
    """C1.1 数据源: 涨停质量荐票_{d}.json → {top5:[], 明细:[], 活跃因子, 口径}"""
    p = os.path.join(L, '涨停质量荐票_%s.json' % d)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None

def load_quality():
    """C2.3/C2.4-2.6/C4.1 数据源: _涨停质量库.json → {规则榜, 分板胜率, 因子, 基准, 环境规则}"""
    p = os.path.join(L, '_涨停质量库.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None

def load_temp():
    """C2.1/C2.2 数据源: _市场温度表.json → {日期: {温度, 温度档, 涨停数, 炸板率, 梯队, ...}}"""
    p = os.path.join(L, '_市场温度表.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None

def load_guiban(d):
    """C3.x.1/2 数据源: 题材归位_{d}.json → {映射: {代码: {大方向, 环节, 催化, 来源档}}}"""
    p = os.path.join(L, '题材归位_%s.json' % d)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None

def load_settle():
    """C3.x.3 数据源: _荐票逐票结算.jsonl → 按荐票日索引 {荐票日: [行...]}"""
    p = os.path.join(L, '_荐票逐票结算.jsonl')
    if not os.path.exists(p): return {}
    out = {}
    for ln in open(p, encoding='utf-8'):
        ln = ln.strip()
        if not ln: continue
        try: row = json.loads(ln)
        except Exception: continue
        out.setdefault(row.get('荐票日', ''), []).append(row)
    return out

def load_reflect():
    """C3.x.4 数据源: _涨停质量反思.jsonl → 按荐票日索引"""
    p = os.path.join(L, '_涨停质量反思.jsonl')
    if not os.path.exists(p): return {}
    out = {}
    for ln in open(p, encoding='utf-8'):
        ln = ln.strip()
        if not ln: continue
        try: row = json.loads(ln)
        except Exception: continue
        out.setdefault(row.get('荐票日', ''), []).append(row)
    return out

def load_body(d):
    """LLM 组件提取源: judgment_{d}.json bodies['limitup']"""
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return ''
    try:
        return json.load(open(p, encoding='utf-8'))['bodies']['limitup']
    except Exception:
        return ''

# ============ 通用 HTML 工具 ============
def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _pct(x, nd=1):
    try: return ('%.*f' % (nd, float(x) * 100))
    except Exception: return '—'

def _num(x, nd=1):
    try:
        v = float(x)
        return ('%.*f' % (nd, v)).rstrip('0').rstrip('.') if nd else str(int(v))
    except Exception: return '—'

def _fmt2(x):
    """固定 2 位小数(保留尾0): -0.60 → -0.60"""
    try:
        return '%.2f' % float(x)
    except Exception: return '—'

def _signed(x):
    """2位小数带正负号: 0.21 → +0.21; -0.60 → -0.60"""
    try:
        v = float(x)
        return ('+' if v > 0 else '') + ('%.2f' % v)
    except Exception: return '—'

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
    """定位含 kw 的卡: kw 往前 rfind 最近的 <div class="card (可带 style) 起点 → 配平取整卡。
    返回 (起点, 终点) 或 None。遍历所有 kw 出现位。含卡后尾随换行(黄金版格式)。"""
    for i in [m.start() for m in re.finditer(re.escape(kw), body)]:
        cs = body.rfind('<div class="card', 0, i)
        if cs < 0: continue
        ce = _match_div(body, cs)
        yield body[cs:ce] + ('\n' if body[ce:ce+1] == '\n' else '')

# ============ 板块一: Top5 荐票卡 ============
def r_top5_table(reco, body):
    """C1.1 机器: Top5 荐票表(黄金版7列: #/标的(代码)/抓龙率(分)/命中规则·主导因子/预测执行/题材)
    数据: 涨停质量荐票_{d}.json top5(全字段直取); 环境规则hint从bodies提取"""
    top5 = (reco or {}).get('top5') or []
    rows = ''
    for i, s in enumerate(top5, 1):
        rules = '; '.join(s.get('命中规则') or [])
        if rules:
            rules = _esc(rules)
        else:
            rules = '<span class="mut">规则未命中</span>'
        zd = s.get('主导因子') or ''
        if zd:
            zd = ('<span class="mut" style="font-size:11px">主导: %s</span>' % _esc(zd))
        else:
            zd = '<span class="mut" style="font-size:11px">主导: —</span>'
        exec_ = ('执1 %s%%/%s%%<br><span class="mut">执2 %s%%/%s%%</span>'
                 % (_num(s.get('预测执1胜率')), _signed(s.get('预测执1均涨')),
                    _num(s.get('预测执2胜率')), _signed(s.get('预测执2均涨'))))
        rows += ('<tr><td>%d</td><td style="white-space:nowrap"><b>%s</b><br><span class="mut">%s</span></td>'
                 '<td style="white-space:nowrap"><b>%s%%</b><br><span class="mut">分%s</span></td>'
                 '<td style="word-break:break-word">%s<br>%s</td>'
                 '<td style="white-space:nowrap">%s</td><td>%s</td></tr>'
                 % (i, _esc(s.get('名称', '')), _esc(str(s.get('代码', ''))),
                    _num(s.get('抓龙率')), _num(s.get('质量分')), rules, zd,
                    exec_, _esc(s.get('大方向', ''))))
    hint = (reco or {}).get('口径', '')
    # 表尾 hint 黄金版=LLM 手写(v5排序...), 从 bodies 提取(荐票卡后紧跟的 hint div)
    bh = ''
    i2 = body.find('<div class="hint">v5排序')
    if i2 > 0:
        bh_end = body.find('</div>', i2)
        bh = body[i2:bh_end + 6] + '\n' if bh_end > 0 else ''
    # 环境规则hint(黄金版位于 h2 一 之后, card 之前, 含 <div class="hint"> 前缀)
    env = ''
    i1 = body.find('<div class="hint">★环境规则')
    if i1 < 0:
        i1 = body.find('★环境规则')
    if i1 > 0:
        env_end = body.find('</div>', i1)
        if env_end > 0:
            env = body[i1:env_end + 6]
    return ('%s<div class="card"><table style="table-layout:fixed;width:100%%"><colgroup>'
            '<col style="width:26px"><col style="width:106px"><col style="width:62px"><col>'
            '<col style="width:150px"><col style="width:96px"></colgroup>'
            '<tr><th>#</th><th>标的</th><th>抓龙率</th><th>命中规则(规则榜) / 主导因子(评分卡)</th>'
            '<th>预测执行(T+1开买→收)</th><th>题材</th></tr>%s</table></div>'
            '%s' % (env, rows, bh))

def r_top5_insight(body):
    """C1.2 LLM: 从 bodies 提取 洞察(agent) 卡原文"""
    for seg in _card_span(body, '洞察(agent)'):
        return seg
    return ''

# ============ 板块二: 市场温度 ============
def _wd_python():
    """市场温度.py 需要 pandas — 用项目 venv (D:\\股票数据\\.venv312), 回退当前解释器"""
    for c in (r'D:\股票数据\.venv312\Scripts\python.exe',
              r'D:\股票数据\.venv\Scripts\python.exe'):
        if os.path.exists(c): return c
    return sys.executable

def r_temp_full(d):
    """C2.1-2.6 机器: 板块二全卡(黄金版权威生成器)
    = strip + 温度卡SVG + 数据表折叠 + 梯队画像 + 档位成绩单 + 龙票规则榜 + 分板胜率库
    调用 市场温度.py --card (pandas 运行时), 读 _学习/市场温度卡_{d}.html"""
    try:
        subprocess.run([_wd_python(), os.path.join(CD, '市场温度.py'), '--card', d],
                       capture_output=True, timeout=180, check=True,
                       env={k: v for k, v in os.environ.items()
                            if k not in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'PYTHONPATH')})
    except Exception as ex:
        print('!!!市场温度.card 调用失败:', ex)
        return ''
    p = os.path.join(L, '市场温度卡_%s.html' % d)
    if not os.path.exists(p): return ''
    return open(p, encoding='utf-8').read() + '\n'

# ============ 板块三: 归位台账 LEDGER ============
def load_zt_pool():
    """C3.x.2 数据源: _ths_zt_pool.json → {日期: [{code,name,order_amount,high_days,first_limit_up_time,...}]}"""
    p = os.path.join(L, '_ths_zt_pool.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}

def _board_num(v):
    """解析连板数: '2天2板'→2, '5板'→5, 数字→int, 其他→1"""
    if v is None: return 1
    s = str(v)
    m = re.search(r'(\d+)\s*板', s)
    if m: return int(m.group(1))
    try: return int(float(s))
    except Exception: return 1

def r_ledger_reco(day):
    """C3.x.1 机器: 当日涨停质量Top5荐票表卡(荐票原文)
    数据: 涨停质量荐票_{day}.json top5; 抓龙率/预测执行若数据源无则标 '—'(零编造)"""
    p = os.path.join(L, '涨停质量荐票_%s.json' % day)
    if not os.path.exists(p): return ''
    try: reco = json.load(open(p, encoding='utf-8'))
    except Exception: return ''
    top5 = reco.get('top5') or []
    if not top5: return ''
    rows = ''
    for i, s in enumerate(top5, 1):
        rules = '; '.join(s.get('命中规则') or [])
        rows += ('<tr><td>%d</td><td style="white-space:nowrap"><b>%s</b><br><span class="mut">%s</span></td>'
                 '<td><b>%s</b></td><td style="word-break:break-word">%s</td>'
                 '<td>%s板</td><td>%s</td><td>%s</td></tr>'
                 % (i, _esc(s.get('名称', '')), _esc(s.get('代码', '')),
                    _num(s.get('封单比')), _esc(rules),
                    _board_num(s.get('连板')), _num(s.get('命中数')), _esc(s.get('题材', ''))))
    return ('<p style="font-weight:700;margin:14px 0 4px;border-left:3px solid var(--accent);padding-left:8px">'
            '当日涨停质量Top5荐票(v5规则榜+抓龙率·第5路)</p>'
            '<div class="card"><table><tr><th>#</th><th>标的</th><th>封单比</th>'
            '<th>命中规则(规则榜) / 命中数</th><th>连板</th><th>命中数</th><th>题材</th></tr>%s</table></div>'
            % rows)

def r_ledger_detail(day, guiban, ztpool):
    """C3.x.2 机器: 涨停明细表卡(首封/标的/封单·身位/催化·来源档/质量分)
    结构: 按大方向分组(组头: 家数/最高板/承载) → 组内按环节 → 明细行
    数据: 题材归位(分组/环节/催化/来源档) + THS涨停池(首封时间/封单额/连板)"""
    mp = (guiban or {}).get('映射') or {}
    pool = (ztpool or {}).get(day) or []
    by_code = {str(x.get('code', '')).zfill(6): x for x in pool}
    # 按大方向分组
    groups = {}
    for code, info in mp.items():
        d = info.get('大方向') or '未归位'
        groups.setdefault(d, []).append((code, info))
    out = '<div class="card"><table><tr><th>首封</th><th>标的</th><th>封单·身位</th>' \
          '<th>催化 · 来源档</th><th>连板/开板</th></tr>'
    for gname, items in groups.items():
        lv = max(_board_num(by_code.get(c, {}).get('high_days')) for c, _ in items)
        out += '<tr style="background:#f3eee1"><td colspan="5"><b>【%s】</b>%d只 · 最高%d板</td></tr>' % (gname, len(items), lv)
        # 环节分组
        subs = {}
        for c, info in items:
            subs.setdefault(info.get('环节') or '—', []).append((c, info))
        for sname, sitems in subs.items():
            out += '<tr><td colspan="5" style="background:#faf7f0"><b>── %s</b> <span class="mut">(%d只)</span></td></tr>' % (sname, len(sitems))
            for c, info in sitems:
                z = by_code.get(c, {})
                out += ('<tr><td>%s</td><td><b>%s</b> <span class="mut">%s</span></td>'
                        '<td>%s</td><td>%s <span class="mut">%s档</span></td><td>%d板/开%d</td></tr>'
                        % (z.get('first_limit_up_time') or '—', z.get('name') or c,
                           c, z.get('order_amount') or '—', info.get('催化') or '—',
                           info.get('来源档') or '—', _board_num(z.get('high_days')), int(z.get('open_num') or 0)))
    out += '</table></div>'
    return out

def r_ledger_llm_extra(body, day):
    """C3.x.5 LLM: 日块内额外判断卡(题材核对说明 + 主线vs散乱结构)
    历史日(旧格式)可能含; 当日/新格式无则返回''。从 bodies 原文提取。"""
    # 定位该日块: summary 里有 07-XX 存档字样
    dk = day[4:6] + '-' + day[6:8]
    i = body.find('<summary><b>%s</b>' % dk)
    if i < 0:
        i = body.find('>%s<' % dk)
    if i < 0: return ''
    # 日块结束 = 下一个 <details class="chain"> (summary 外层) 或 h2 四
    nxt = body.find('<details class="chain">', i + 20)
    end = nxt if nxt > 0 else len(body)
    seg = body[i:end]
    out = ''
    for kw, label in [('题材核对说明', '题材核对说明(A/B/C + 跨界识别)· THS归位后'),
                      ('主线 vs 散乱结构', '主线 vs 散乱结构')]:
        k = seg.find(kw)
        if k < 0: continue
        # 卡起点: p 标签之后紧跟的 card
        cs = seg.find('<div class="card">', k)
        if cs < 0: continue
        ce = _match_div(seg, cs)
        if ce <= cs: continue
        out += ('<p style="font-weight:700;margin:14px 0 4px;border-left:3px solid var(--accent);padding-left:8px">%s</p>'
                '%s' % (label, seg[cs:ce]))
    return out

def r_ledger_day(d, guiban, settle, body, day, ztpool=None, is_newest=False):
    """C3.x 机器+LLM: 单日台账日块 — bodies 原文提取(黄金版=LLM判断+机器注入混合体)
    bodies 中 <!--LEDGER--> 后即完整板块三(最新日 open + 历史折叠), 逐字节保真。
    机器函数(r_ledger_settle/reco/detail)作为校验器: 数字与数据源不一致时报告。"""
    # 整板块三 = <h2>三 到 <h2>四 (bodies: h2 三 在 <!--LEDGER--> 前)
    # 黄金版 vs bodies 差异: 黄金版有 foldarchive(更早存档容器) — 由 _fold_ledger 注入
    ls = body.find('<h2>三')
    if ls < 0: return ''
    le = body.find('<h2>四', ls)
    seg = body[ls:le if le > 0 else len(body)]
    # 模拟 _fold_ledger: 若 bodies 无 foldarchive 且含 >1 个日块, 则注入
    if 'foldarchive' not in seg:
        # 找第一个日块 details(open) 的结束, 与后续日块
        o1 = seg.find('<details class="chain" open>')
        if o1 >= 0:
            # 最新日块结束 = 下一个 <details class="chain"> 的位置(其前面的 </details>)
            d2 = seg.find('<details class="chain">', o1 + 10)
            if d2 > 0:
                newest = seg[:d2]
                rest = seg[d2:]
                # 更早存档容器(日期升序: 最早 ~ 最晚); 闭合注释位置对齐黄金版
                rest_clean = rest.replace('<!--/LEDGER-->', '').rstrip('\r\n')
                dts = re.findall(r'<summary><b>([^<]+)</b>', rest_clean)
                arch = ('<details class="chain foldarchive"><summary><b>更早存档</b> <span class="chip">%d条</span> <span class="mut">%s ~ %s</span></summary>'
                        '<div class="inner">%s</div></details><!--/LEDGER-->\n'
                        % (len(re.findall(r'<details class="chain">', rest_clean)),
                           dts[-1] if dts else '', dts[0] if dts else '', rest_clean))
                seg = newest + arch
    return seg

def r_attribution(body, day):
    """C3.x.4 LLM: 从 bodies 按日期键提取 自动归因反思 卡原文
    算法: _card_span 遍历所有'自动归因反思'卡 → 卡内含该日结算字样(0715/20260715荐票)才返回"""
    key = day[2:] if len(day) == 8 else day          # 20260715 → 0715
    for seg in _card_span(body, '自动归因反思'):
        if key in seg or (day + '荐票') in seg:
            return seg
    return ''

# ============ 板块四: 训练库 v6 ============
def r_factor_table(q, body):
    """C4.1 机器: 因子表(16因子/权重/区分度/rho/状态) — 黄金版包 details 折叠
    状态=数据源原文; 区分度带pp; rho 1位小数; '今晚变化'说明从 bodies 提取"""
    fz = (q or {}).get('因子') or {}
    rows = ''
    for name, v in fz.items():
        st = v.get('状态') or '—'
        if '有效' in st and '淘汰' not in st and '翻转' not in st:
            cls = " class='up'"
        elif '淘汰' in st or '翻转' in st:
            cls = " class='dn'"
        else:
            cls = " class='mut'"
        w = v.get('权重')
        w_str = '—' if w is None else ('%.4f' % float(w)).rstrip('0').rstrip('.') + ('.0' if float(w) == 0 else '')
        if float(w) == 0: w_str = '0.0'
        dd = v.get('区分度')
        dd_str = '—' if dd is None else ('%.1fpp' % float(dd))
        rh = v.get('单调rho')
        rh_str = '—' if rh is None else ('%.1f' % float(rh))
        rows += ('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td%s>%s</td></tr>'
                 % (_esc(name), w_str, dd_str, rh_str, cls, st))
    qq = q or {}
    sample = qq.get('样本') or '—'
    win = qq.get('窗口') or '—'
    # '今晚变化'说明段(LLM 手写, bodies 提取, 含 <p> 包装)
    note = ''
    i = body.find('今晚变化')
    if i > 0:
        ps = body.rfind('<p', 0, i)
        pe = body.find('</p>', i)
        if ps > 0 and pe > 0:
            note = body[ps:pe + 4]
    return ('<details class="chain"><summary><b>质量库v6 · 样本%s · 窗口%s · 活跃因子%d/16</b> <span class="chip">%s重训</span></summary>'
            '<div class="inner"><table><tr><th>因子</th><th>权重</th><th>区分度</th>'
            '<th>rho</th><th>状态</th></tr>%s</table>%s</div></details>\n'
            % (sample, win, len((qq.get('活跃因子') or [])), qq.get('更新') or '—', rows, note))

# ============ 板块五: 自主深挖 ============
def r_scan_card(body):
    """C5.1 LLM: 清单应答卡 + 观察块(obs) 原文提取
    黄金版板块五 = 清单应答card + 0..N个 obs 块 + 出页自检card; 取 清单应答 起到 出页自检 前
    2026-08-15 修复: 无'清单应答'标记时(LLM 改用假设/深挖 card 格式) fallback 保留 h2五 后原文,
    不因格式标记缺失丢内容(逐字节保真, 对齐 r_cog_timeline 的 fallback 原则)"""
    i = body.find('清单应答')
    if i < 0:
        h5 = body.find('<h2>五 ')
        if h5 < 0: return ''
        tail = body[h5:]
        e = tail.find('</h2>')
        seg = tail[e+5:].strip() if e >= 0 else ''
        chk = seg.find('出页自检')
        if chk >= 0: seg = seg[:chk]
        h6 = seg.find('<h2>六')
        if h6 >= 0: seg = seg[:h6]
        return seg.strip()
    cs = body.rfind('<div class="card', 0, i)
    if cs < 0: return ''
    nxt = body.find('出页自检', i)
    end = body.rfind('<div class="card', 0, nxt) if nxt > 0 else _match_div(body, cs)
    if end <= cs: end = _match_div(body, cs)
    return body[cs:end]

def r_selfcheck_card(body):
    """C5.2 LLM: 出页自检卡 原文提取"""
    for seg in _card_span(body, '出页自检'):
        return seg
    return ''
# ============ 板块六: 认知迭代 ============
def r_cog_timeline(body):
    """C6.1 机器+折叠: 认知时间线(最新1条外露 + 其余 tlfold 折叠)
    模拟 _fold_tl: bodies 里 div.tl 含全部 tli, 拆出 → 最新外露 + 其余包 tlfold
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
    # 拆出全部 tli(按 <div class="tli" 边界切, 保序)
    items = []
    for m in re.finditer(r'<div class="tli(?:\s[^>]*)?">', seg):
        en = _match_div(seg, m.start())
        if en >= len(seg): break
        items.append(seg[m.start():en])
    if not items: return ''
    newest = items[0]
    rest = items[1:]
    out = '<div class="tl">%s</div>' % newest
    if rest:
        out += ('<details class="chain tlfold"><summary><b>更早的认知迭代</b> '
                '<span class="chip">%d条</span> <span class="mut">%s ~ %s</span></summary>'
                '<div class="inner"><div class="tl">%s</div></div></details>\n'
                % (len(rest), _tli_date(rest[-1]), _tli_date(rest[0]), ''.join(rest)))
    return out

def _tli_date(tli):
    m = re.search(r'<b>(\d\d-\d\d)</b>', tli)
    if m: return m.group(1)
    m = re.search(r'<b>(\d{4})(\d{2})(\d{2})</b>', tli)
    return ('%s-%s' % (m.group(2), m.group(3))) if m else ''

# ============ 板块组合器(只拼不逻辑) ============
# ★黄金版六段 h2 语义族白名单 + 标准模板(2026-08-12 事故修复)
# 背景: 8/12 LLM 写 bodies 时把板块四"涨停质量库"自造为"连板结构"、hint 从方法说明变数据摘要,
#       渲染器逐字节保真 → 标题与内容错位上页。修复: 模块名主体命中语义族→LLM 原文放行;
#       不命中(=契约偏离)→回退黄金版标准 h2(内容组件仍由数据源渲染, 只换标题)。
_H2_KW = {
    '一 ': ('Top5', '荐票'),
    '二 ': ('市场温度', '涨停生态'),
    '三 ': ('归位台账',),
    '四 ': ('训练库', '质量库', '质量训练', '因子'),
    '五 ': ('自主深挖', '深挖'),
    '六 ': ('我的认知迭代', '认知迭代'),
}
# ★2026-08-13: h2 内不允许出现块级元素(hint 只能是 span); 嵌块=双重渲染源
_H2_BAD_BLOCK = re.compile(r'<(table|div|ul|ol|p|details|svg|pre)\b')
_H2_STD = {
    '一 ': '<h2>一 涨停复盘 · Top5荐票<span class="hint">排序=命中规则数→抓龙率→质量分;负筛只作用于0命中票(8/13拍板,规则命中票全保);发出版不可覆盖;桶均值非个股预言</span></h2>',
    '二 ': '<h2>二 市场温度 · 涨停生态<span class="hint">温度卡+档位成绩单(脚本产出勿改数)</span></h2>',
    '三 ': '<h2>三 归位台账<span class="hint">LEDGER=台账脚本注入;题材归位=全系统唯一真源</span></h2>',
    '四 ': '<h2>四 涨停质量库 · 因子与规则<span class="hint">因子表/规则榜/分板胜率库/甜点=脚本产出折叠;LLM逐条说明见下</span></h2>',
    '五 ': '<h2>五 自主深挖 · 因子与归位孵化</h2>',
    '六 ': '<h2>六 我的认知迭代 · 最新</h2>',
}

def _body_h2(body, kw):
    """从 bodies 提取 h2 原文(黄金版 h2=LLM 手写含 hint, 逐字节保真);
    模块名语义族白名单校验: 命中→原文放行; 不命中(LLM 契约偏离)→回退标准模板 h2
    ★2026-08-13加固: 白名单命中但 h2 内嵌块级元素(表格/div 等)=双重渲染源(8/13 板块一
    荐票小表/板块二温度kv 复现), 一律回退标准模板(内容组件仍由数据源渲染, 只换标题)"""
    i = body.find('<h2>%s' % kw)
    if i < 0:
        return _H2_STD.get(kw, '')
    e = body.find('</h2>', i)
    if e <= 0:
        return _H2_STD.get(kw, '')
    raw = body[i:e + 5]
    txt = re.sub(r'<[^>]+>', '', raw)
    if not any(k2 in txt for k2 in _H2_KW.get(kw, ())):
        return _H2_STD.get(kw, '')
    if _H2_BAD_BLOCK.search(raw):
        return _H2_STD.get(kw, '')
    return raw

def plate_top5(body, c1, c2):
    h = _body_h2(body, '一 ')
    return (h or '<h2>一 Top5 荐票卡</h2>') + '\n' + c1 + c2

def plate_temp(body, c2):
    h = _body_h2(body, '二 ')
    return (h or '<h2>二 市场温度</h2>') + '\n' + c2

def plate_ledger(seg):
    """板块三: bodies <!--LEDGER--> 原文整块(含 h2 三, 最新日open+历史折叠)"""
    if not seg: return '<h2>三 归位台账</h2>'
    return seg

def plate_train(body, c, c2='', c3=''):
    h = _body_h2(body, '四 ')
    return (h or '<h2>四 训练库</h2>') + '\n' + c + c2 + c3

def plate_scan(body, c1, c2):
    h = _body_h2(body, '五 ')
    return (h or '<h2>五 自主深挖</h2>') + '\n' + c1 + c2

def plate_cog(body, c):
    h = _body_h2(body, '六 ')
    return (h or '<h2>六 我的认知迭代</h2>') + '\n' + c

# ============ 板块一.五: 池外候选栏 ============
def r_pool_out(d):
    """读 池外候选卡_{d}.html(涨停质量荐票.py生成, 2026-08-13上线); 无文件→空串零影响"""
    p = os.path.join(L, f'池外候选卡_{d}.html')
    if not os.path.isfile(p):
        return ''
    seg = open(p, encoding='utf-8').read().strip()
    if not seg:
        return ''
    return ('<h2>一·五 池外候选 · 量价甜点观察池<span class="hint">量价因子库全市场扫描SW-1/CW,'
            '26年实测; 与Top5并列观察非荐票</span></h2>\n' + seg + '\n')

# ============ 板块四附加折叠: 质量库折叠(两折叠) + 甜点概率(2026-08-15移动/新增) ============
def r_quality_folds(d):
    """C4.2 机器: 龙票规则榜+分板×质量×温度胜率库两折叠(市场温度.py拆出, 移到四段涨停质量库)"""
    p = os.path.join(L, f'质量库折叠_{d}.html')
    if not os.path.isfile(p):
        return ''
    seg = open(p, encoding='utf-8').read().strip()
    return seg + '\n' if seg else ''


def r_sweetspot():
    """C4.3 机器: 第3板甜点概率折叠(量价因子库M28定稿, 26年跨年验证)——固定内容, 零编造"""
    return (
        '<details class="chain"><summary><b>第3板甜点概率 · 唯一正期望介入点</b>'
        '<span class="chip cold">量价因子库M28</span><span class="chip">26年17/17年正</span></summary>'
        '<div class="inner">'
        '<p class="hint" style="padding-left:0;margin:6px 0 4px">龙头逐板晋级研究(2000-2026·5787只·M2-M31)唯一抠出正期望的介入点=第3板一字开炸板&lt;3%回封。与质量分"次日执行"不同,这是"当日盘中回封瞬间买入"信号。</p>'
        '<table><tr><th>信号</th><th>n</th><th>胜率</th><th>单笔均收</th><th>盈亏比</th><th>跨年</th></tr>'
        '<tr><td>第3板一字开炸板&lt;3%回封(浅/中炸)</td><td>471</td><td>68%</td><td style="color:#1e8449;font-weight:700">+4.18%</td><td>2.76</td><td>17/17年正</td></tr>'
        '<tr><td>深炸&gt;3%(一字开炸深)</td><td>—</td><td>封住率47%</td><td>负</td><td>—</td><td>0/20年</td></tr>'
        '<tr><td>换手板打板(涨停价买)</td><td>—</td><td>—</td><td style="color:#c0392b">-2.09%</td><td>—</td><td>禁区</td></tr>'
        '<tr><td>换手板低吸(开盘价买)</td><td>—</td><td>37%</td><td style="color:#c0392b">-0.77%</td><td>—</td><td>2/26年(证伪)</td></tr>'
        '</table>'
        '<div class="hint">卖出(次日零后视镜):低开&lt;-2%开盘止损;平开±2%开盘卖;高开&gt;2%看次日量比(&lt;1.5缩量锁筹持有到断板,≥1.5放天量开盘卖)。甜点为稀有事件(日均0.1~0.25次),多数日无甜点=正常。</div>'
        '</div></details>'
    )


# ============ 拼装器(无逻辑 concat) ============
def assemble_limitup(plates):
    return ''.join(plates)

# ============ 主入口(单测用) ============
def _ledger_days(d):
    """板块三日期集合(黄金版口径): 最新=当日(d), 历史=7 个更早交易日
    日期全集 = _ths_zt_pool.json 键 ∪ 涨停质量荐票_*.json 文件名, 取 <= d 的最近 8 天"""
    pool = load_zt_pool()
    ks = set(str(k) for k in pool.keys() if len(str(k)) == 8)
    import glob
    for f in glob.glob(os.path.join(L, '涨停质量荐票_20*.json')):
        m = re.search(r'(\d{8})\.json$', f)
        if m: ks.add(m.group(1))
    ks = sorted(k for k in ks if k <= d)
    return list(reversed(ks[-8:]))

def build_components(d):
    """渲染 limitup 页全部组件 → {组件ID: html片段}"""
    reco = load_recommend(d)
    q = load_quality()
    temp = load_temp()
    body = load_body(d)
    settle = load_settle()
    reflect = load_reflect()

    comps = {}
    # 板块一
    comps['C1.1'] = r_top5_table(reco, body)
    comps['C1.2'] = r_top5_insight(body)
    # 板块二: 全卡 = 市场温度.py 权威生成器(含 strip/温度卡/梯队/成绩单/规则榜/胜率库)
    comps['C2'] = r_temp_full(d)
    # 板块三: 整块 = bodies <!--LEDGER--> 原文(含最新日open+历史折叠, 黄金版逐字节)
    comps['C3'] = r_ledger_day(d, load_guiban(d), settle, body, d)
    comps['_days'] = _ledger_days(d)
    # 板块四/五/六
    comps['C4.1'] = r_factor_table(q, body)
    comps['C4.2'] = r_quality_folds(d)
    comps['C4.3'] = r_sweetspot()
    comps['C5.1'] = r_scan_card(body)
    comps['C5.2'] = r_selfcheck_card(body)
    comps['C6.1'] = r_cog_timeline(body) + r_cog_lib('limitup', d)
    comps['_body'] = body
    return comps

def build_page(d):
    """拼装完整 limitup 页 body(不含 shell) → 供 S2 接线"""
    comps = build_components(d)
    body = comps.get('_body', '')
    plates = [
        plate_top5(body, comps.get('C1.1', ''), comps.get('C1.2', '')),
        r_pool_out(d),
        plate_temp(body, comps.get('C2', '')),
        plate_ledger(comps.get('C3', '')),
        plate_train(body, comps.get('C4.1', ''), comps.get('C4.2', ''), comps.get('C4.3', '')),
        plate_scan(body, comps.get('C5.1', ''), comps.get('C5.2', '')),
        plate_cog(body, comps.get('C6.1', '')),
    ]
    return assemble_limitup(plates)

def build_page_full(d):
    """完整页 body(头部区 + PAPERTRADE 锚点 + 六板块) → S2 接线用
    头部区(bodies 开头 rowA/hero/kick/h1/导语/stance/kpi)从 bodies 提取(LLM 手写, 逐字节保真);
    PAPERTRADE 锚点必须输出 — 模拟盘引擎 inject 靠它替换注入看板(黄金版同构)。"""
    comps = build_components(d)
    body = comps.get('_body', '')
    # 头部区 = bodies 开头 到 <h2>一 (含 rowA/hero/kick/h1/导语/stance/kpi 卡区)
    head = ''
    i2 = body.find('<h2>一')
    if i2 > 0:
        head = body[:i2] + '\n'
    plates = [
        plate_top5(body, comps.get('C1.1', ''), comps.get('C1.2', '')),
        r_pool_out(d),
        plate_temp(body, comps.get('C2', '')),
        plate_ledger(comps.get('C3', '')),
        plate_train(body, comps.get('C4.1', ''), comps.get('C4.2', ''), comps.get('C4.3', '')),
        plate_scan(body, comps.get('C5.1', ''), comps.get('C5.2', '')),
        plate_cog(body, comps.get('C6.1', '')),
    ]
    return head + assemble_limitup(plates)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '20260716'
    comps = build_components(d)
    print('=== limitup 组件渲染单测 @%s ===' % d)
    total = 0
    for k in sorted(comps.keys()):
        if k.startswith('_'): continue
        v = comps[k]
        total += 1
        print('  %s: %d B | 卡%d 表%d' % (k, len(v), v.count('class="card"'), v.count('<table')))
    print('组件数: %d (不含元键)' % total)
    page = build_page(d)
    print('整页 body: %d KB | 卡%d 表%d 折叠%d' % (
        len(page) // 1024, page.count('class="card"'), page.count('<table'), page.count('<details')))
