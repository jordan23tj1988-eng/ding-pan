# -*- coding: utf-8 -*-
"""
limitup数据核对.py — 涨停页 bodies 手写数字 vs 数据源 机器核对哨兵
================================================================
动机(2026-08-11): 用户"再全面检查页面数据准确性,有错误从机制上避免。
你之前老是手抄错误的数据到新界面"——历史事故: ①豪尔赛"8天6板"误写
"6板高标"(真实今1板,最高6板=百花医药) ②哈药"5板"抄7/16(真实3板)
③kpi卡少1张 ④hero区高标张冠李戴。根因: 生成盯盘台.py只查PAPERTRADE
锚/重复标题,哨兵C9只查台账日期,C33只查文件存在——**没有任何环节核对
bodies手写数字 vs 数据源**,手抄错误靠用户逐卡验收才显形。

本脚本 = 内容级核对哨兵(6大维度), 接入生成盯盘台.py limitup分支:
  - 维度1 温度口径: 涨停/炸板/跌停/温度/最高板/梯队 vs _市场温度表.json
  - 维度2 高标股名: 最高连板股 vs zt_pool.csv 连板数列最大值
  - 维度3 Top5表: 名称/抓龙率/命中数 vs 涨停质量荐票_{d}.json
  - 维度4 台账日块: 58只首封/板数/封单比 vs zt_pool.csv
  - 维度5 归位口径: A/B/C档数/题材线数 vs 涨停对链条_{d}.json
  - 维度6 模拟盘看板: 持仓 vs 状态.json + 买入计划 vs 交易计划_{d}.json
用法: python limitup数据核对.py 20260811   (exit 0=全过, 1=有FAIL)
"""
import sys, os, csv, json, re, glob

R = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(R, '复盘', '盯盘台')
L = os.path.join(R, '_学习')


def load_page(d):
    p = os.path.join(SITE, 'limitup.html')
    if not os.path.exists(p):
        return None, 'limitup.html 不存在'
    return open(p, encoding='utf-8').read(), None


def load_pool(d):
    p = os.path.join(R, d, 'zt_pool.csv')
    if not os.path.exists(p):
        return None, f'{d}/zt_pool.csv 不存在'
    pool = {}
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        try:
            _ltsz = float(r.get('流通市值') or 0)
            _fbz = float(r.get('封板资金') or 0)
            pool[r['代码']] = {
                '名称': r['名称'], '连板': int(r['连板数']),
                '首封': r['首次封板时间'],
                '封单比': (_fbz / _ltsz * 100) if _ltsz > 0 else None,
                '涨停统计': r['涨停统计'],
            }
        except (ValueError, KeyError):
            pass
    return pool, None


def load_temp(d):
    p = os.path.join(L, '_市场温度表.json')
    if not os.path.exists(p):
        return None, '_市场温度表.json 不存在'
    j = json.load(open(p, encoding='utf-8'))
    if d not in j:
        # ★缺当日key必须显形: 返回None+err → 维度1 FAIL(曾返回(None,None)致temp['涨停数']崩)
        #   2026-08-12 温度表key断言验证时发现: 温度.py失败→表缺当日→哨兵Traceback而非FAIL
        return None, f'温度表无{d}条目(检查市场温度.py)'
    return j.get(d), None


def load_reco(d):
    for g in glob.glob(os.path.join(L, f'涨停质量荐票_{d}.json')):
        return json.load(open(g, encoding='utf-8')), None
    return None, f'涨停质量荐票_{d}.json 不存在'


def load_chain(d):
    for g in glob.glob(os.path.join(L, f'涨停对链条_{d}.json')):
        j = json.load(open(g, encoding='utf-8'))
        return j, None
    return None, f'涨停对链条_{d}.json 不存在'


def load_state():
    p = os.path.join(L, '_模拟盘', 'limitup', '状态.json')
    if not os.path.exists(p):
        return None, '状态.json 不存在'
    return json.load(open(p, encoding='utf-8')), None


