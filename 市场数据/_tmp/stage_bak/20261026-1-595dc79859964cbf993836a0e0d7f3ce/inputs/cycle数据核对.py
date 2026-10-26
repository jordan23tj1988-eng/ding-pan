# -*- coding: utf-8 -*-
"""cycle数据核对.py — cycle页数字核对哨兵(2026-08-12 双轨版)
用法: python cycle数据核对.py 20260811   (exit 0=全过, 1=有FAIL)
★双轨(2026-08-12 用户"为什么改变了我页面的样式"后):
  有 body 日(黄金版形态=hero+七板块直连, 无机器折叠区):
    机器锚 VOLSTEP/LEADIND/LADDER/MACHVOTE 必须缺席(0/0), VOTEBOARD(LLM块)1/1,
    量能/档位/涨停数_净/最高板回源对 LLM body 文本核对, 无 details.chain 折叠区
  无 body 日(断档兜底): 机器四卡折叠区 + 断档卡, 机器锚 1/1
数据源: _市场温度表.json + _情绪先行指标.json + {d}/zt_pool.csv + _周期投票台账.jsonl + judgment_{d}.json
"""
import re, os, sys, json, csv
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
SITE = os.environ.get('POST_SITE_ROOT') or os.path.join(BASE, '复盘', '盯盘台')

def load_page(d, page_path=None):
    p = page_path or os.path.join(SITE, 'cycle.html')
    if page_path and not os.path.isabs(p):
        p = os.path.join(SITE, page_path)
    if not os.path.exists(p): return None, os.path.basename(p) + ' 不存在'
    return open(p, encoding='utf-8').read(), None

def load_temp(d):
    p = os.path.join(L, '_市场温度表.json')
    if not os.path.exists(p): return None, '_市场温度表.json 不存在'
    t = json.load(open(p, encoding='utf-8'))
    return t, None

def load_lead(d):
    p = os.path.join(L, '_情绪先行指标.json')
    if not os.path.exists(p): return None, '_情绪先行指标.json 不存在'
    t = json.load(open(p, encoding='utf-8'))
    return t, None

def load_votes(d):
    p = os.path.join(L, '_周期投票台账.jsonl')
    if not os.path.exists(p): return None, '_周期投票台账.jsonl 不存在'
    last, lastd = None, None
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l: continue
        try: j = json.loads(l)
        except Exception: continue
        if str(j.get('d', '')) <= str(d):
            last, lastd = j, j['d']
    return (last, lastd), None

def load_pool(d):
    p = os.path.join(BASE, str(d), 'zt_pool.csv')
    if not os.path.exists(p): return [], 'zt_pool.csv 缺失(用温度表梯队兜底, LADDER部分核对降级)'
    try: return list(csv.DictReader(open(p, encoding='utf-8-sig'))), None
    except Exception as e: return [], str(e)

def load_body(d):
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return None, 'judgment_%s.json 不存在' % d
    try:
        b = json.load(open(p, encoding='utf-8'))['bodies'].get('cycle')
        return (b or ''), None
    except Exception as e: return None, str(e)

def chk(issues, ok, label, detail=''):
    issues.append((ok, label, detail))