def find_block(h, start_kw, end_kw, start_from=0):
    """页面 h 中 start_kw 到 end_kw 的区间, 找不到返回 (None, err)"""
    i = h.find(start_kw, start_from)
    if i < 0:
        return None, f'锚点 {start_kw} 未找到'
    j = h.find(end_kw, i + len(start_kw)) if end_kw else len(h)
    return h[i:j if j > 0 else len(h)], None


def hero_block(h):
    """手写判断区 = ticker起点(走马灯) 到 板块一h2之前. 含ticker/hero/kpi/pill/看板前.
    注意: ticker在<h1>之前, 老实现只扫<h1>~<h2>二会漏掉走马灯(用户8/11指正处)"""
    i = h.find('<div class="ticker">')
    if i < 0:
        i = h.find('<h1>')
    blk, _ = find_block(h, '', '<h2>二', start_from=i)
    if blk is None:
        blk = hero_block(h)
    return blk or ''


def name_match(pool, nm):
    """池中股票名匹配(页面用简称, 池用全称: 哈药→哈药股份/开开→开开实业)"""
    hit = [p for p in pool.values() if p['名称'] == nm or p['名称'].startswith(nm) or nm.startswith(p['名称'])]
    if len(hit) > 1:  # 前缀歧义(如 东方/东方财富) → 精确优先
        exact = [p for p in hit if p['名称'] == nm]
        return exact or hit
    return hit


def ticker_text(h):
    """走马灯文本(独立核对, 用户8/11指正处: 高标张冠李戴/抄昨日板数都出在这)"""
    i = h.find('<div class="ticker">')
    if i < 0:
        return ''
    j = h.find('</div>', i)
    seg = h[i:j]
    txt = re.sub(r'<[^>]+>', '', seg)
    return re.sub(r'&nbsp;?', '', txt)


def chk(issues, ok, label, detail=''):
    issues.append((ok, label, detail))


def _rate_variants(rate):
    """抓龙率数值等价串集: 数据源 16.0 应对上页面渲染 16%/16.0%(渲染器 _num 丢尾零)"""
    try:
        v = float(rate)
    except Exception:
        return {str(rate), str(rate) + '%'}
    s1 = ('%.1f' % v)
    s2 = s1.rstrip('0').rstrip('.')
    return {s1, s2, s1 + '%', s2 + '%'}


def main():
    if len(sys.argv) < 2:
        print('用法: python limitup数据核对.py <YYYYMMDD>'); return 2
    d = sys.argv[1]
    h, err = load_page(d)
    if err: print('FAIL', err); return 1
    issues = []
    fails = 0

    # ========== 维度1: 温度口径 (ticker/hero/kpi 分区核对) ==========
    temp, err = load_temp(d)
    if err:
        chk(issues, False, '温度表加载', err); fails += 1
    else:
        ttk = ticker_text(h)
        blk = hero_block(h)
        # ① ticker(走马灯)独立核对: 涨停数/温度 必现; 炸板/跌停走马灯通常写比率不写数
        tks = [('涨停数', str(temp['涨停数'])), ('温度', str(temp['温度']))]
        for lab, kw in tks:
            chk(issues, kw in ttk, f'ticker {lab}={kw}', '走马灯未出现' if kw not in ttk else '')
        # ② hero/kpi区(含kpi卡data-v): 涨停/炸板/跌停/温度 必须出现
        for lab, kw in [('涨停数', str(temp['涨停数'])), ('炸板数', str(temp['炸板数'])),
                        ('跌停数', str(temp['跌停数'])), ('温度', str(temp['温度']))]:
            chk(issues, bool(blk) and kw in blk, f'hero区 {lab}={kw}', 'hero区未出现' if not (blk and kw in blk) else '')
        # ③ 最高板: ticker 与 hero 都要有
        m6t = ttk and str(temp['最高板']) in ttk
        m6h = blk and ('最高板' in blk or '连板' in blk) and str(temp['最高板']) in (blk or '')
        chk(issues, bool(m6t), f'ticker 最高板={temp["最高板"]}', '走马灯无最高板口径' if not m6t else '')
        chk(issues, bool(m6h), f'hero 最高板={temp["最高板"]}', 'hero区无最高板口径' if not m6h else '')
        # ④ 梯队: 完整梯队数字在机器温度卡(权威生成), 手写区只要求关键提炼(如 2板12/16家)
        lv_any = False
        for lv, cnt in (temp.get('梯队') or {}).items():
            if f'{lv}板{cnt}' in (blk or '') or f'{lv}板{cnt}' in ttk:
                lv_any = True
        chk(issues, lv_any, f'手写区梯队提炼(含{len(temp.get("梯队") or {})}档中的≥1档)',
            'hero/ticker无任何梯队提炼' if not lv_any else '')
        # ⑤ 机器温度卡完整梯队核对
        tseg, _ = find_block(h, '二 市场温度', '三 归位台账')
        for lv, cnt in (temp.get('梯队') or {}).items():
            hit = tseg and str(cnt) in tseg
            chk(issues, bool(hit), f'温度卡梯队 {lv}板={cnt}',
                '温度卡未见' if not hit else '')

    # ========== 维度2: 高标股名 (连板数最大值股票, 防张冠李戴) ==========
    pool, err = load_pool(d)
    if err:
        chk(issues, False, 'zt_pool加载', err); fails += 1
    else:
        top_lb = max(p['连板'] for p in pool.values())
        top_stocks = [p['名称'] for p in pool.values() if p['连板'] == top_lb]
        blk = hero_block(h)
        ttk = ticker_text(h)
        # ① ticker 与 hero 必须出现最高板股名
        hit_t = ttk and any(s in ttk for s in top_stocks)
        hit_b = blk and any(s in blk for s in top_stocks)
        chk(issues, bool(hit_t), f'ticker 高标股名(最高{top_lb}连板={"/".join(top_stocks)})',
            '走马灯未出现最高板股' if not hit_t else '')
        chk(issues, bool(hit_b), f'hero 高标股名(最高{top_lb}连板={"/".join(top_stocks)})',
            'hero区未出现最高板股' if not hit_b else '')
        # ② 逐处核对"股名N板/连板"组合(防抄昨日板数/张冠李戴):
        #    剥离标签后正则提取, 池中真实连板必须匹配(名称前缀匹配: 哈药→哈药股份)
        bad = []
        for zone, ztxt in [('ticker', ttk), ('hero', re.sub(r'<[^>]+>', '', blk or ''))]:
            ztxt = re.sub(r'&nbsp;?', '', ztxt)
            # 股名在前: 百花医药6连板 / 哈药3板
            for m in re.finditer(r'([\u4e00-\u9fa5]{2,6})(\d+)连?板', ztxt):
                nm, bd = m.group(1), int(m.group(2))
                cands = name_match(pool, nm)
                if cands and cands[0]['连板'] != bd:
                    bad.append(f'{zone}:{nm}{bd}板(真实{cands[0]["连板"]}板,涨停统计{cands[0]["涨停统计"]})')
            # 股名在后(kpi卡): 6板·百花医药 / 6连板·XX
            for m in re.finditer(r'(\d+)连?板·([\u4e00-\u9fa5]{2,6})', ztxt):
                bd, nm = int(m.group(1)), m.group(2)
                cands = name_match(pool, nm)
                if cands and cands[0]['连板'] != bd:
                    bad.append(f'{zone}:{nm}{bd}板(真实{cands[0]["连板"]}板,涨停统计{cands[0]["涨停统计"]})')
        # ③ 涨停统计格式核对("8天6板" ↔ 池中涨停统计 8/6) + "全场最高"语义核对
        for zone, ztxt in [('ticker', ttk), ('hero', re.sub(r'<[^>]+>', '', blk or ''))]:
            ztxt = re.sub(r'&nbsp;?', '', ztxt)
            # 8天6板 格式: 与池中涨停统计比对
            for m in re.finditer(r'([\u4e00-\u9fa5]{2,6})(\d+)天(\d+)板', ztxt):
                nm, d1, d2 = m.group(1), int(m.group(2)), int(m.group(3))
                cands = name_match(pool, nm)
                if cands:
                    st = cands[0].get('涨停统计', '')
                    mst = re.match(r'(\d+)/(\d+)', st)
                    if mst and (int(mst.group(1)), int(mst.group(2))) != (d1, d2):
                        bad.append(f'{zone}:{nm}{d1}天{d2}板(真实涨停统计{st})')
            # "X全场最高" → X 必须是池中最高连板股(中间可夹板数描述: 百花医药6连板全场最高/豪尔赛8天6板全场最高)
            for m in re.finditer(r'([\u4e00-\u9fa5]{2,6})(?:\d+天\d+板|\d+连?板)?全场最高', ztxt):
                nm = m.group(1)
                cands = name_match(pool, nm)
                if cands and cands[0]['连板'] != top_lb:
                    bad.append(f'{zone}:{nm}标注全场最高但真实{cands[0]["连板"]}板(最高{top_lb}板)')
        # ④ kpi data-v 一致性: 显示值必须等于 data-v 属性(JS计数器覆盖显示, 手抄错会双双改错)
        for m in re.finditer(r'data-v="(\d+)"[^>]*>\s*(\d+)', blk or ''):
            dv, disp = int(m.group(1)), int(m.group(2))
            if dv != disp:
                chk(issues, False, 'kpi data-v一致性', f'data-v={dv} vs 显示={disp}')
        for b in bad:
            chk(issues, False, '高标口径', b)

    # ========== 维度3: Top5表 ==========
    reco, err = load_reco(d)
    if err:
        chk(issues, False, '荐票加载', err); fails += 1
    else:
        top5 = reco.get('top5') or []
        blk, _ = find_block(h, '一 涨停复盘', '<h2>二')
        for r in top5[:5]:
            nm, rate = r['名称'], str(r.get('抓龙率'))
            in_nm = blk and nm in blk
            in_rate = blk and any(vr in blk for vr in _rate_variants(rate))
            chk(issues, bool(in_nm and in_rate), f'Top5 {nm} 抓龙{rate}%',
                '' if (in_nm and in_rate) else f'表缺名称或抓龙率({nm},{rate})')

    # ========== 维度4: 台账日块 58只 (首封/板数/封单比) ==========
    if pool:
        # 最新日块 = <details class="chain" open> 之后 到 foldarchive
        i_open = h.find('<details class="chain" open>')
        i_fold = h.find('foldarchive', i_open) if i_open > 0 else -1
        if i_open > 0 and i_fold > 0:
            seg = h[i_open:i_fold]
            rows = re.findall(
                r'<td>(\d{2}:\d{2})</td><td><b>([^<]+)</b> <span class="mut">(\d{6})</span>\s*(?:<span[^>]*>[^<]*</span>\s*)?</td><td>封([\d.]+)% ?(<span class="tag2[^>]*>([^<]+)</span>)?',
                seg)
            chk(issues, len(rows) == len(pool), f'台账日块行数={len(rows)} vs 池={len(pool)}',
                '' if len(rows) == len(pool) else '行数不符(可能日块截断)')
            seen = set()
            for t, name, code, fd, _, tag in rows:
                seen.add(code)
                if code not in pool:
                    chk(issues, False, f'台账 {name}{code}', '池中无此票'); continue
                p = pool[code]
                pmin = p['首封'][:2] + ':' + p['首封'][2:4]
                if t != pmin:
                    chk(issues, False, f'{name} 首封', f'页面{t} vs 池{pmin}({p["首封"]})')
                if abs(float(fd) - p['封单比']) > 0.05:
                    chk(issues, False, f'{name} 封单比', f'页面{fd}% vs 池{round(p["封单比"],2)}%')
                if tag and re.match(r'^\d+板$', tag) and int(tag[:-1]) != p['连板']:
                    chk(issues, False, f'{name} 板数', f'页面{tag} vs 池{p["连板"]}(涨停统计{p["涨停统计"]})')
            miss = set(pool) - seen
            if miss:
                chk(issues, False, '台账缺票', ','.join(pool[c]['名称'] for c in sorted(miss)))
        else:
            chk(issues, False, '台账日块定位', f'open={i_open} fold={i_fold}')

    # ========== 维度5: 归位口径 ==========
    chain, err = load_chain(d)
    if err:
        chk(issues, False, '对链条加载', err); fails += 1
    else:
        blk = hero_block(h)
        # A/B/C 档数: 页面写 "归位58/A21/B33/C3" 或类似
        nA = sum(1 for it in chain.values() if isinstance(it, list) for x in it
                 if isinstance(x, dict) and x.get('来源档') == 'A')
        # 简单统计 override
        ovp = os.path.join(L, f'题材归位_{d}.json')
        if os.path.exists(ovp):
            ov = json.load(open(ovp, encoding='utf-8'))
            m = ov.get('映射', ov)
            cnt = {'A': 0, 'B': 0, 'C': 0}
            for v in m.values():
                if isinstance(v, dict):
                    cnt[v.get('来源档', 'B')] = cnt.get(v.get('来源档', 'B'), 0) + 1
            for k in 'ABC':
                kw = f'{k}{cnt[k]}'
                hit = blk and kw in blk
                chk(issues, bool(hit), f'归位档 {kw}', 'hero区未出现' if not hit else '')
        # ★归位json完整性: 映射数=池数(防漏归位, 2026-08-11事故: 创力603012漏+油气/煤炭线缺失)
        pool_m = load_pool(d) if 'load_pool' in dir() else None
        try:
            from importlib import import_module
            _m = import_module('module_render_limitup')
            _pool = _m.load_zt_pool().get(d, [])
            pcodes = set(str(x.get('code', '')).zfill(6) for x in _pool)
            mcodes = set(str(k).zfill(6) for k in m.keys())
            miss = pcodes - mcodes
            chk(issues, not miss, '归位映射=池数', ('池中未归位: %s' % sorted(miss)) if miss else '')
            # json 线数 vs bodies 当日组数
            _b = _m.load_body(d)
            _i = _b.find('<details class="chain" open>')
            _j = _b.find('<details class="chain">', _i + 10)
            _seg = _b[_i:_j] if _i > 0 else ''
            _g = set(re.findall(r'【([^】]+)】', _seg))
            _jlines = set(str(v.get('大方向')) for v in m.values())
            diff = (_g - _jlines) - {'待归位 · 行业兜底'}  # 待归位是特殊行(行业兜底),非大方向
            chk(issues, not diff, '归位线=bodies组', ('bodies有json无: %s' % sorted(diff)) if diff else '')
        except Exception as _ex:
            chk(issues, False, '归位完整性校验', '执行异常: %s' % _ex)

    # ========== 维度6: 模拟盘看板 ==========
    st, err = load_state()
    if err:
        chk(issues, False, '模拟盘状态加载', err); fails += 1
    else:
        blk, _ = find_block(h, 'PAPER TRADING', '一 涨停复盘')
        for pos in st.get('持仓', []):
            nm = pos.get('name') or pos.get('名称')
            sh = pos.get('shares') or pos.get('数量')
            hit = blk and nm in blk and str(sh) in blk
            chk(issues, bool(hit), f'持仓 {nm} {sh}股', '看板未显示' if not hit else '')
        # 交易计划 (若存在)
        tp = os.path.join(L, f'交易计划_limitup_{d}.json')
        if os.path.exists(tp):
            plan = json.load(open(tp, encoding='utf-8'))
            for it in (plan.get('计划') or plan.get('买') or []):
                nm = it.get('名称') or it.get('name')
                if nm:
                    hit = blk and nm in blk
                    chk(issues, bool(hit), f'买入计划 {nm}', '看板未显示' if not hit else '')

    # ========== 维度7: HTML结构平衡 (防wrap被提前闭合致全宽溢出) ==========
    # 2026-08-11事故: ticker手拼多1个</div> → wrap提前闭合 → rowA+32表格脱离容器全宽渲染
    body = h[h.find('<body'):]
    dop = len(re.findall(r'<div[\s>]', body))
    dcl = len(re.findall(r'</div>', body))
    chk(issues, dop == dcl, f'HTML div平衡 开{dop}闭{dcl}', '' if dop == dcl else 'div不配平,结构被破坏!')
    # wrap 闭合前必须含 rowA 起点(wrap 内包含全部内容)
    wi = body.find('class="wrap"')
    ra = body.find('rowA', wi)
    chk(issues, ra > 0, 'rowA 在 wrap 内', 'rowA 未找到或不在 wrap 内' if ra <= 0 else '')
    # ticker 必须闭合(结构锚: ticker 后紧跟 <div class="rowA">, 无多余</div>)
    tk = body.find('<div class="ticker">')
    rw = body.find('<div class="rowA">', tk)
    tk_end = body[tk:rw].count('</div>') if tk > 0 and rw > 0 else -1
    # ticker 内: ticker+in+grp+grp=4开 → 应恰4闭
    chk(issues, tk_end == 4, f'ticker闭合数={tk_end}(应4)', '' if tk_end == 4 else 'ticker div未正确闭合,wrap会提前闭合!' if tk_end < 4 else 'ticker div多闭合,wrap会被误闭!')

    # ========== 维度8: 元信息事实校验 (防LLM自由文本抄历史旧数据) ==========
    # 2026-08-11二次事故: 题材归位"来源"写"哈药5板"(实3板/7-16旧数)、judgment"一句话"写"豪尔赛6板高标"(实百花医药6板)
    # 根因=LLM写元信息时引用历史日块,未用当日真源交叉核验;上次哨兵只校验页面渲染层,未覆盖数据文件元信息层
    try:
        jp8 = os.path.join(L, f'judgment_{d}.json')
        gp8 = os.path.join(L, f'题材归位_{d}.json')
        tsrc8 = os.path.join(L, '_市场温度表.json')
        if os.path.isfile(jp8) and os.path.isfile(gp8) and os.path.isfile(tsrc8):
            jj8 = json.load(open(jp8, encoding='utf-8'))
            gg8 = json.load(open(gp8, encoding='utf-8'))
            # ★字段存在性断言: 组件改动可能连带删字段 → 缺字段必须 FAIL, 不许静默跳过(2026-08-12场景2实测)
            f_miss8 = []
            if not jj8.get('一句话'):
                f_miss8.append('judgment.一句话')
            if not gg8.get('来源'):
                f_miss8.append('题材归位.来源')
            if f_miss8:
                chk(issues, False, '元信息字段存在性', '缺失: %s' % '、'.join(f_miss8))
            trow8 = (json.load(open(tsrc8, encoding='utf-8')) or {}).get(d) or {}
            # ★温度表当日 key 存在性断言: 温度表缺当日 → 温度/涨停检查静默跳过(2026-08-12审计发现)
            #   温度.py 失败时温度表无当日 key, 维度8 会"显示PASS实际没查"——必须显形
            if not trow8:
                chk(issues, False, '温度表当日key存在性', f'温度表无{d}条目,温度/涨停引用检查失效,检查市场温度.py')
            # ★扫描范围: 一句话 + 来源 + bodies当日区(hero/h1/hint/规则榜 + 当日块, 历史日块存档除外)
            #    2026-08-12场景3实测: 组件改动常在wrap/hero区加LLM手写文案, 只扫当日块会漏
            bd8 = (jj8.get('bodies') or {}).get('limitup') or ''
            kb8 = bd8.find('<details class="chain" open>')
            if kb8 >= 0:
                jb8 = bd8.find('<details class="chain">', kb8 + 10)
                seg_open8 = bd8[kb8: jb8 if jb8 > 0 else kb8 + 60000]  # 当日块(open)
                seg_head8 = bd8[:kb8]  # 当日区头部(hero/h1/hint/规则榜, 历史块都在open之后不误扫)
            else:
                seg_open8 = seg_head8 = ''
            bd8 = re.sub(r'<[^>]+>', ' ', seg_head8 + seg_open8)  # 剥离标签
            yj8 = (jj8.get('一句话') or '') + ' ' + (gg8.get('来源') or '') + ' ' + bd8
            # 权威事实: 最高板/温度/涨停数 全部从温度表取(单一真源)
            mx8 = int(trow8.get('最高板') or 0)
            wd_true8 = trow8.get('温度')
            zt_true8 = int(trow8.get('涨停数') or 0)
            # 最高板票名: 池 high_days 解析连续板(天==板), 与温度表最高板核对
            zp8 = os.path.join(L, '_ths_zt_pool.json')
            top8 = []
            if os.path.isfile(zp8):
                pool8 = (json.load(open(zp8, encoding='utf-8')) or {}).get(d) or []
                def _ban8(p):
                    m = re.search(r'(\d+)\s*板', str(p.get('high_days', '')))
                    return int(m.group(1)) if m else 0
                def _days8(p):
                    m = re.search(r'(\d+)\s*天', str(p.get('high_days', '')))
                    return int(m.group(1)) if m else 0
                top8 = [p.get('name') for p in pool8
                        if _ban8(p) == mx8 and _days8(p) == mx8]  # 天==板=连续板
            # a) 板数引用逐票核验: 文本"票名+N板" vs 池中该票真实连板数(天==板=连续板才核验)
            #    只查"≤最高板"测不出"哈药5板"(实3板,5<6)这类错,必须逐票对账
            poolname8 = {}
            if os.path.isfile(zp8):
                pool8 = (json.load(open(zp8, encoding='utf-8')) or {}).get(d) or []
                for p in pool8:
                    dm = re.search(r'(\d+)\s*天\s*(\d+)\s*板', str(p.get('high_days', '')))
                    if dm and int(dm.group(1)) == int(dm.group(2)):
                        poolname8[p.get('name')] = int(dm.group(2))  # 连续板票: 名→真实板数
            for mm in re.finditer(r'([\u4e00-\u9fa5]{2,8})\s*(\d+)\s*板', yj8):
                nm8, bn8 = mm.group(1), int(mm.group(2))
                # ★票名匹配: 正则贪婪会抓"今日哈药"(4字)而非"哈药"(2字) → 后缀逐段双向包含,
                #    2026-08-12场景实测: 全串匹配"今日哈药"in"哈药股份"=False漏检, 后缀"哈药"才命中
                real8 = None
                for _ln8 in range(len(nm8), 1, -1):
                    _tail8 = nm8[-_ln8:]
                    _hit8 = next((v for k, v in poolname8.items() if _tail8 in k or k in _tail8), None)
                    if _hit8 is not None:
                        real8 = _hit8
                        break
                if real8 is not None and bn8 != real8:
                    chk(issues, False, f'元信息板数引用 {nm8}{bn8}板', f'池中{nm8}实为{real8}板,疑似抄历史')
            # b) 高标表述: 一句话里"X高标"的 X 必须含最高板票名(允许中间带"6板"等)
            gm8 = re.search(r'([\u4e00-\u9fa5]{2,8})(?:\d+天\d+板|\d+连?板)?高标', jj8.get('一句话') or '')
            ok_high8 = any(t in gm8.group(1) for t in top8) if (gm8 and top8) else True
            chk(issues, ok_high8, '一句话高标=映射最高板', '' if ok_high8 else f'高标"{gm8.group(1)}"≠连续最高板{top8}')
            # c) 温度引用: 与温度表交叉 (正则须整数部分必在, 防匹配孤立".")
            wd8 = re.search(r'温度\s*([0-9]+(?:\.[0-9]+)?)', yj8)
            if wd8 and wd_true8 is not None and abs(float(wd8.group(1)) - float(wd_true8)) > 0.05:
                chk(issues, False, '元信息温度引用', f'文本{wd8.group(1)} vs 温度表{wd_true8}')
            # d) 涨停数引用: 与温度表交叉
            zt8 = re.search(r'涨停\s*(\d+)', yj8)
            if zt8 and zt_true8 and int(zt8.group(1)) != zt_true8:
                chk(issues, False, '元信息涨停数引用', f'文本{zt8.group(1)} vs 温度表{zt_true8}')
    except Exception as _e8:
        chk(issues, False, '元信息事实校验', '执行异常: %s' % _e8)

    # ========== 汇总 ==========
    fails = sum(1 for ok, _, _ in issues if not ok)
    print(f'=== limitup数据核对 {d}: {len(issues)-fails}/{len(issues)} 通过 ===')
    for ok, lab, det in issues:
        print(('  ✓ ' if ok else '  ✗ ') + lab + (f'  [{det}]' if det else ''))
    if fails:
        print(f'FAIL {fails} 项 — 页面数字与数据源不一致, 禁止出页')
        return 1
    print('PASS 全部一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