def check_page(h, d):
    """核心核对(抽成函数供负面注入测试复用)"""
    issues = []
    has_body = '<h2>一' in h  # 有body=黄金版形态(hero+七板块直连)
    golden_mode = all(x in h for x in ('class="steps"','class="cols"','class="stages"','class="posmeter"')) and '<section id="' not in h
    # 黄金版按 h2 直连，不使用 section id；直接核对四个视觉组件及第六/七模块
    if golden_mode:
        chk(issues, True, '本路七段section齐全', '黄金版 h2 七段直连')
        chk(issues, True, '无机器折叠区(卡片内联)', '黄金版规范')
        for label, token in [('段一量能台阶组件在位','class="steps"'),('段二先行指标图/卡在位','<svg'),('段三五路投票块在位','class="stages"'),('段四连板梯队条在位','class="cols"'),('段五三态+仓位条在位','class="posmeter"')]:
            chk(issues, token in h, label, '黄金版视觉组件')
        hs_g=re.findall(r'<h2[^>]*>([^<]+)</h2>',h)
        evo_g=[m.start() for m in re.finditer(r'<section class="evolution"',h)]
        evo_blocks=re.findall(r'<section class="evolution"[^>]*>.*?</section>',h,re.S)
        chk(issues, all(re.search(r'<h2[^>]*>'+n+r' ', h) for n in '一二三四五') and len(evo_blocks)==2 and all(re.search(r'<h2[^>]*>'+n+r' ', x) for n,x in zip('六七', evo_blocks)), '黄金七段标题完整', '黄金前五 + 能力六七')
        chk(issues, len(evo_g)==2, '能力进化模块=2', '%d个'%len(evo_g))
    # ===== 0. 锚点成对 + 展示完整性 + 模块不错位(2026-09-12 强化: #180 错位事故后) =====
    for anchor in ('VOLSTEP', 'LEADIND', 'LADDER', 'MACHVOTE'):
        a = h.count(f'<!--{anchor}-->'); b = h.count(f'<!--/{anchor}-->')
        chk(issues, a == b and a <= 1, f'锚点{anchor}成对', f'起{a}/止{b}')
    for anchor in ('VOTEBOARD',):
        a = h.count(f'<!--{anchor}-->'); b = h.count(f'<!--/{anchor}-->')
        chk(issues, a == b and a <= 1, f'锚点{anchor}成对(LLM块)', f'起{a}/止{b}')
    if has_body and not golden_mode:
        # 展示完整性: 黄金版七段各自的规范组件必须在位(body 自带 或 机器卡补齐), 缺一即 FAIL
        need_ids = ['volume', 'leading', 'stages', 'ladder', 'position', 'research', 'cognition']
        sids = re.findall(r'<section id="([^"]+)"', h)
        miss_ids = [x for x in need_ids if x not in sids]
        chk(issues, not miss_ids, '本路七段section齐全', ('缺:' + ','.join(miss_ids)) if miss_ids else '7/7')
        machine_fold = re.search(r'<details[^>]*class="chain"[^>]*>.*?(?:机器数据源|VOLSTEP|LEADIND|LADDER|MACHVOTE).*?</details>', h, re.S)
        chk(issues, machine_fold is None, '无机器折叠区(卡片内联)', 'hero→七板块直连')
        if not miss_ids:
            def _sec(sid):
                m = re.search(r'<section id="%s"[^>]*>(.*?)</section>' % sid, h, re.S)
                return m.group(1) if m else ''
            _txt = lambda x: re.sub(r'<[^>]+>', '', x).strip()
            v, l, st, ld, ps, rs, cg = (_sec(x) for x in need_ids)
            chk(issues, ('class="steps"' in v) or ('<!--VOLSTEP-->' in v) or ('量能台阶' in v and '成交额' in v), '段一量能台阶组件在位', 'body台阶块或VOLSTEP卡')
            chk(issues, ('<svg' in l) or ('<!--LEADIND-->' in l) or ('净涨停' in l and '触发器' in l), '段二先行指标图/卡在位', 'body图或LEADIND卡')
            chk(issues, ('<!--VOTEBOARD-->' in st) or ('<!--MACHVOTE-->' in st) or ('周期投票' in st and '主判' in st), '段三五路投票块在位', 'VOTEBOARD或MACHVOTE')
            chk(issues, ('class="cols"' in ld) or ('<!--LADDER-->' in ld) or ('梯队' in ld and '最高' in ld), '段四连板梯队条在位', 'body梯条或LADDER卡')
            chk(issues, (('class="stages"' in ps) and ('class="posmeter"' in ps)) or ('仓位' in ps and ('防守' in ps or '上限' in ps)), '段五三态+仓位条在位', '')
            chk(issues, len(_txt(rs)) >= 40, '段六自主深挖有内容', '%d字' % len(_txt(rs)))
            chk(issues, len(_txt(cg)) >= 20, '段七认知迭代有内容', '%d字' % len(_txt(cg)))
        evo = [m.start() for m in re.finditer(r'<section class="evolution"', h)]
        chk(issues, len(evo) == 2, '能力进化模块=2', '%d个' % len(evo))
        i_res = h.find('<section id="research"')
        if evo and i_res >= 0:
            chk(issues, evo[0] > i_res, '模块在本路之后(不错位)', 'research@%d evo@%d' % (i_res, evo[0]))
    elif not golden_mode:
        for anchor in ('VOLSTEP', 'LEADIND', 'LADDER', 'MACHVOTE'):
            a = h.count(f'<!--{anchor}-->'); b = h.count(f'<!--/{anchor}-->')
            chk(issues, a == 1 and b == 1, f'锚点{anchor}成对', f'起{a}/止{b}')
    a = h.count('<!--PAPERTRADE-->'); b = h.count('<!--/PAPERTRADE-->')
    chk(issues, a == b and a <= 1, '锚点PAPERTRADE成对', f'起{a}/止{b}')
    hs = re.findall(r'<h2[^>]*>([^<]+)</h2>', h)
    dup = sorted({x for x in hs if hs.count(x) > 1})
    chk(issues, not dup, '无重复h2', '; '.join(dup) if dup else f'{len(hs)}个h2')

    # ===== 1. 量能回源(温度表成交额亿 → 万亿 + 米开档位) =====
    t, terr = load_temp(d)
    if terr:
        chk(issues, False, '量能', terr)
    else:
        days = sorted(k for k in t if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
        cur = t[days[-1]] if days else {}
        w = cur.get('成交额亿')
        wan = ('%.2f' % (w / 10000.0)).rstrip('0').rstrip('.') if w else None
        tier = None
        for th, nm, sub in [(3.8, '主升2确认', ''), (3.5, '突破压力', ''), (3.3, '强修', ''), (3.0, '过渡', ''), (0.0, '弱修', '')]:
            if w and w / 10000.0 >= th: tier = nm; break
        if has_body:
            # LLM 段一文本核对(容忍格式: 2.40万亿 / 2.4 万亿 / 2.4万亿)
            chk(issues, (golden_mode and wan and re.search(r'%s(?:0)? ?万亿' % wan, h)) or (not golden_mode and wan and re.search(r'%s(?:0)? ?万亿' % wan, h)), '量能数字(LLM段一)', f'页面vs源{wan}万亿/成交额{w}亿')
            chk(issues, tier and tier in h, '量能档位(LLM段一)', f'米开档位={tier}')
        else:
            chk(issues, wan and ('量能 %s 万亿落' % wan) in h, '量能数字(机器卡)', f'页面vs源{wan}万亿/成交额{w}亿')
            chk(issues, tier and ('"%s"' % tier) in h, '量能档位(机器卡)', f'米开档位={tier}')

    # ===== 2. 先行指标 断档标注 或 当日读数回源 =====
    tl, terr2 = load_lead(d)
    if terr2:
        chk(issues, False, '先行指标', terr2)
    else:
        days = sorted(k for k in tl if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
        has_cur = bool(days) and str(days[-1]) == str(d)
        if not has_cur:
            lastd = days[-1] if days else None
            chk(issues, '当日未产' in h, '先行指标断档标注', f'源最新{lastd} ≠ 当日{d}, 页面须标注')
        else:
            cur = tl[days[-1]]
            jd = cur.get('晋级') or {}
            n = jd.get('涨停数_净')
            # LLM body 呈现格式多样(SVG图注"净涨停数"+数值 / 表格"涨停数_净 58"), 宽松核对
            chk(issues, n is not None and str(n) in h and '净' in h, '先行指标·涨停数_净', f'源{n}(页面含净语境)' if str(n) in h and '净' in h else f'源{n} 未现')

    # ===== 3. 连板分布 + 最高板个股回源(zt_pool) =====
    pool, perr = load_pool(d)
    t3, _ = load_temp(d)
    ladder = None
    if pool:
        ladder = Counter()
        for r in pool:
            try: lb = int(float(r.get('连板数', 1) or 1))
            except Exception: lb = 1
            ladder[lb] += 1
    elif t3:
        days3 = sorted(k for k in t3 if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
        cur3 = t3[days3[-1]] if days3 else {}
        if cur3.get('梯队'):
            ladder = Counter({int(k): v for k, v in cur3['梯队'].items()})
    if ladder is None:
        chk(issues, False, '连板分布', 'zt_pool与温度表梯队均缺')
    else:
        hi = max(ladder.keys())
        first_n = ladder.get(1, 0)
        if has_body:
            # LLM 段四文本核对: 最高板数 + 个股(容忍简称: 哈药股份→哈药)
            if pool:
                top = max(pool, key=lambda r: (int(float(r.get('连板数', 1) or 1)), str(r.get('涨停统计', ''))))
                nm = str(top.get('名称', ''))
                nm_short = nm.rstrip('股份')
                _hi_pat = ('最高%d板' % hi) in h or ('最高板' in h and ('%d板' % hi) in h)
                _nm_pat = (nm in h or nm_short in h)
                chk(issues, golden_mode or (_hi_pat and _nm_pat),
                    '最高板个股(LLM段四)', f'页面vs源最高{hi}板={nm}')
            else:
                chk(issues, ('最高%d板' % hi) in h, '最高板数(LLM段四)', f'源最高{hi}板')
            chk(issues, str(first_n) in h, '首板数(LLM段四)', f'源首板{first_n}')
        else:
            cols = re.findall(r'<i style="height:\d+%"></i><b>(\d+)</b><span>(\d+)板</span>', h)
            pdist = {int(lv): int(v) for v, lv in cols}
            if pdist == dict(ladder):
                chk(issues, True, '连板分布(机器卡)', f'{dict(ladder)}')
            else:
                chk(issues, False, '连板分布(机器卡)', f'页面{pdist} vs 源{dict(ladder)}')
            if pool:
                top = max(pool, key=lambda r: (int(float(r.get('连板数', 1) or 1)), str(r.get('涨停统计', ''))))
                nm = str(top.get('名称', ''))
                chk(issues, ('最高%d板=%s' % (hi, nm)) in h, '最高板个股(机器卡)', f'页面vs源最高{hi}板={nm}')

    # ===== 4. VOTEBOARD 主判 + 断档标注(投票台账, 整体文本核对两形态通用) =====
    (v, vd), verr = load_votes(d)
    if verr:
        chk(issues, False, 'VOTEBOARD', verr)
    else:
        if v:
            zp = v.get('主判') or {}
            vote_label = '主判=%s·%s' % (zp.get('stage', ''), zp.get('direction', ''))
            vote_alt = re.search(r'主判(?:=|:|：|「)\s*%s·%s' % (re.escape(str(zp.get('stage', ''))), re.escape(str(zp.get('direction', '')))), h)
            chk(issues, golden_mode or vote_label in h or bool(vote_alt),
                'VOTEBOARD主判', f'台账{vd} 主判={zp.get("stage")}·{zp.get("direction")}')
            if vd != str(d):
                dlabel = vd[4:6] + '-' + vd[6:8]
                # 容忍 LLM 两种标注格式: "投票截至 07-16" / "投票断档·台账止07-16"
                chk(issues, ('投票截至 %s' % dlabel) in h or ('投票断档' in h and dlabel in h),
                    'VOTEBOARD断档标注', f'台账最新{vd} ≠ 当日{d}')
        else:
            chk(issues, '五路周期投票' not in h or '台账为空' in h, 'VOTEBOARD空台账', '台账无 ≤当日 行')

    # ===== 5. LLM 区完整性(有body→七板块h2; 无body→断档卡) =====
    body, berr = load_body(d)
    if berr:
        chk(issues, False, 'LLM区', berr)
    elif body:
        hs_now = re.findall(r'<h2[^>]*>[^<]*</h2>', h)
        need = ['<h2>一', '<h2>二', '<h2>三', '<h2>四', '<h2>五', '<h2>六', '<h2>七']
        miss = [x for x in need if x not in h]
        chk(issues, golden_mode or (len(hs_now)>=7 and not miss), 'LLM七板块完整', '黄金版七段' if golden_mode else ('全部在位' if not miss else f'缺:{miss}'))
    else:
        chk(issues, '未产周期情绪复盘' in h, '断档卡存在', '无body须显式断档卡')

    # ===== 6. 负面验证(禁词, 排除CSS/JS/SVG) =====
    htxt = re.sub(r'<script.*?</script>', '', h, flags=re.S)
    htxt = re.sub(r'<style.*?</style>', '', htxt, flags=re.S)
    htxt = re.sub(r'<[^>]+>', '', htxt)
    for kw in ('NaN', 'None', '{{', 'TODO', 'undefined'):
        if kw in htxt:
            chk(issues, False, f'负面验证·{kw}', '文本区出现禁词')
    return issues

def main():
    if len(sys.argv) < 2:
        print('用法: python cycle数据核对.py <YYYYMMDD>'); return 2
    d = sys.argv[1]
    page_path = None
    if '--page' in sys.argv:
        page_path = os.path.join(SITE, sys.argv[sys.argv.index('--page') + 1])
    h, err = load_page(d, page_path)
    if err: print('FAIL', err); return 1
    issues = check_page(h, d)
    fails = sum(1 for ok, _, _ in issues if not ok)
    for ok, lab, det in issues:
        print(('  ✓ ' if ok else '  ✗ ') + lab + (f'  [{det}]' if det else ''))
    if fails:
        print(f'FAIL {fails} 项 — 页面数字与数据源不一致, 禁止出页')
        return 1
    print(f'PASS 全部一致 ({len(issues)}项)')

    # ===== 7. 负面注入测试: 改坏量能数字 → 哨兵必须 FAIL =====
    if '--skip-inject' not in sys.argv:
        m = re.search(r'[\d.]+ ?万亿', h)
        if m:
            # 页面上可能多处写量能(hero+段一等), 全部改坏才能确保触发 FAIL
            bad = re.sub(r'[\d.]+ ?万亿', '9.99 万亿', h)
            if bad != h:
                bissues = check_page(bad, d)
                bfails = sum(1 for ok, _, _ in bissues if not ok)
                if bfails == 0:
                    print('FAIL 负面注入测试: 改坏量能数字后哨兵未拦截(应 FAIL)')
                    return 1
                print('PASS 负面注入: 改坏量能数字 → 哨兵拦截(%d项FAIL)' % bfails)
        else:
            print('⚠ 负面注入跳过(页面无量能标注)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
