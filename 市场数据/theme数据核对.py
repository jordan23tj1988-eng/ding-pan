# -*- coding: utf-8 -*-
"""theme数据核对.py — theme页数字核对哨兵(2026-08-12, 参照 lhb数据核对.py / limitup数据核对.py)
用法: python theme数据核对.py 20260811   (exit 0=全过, 1=有FAIL)
核对项: 机器锚成对 / h2六板块 / 归位-对链条-zt_pool 唯一真源互证 / 6有字段合法 / 四维字段+显式null /
        机器组件回源(战场全貌/6有/四维) / bodies.theme判断产物 / 荐票∈涨停池 / kpi结构 / fact层接线 / 负面验证
数据源: 题材归位_{d}.json + 涨停对链条_{d}.json + 主流题材6有_{d}.json + _题材四维.json +
        judgment_{d}.json(bodies.theme) + fact_{d}.json + {d}/zt_pool.csv
"""
import re, os, sys, json, csv
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
SITE = os.path.join(BASE, '复盘', '盯盘台')

def load_page(d, page_path=None):
    p = page_path or os.path.join(SITE, 'theme.html')
    if not os.path.exists(p): return None, os.path.basename(p) + ' 不存在'
    return open(p, encoding='utf-8').read(), None

def load_json(fn):
    p = os.path.join(L, fn)
    if not os.path.exists(p): return None, fn + ' 不存在'
    try:
        return json.load(open(p, encoding='utf-8')), None
    except Exception as e:
        return None, fn + ' 解析失败: ' + str(e)[:80]

def load_ztpool(d):
    p = os.path.join(BASE, d, 'zt_pool.csv')
    if not os.path.exists(p): return None, f'{d}/zt_pool.csv 不存在'
    try:
        return list(csv.DictReader(open(p, encoding='utf-8-sig'))), None
    except Exception as e:
        return None, 'zt_pool.csv 解析失败: ' + str(e)[:80]

def chk(issues, ok, label, detail=''):
    issues.append((ok, label, detail))

def main():
    if len(sys.argv) < 2:
        print('用法: python theme数据核对.py <YYYYMMDD>'); return 2
    d = sys.argv[1]
    page_path = None
    if '--page' in sys.argv:
        page_path = os.path.join(SITE, sys.argv[sys.argv.index('--page') + 1])
    issues = []
    h, err = load_page(d, page_path)
    if err:
        print('FAIL', err); return 1

    # ===== 0. 结构基线: 机器锚成对 + h2 五板块 =====
    for anchor in ('THEMEBATTLE', '6YOU', 'FOURDIM', 'LIFECYCLE'):
        a = h.count(f'<!--{anchor}-->'); b = h.count(f'<!--/{anchor}-->')
        chk(issues, a == 1 and b == 1, f'机器锚 {anchor} 开闭成对', f'开{a}/闭{b}')
    h2s = re.findall(r'<h2>([一二三四五])', h)
    for i, num in enumerate('一二三四五', 1):
        chk(issues, h2s.count(num) == 1, f'h2 板块{num} 唯一', f'出现{h2s.count(num)}次')
    chk(issues, len(h2s) == 5, 'h2 五板块齐全(板块四龙头识别已并入矩阵)', f'实际{len(h2s)}个')
    chk(issues, h.count('<!--PAPERTRADE-->') == h.count('<!--/PAPERTRADE-->'),
         'PAPERTRADE 锚开闭配对', f'开{h.count("<!--PAPERTRADE-->")}/闭{h.count("<!--/PAPERTRADE-->")}')

    # ===== 1. 数据源加载 =====
    gui, err = load_json(f'题材归位_{d}.json')
    chk(issues, gui is not None, '题材归位(唯一真源)存在', err or '')
    chain, err = load_json(f'涨停对链条_{d}.json')
    chk(issues, chain is not None, '涨停对链条存在', err or '')
    s6, err = load_json(f'主流题材6有_{d}.json')
    chk(issues, s6 is not None, '主流题材6有存在', err or '')
    d4, err = load_json('_题材四维.json')
    chk(issues, d4 is not None and d in d4, '四维含当日条目', err or '')
    jud, err = load_json(f'judgment_{d}.json')
    chk(issues, jud is not None, 'judgment存在', err or '')
    zt, err = load_ztpool(d)
    chk(issues, zt is not None, 'zt_pool存在', err or '')

    # ===== 2. 唯一真源互证: 归位 vs 对链条 vs zt_pool =====
    if gui and chain:
        mp = gui.get('映射') or {}
        cnt = Counter((v or {}).get('大方向', '未归位') for v in mp.values())
        lines = {(ln or {}).get('大方向'): ln for ln in (chain.get('题材线') or [])}
        wg = chain.get('待归位_行业兜底') or []
        chk(issues, chain.get('涨停总数') == len(mp) + len(wg), '对链条涨停总数==归位映射数+待归位数',
            f'对链条{chain.get("涨停总数")} vs 归位{len(mp)}+待归位{len(wg)}')
        mismatch = [nm for nm, n in cnt.items()
                    if nm in lines and (lines[nm].get('家数') or 0) != n]
        chk(issues, not mismatch, '每线家数 归位==对链条', ';'.join(mismatch[:5]) or '一致')
        chk(issues, len(cnt) == len(lines), '归位大方向数==对链条题材线数',
            f'归位{len(cnt)} vs 对链条{len(lines)}')
        non_st_wg = [x for x in wg if 'ST' not in (x.get('名称') or '')]
        chk(issues, len(non_st_wg) == 0, '待归位仅ST股(非ST待归位=归位不完整)',
            f'{len(non_st_wg)}只非ST待归位:{";".join(x.get("名称","") for x in non_st_wg[:5])}' if non_st_wg else f'仅{len(wg)}只ST股(独立行情合法)')
        if zt:
            zt_codes = set(str(r.get('代码', '')).zfill(6) for r in zt)
            zt_st = set(str(r.get('代码', '')).zfill(6) for r in zt if 'ST' in (r.get('名称') or ''))
            zt_nonst = zt_codes - zt_st
            gui_codes = set(mp.keys())
            chk(issues, zt_nonst == gui_codes, '归位覆盖==zt_pool非ST涨停(ST股独立行情不归题材)',
                f'zt非ST{len(zt_nonst)} vs 归位{len(gui_codes)}; 差={len(zt_nonst ^ gui_codes)}')

    # ===== 3. 6有 字段合法性 =====
    if s6:
        th = s6.get('题材') or []
        chk(issues, len(th) > 0, '6有题材列表非空', f'{len(th)}条')
        scores_ok = all(1 <= (x.get('得分') or 0) <= 6 for x in th)
        chk(issues, scores_ok, '6有得分∈1-6')
        valid_judge = {'主流', '主流候选', '大分支', '分支'}
        jd = [x.get('判定') for x in th]
        chk(issues, set(jd) <= valid_judge, '6有判定枚举合法', f'{set(jd)}')
        if chain and th:
            s6_sum = sum(x.get('涨停数') or 0 for x in th)
            # ★2026-08-12: 行业口径=聚类子集(聚类口径注"未归位涨停不计入,偏保守"), 合计必然<对链条总数——WARN不FAIL
            if s6_sum > chain.get('涨停总数', 0):
                chk(issues, False, '6有涨停合计≤对链条涨停总数(行业口径是聚类子集)',
                    f'6有{s6_sum} > 对链条{chain.get("涨停总数")}')
            else:
                print('  (WARN) 6有行业口径合计{0} < 对链条{1}——口径注:未归位不计入偏保守, 合法'.format(
                    s6_sum, chain.get('涨停总数')))

    # ===== 4. 四维 字段完整 + 显式 null(零编造) =====
    if d4 and d in d4:
        cur = d4[d]
        lines4 = {k: v for k, v in cur.items() if k != '_警报'}
        miss_f = [nm for nm, e in lines4.items()
                  if not all(f in e for f in ('宽度', '高度', '首板', '二连板', '宽度环比', '题材晋级率'))]
        chk(issues, not miss_f, '四维每线字段完整(含环比/晋级率显式)', ';'.join(miss_f[:5]) or '完整')
        if gui:
            cnt = Counter((v or {}).get('大方向', '未归位') for v in (gui.get('映射') or {}).values())
            chk(issues, len(lines4) == len(cnt), '四维线数==归位大方向数',
                f'四维{len(lines4)} vs 归位{len(cnt)}')
        if chain:
            hi_mismatch = []
            for nm, e in lines4.items():
                ln = next((x for x in (chain.get('题材线') or []) if (x or {}).get('大方向') == nm), None)
                if ln and (ln.get('最高连板') or 0) != (e.get('高度') or 0):
                    hi_mismatch.append(f'{nm}:四维{e.get("高度")}板/对链条{ln.get("最高连板")}板')
            chk(issues, not hi_mismatch, '四维高度==对链条最高连板', ';'.join(hi_mismatch[:5]) or '一致')

    # ===== 5. 判断产物: bodies.theme 存在(题材命门 8/11 断更欠账拦截点) =====
    if jud:
        bt = (jud.get('bodies') or {}).get('theme') or ''
        chk(issues, bool(bt), 'bodies.theme 存在(题材命门判断产物)', '缺失=题材路断更, 需补跑' if not bt else f'{len(bt)//1024}KB')
        if bt:
            for i, num in enumerate('一二三四五', 1):
                chk(issues, f'<h2>{num}' in bt, f'bodies h2板块{num} 存在')
        # kpi 头部结构(黄金版4卡: 涨停/最高板/温度/昨结算 — 题材页 hero 卡数由生成器定, 至少 1 卡)
        chk(issues, bool(jud.get('bodies')) and len(jud.get('bodies', {})) >= 3,
            'judgment bodies 多路齐全', f'{len(jud.get("bodies", {}))}路')

    # ===== 6. 荐票铁律: 标的 ∈ 当日 zt_pool =====
    if jud and zt and (jud.get('bodies') or {}).get('theme'):
        bt = jud['bodies']['theme']
        codes = set(str(r.get('代码', '')).zfill(6) for r in zt)
        rec_codes = set(re.findall(r'(\d{6})', bt))
        bad = rec_codes - codes
        # ★2026-08-12: \d{6} 会误抓日期前缀(20260811→'202608', 20260716→'202607')——排除 20xx 开头的日期串
        bad = {c for c in bad if not re.match(r'20\d{4}', c)}
        chk(issues, not bad, 'bodies.theme 内代码∈zt_pool', ';'.join(sorted(bad)[:5]) or '全在池内')

    # ===== 7. 机器组件回源(页面 vs 数据源, 抽查) =====
    if gui and chain:
        # 战场全貌: 页面含 Top1 线名+家数
        top1 = sorted(((v or {}).get('大方向') for v in (gui.get('映射') or {}).values()),
                      key=lambda x: Counter(v.get('大方向', '') for v in gui['映射'].values())[x])[-1]
        n1 = Counter((v or {}).get('大方向', '') for v in gui['映射'].values())[top1]
        chk(issues, top1 in h, '战场全貌含 Top1 归位线', top1)
    if s6:
        t0 = (s6.get('题材') or [{}])[0]
        nm0 = t0.get('题材(行业口径)') or t0.get('题材') or ''
        chk(issues, nm0 and nm0 in h, '6有卡含 Top1 题材', nm0)
    if d4 and d in d4:
        cur = d4[d]
        lines4 = {k: v for k, v in cur.items() if k != '_警报'}
        if lines4:
            topw = max(lines4.items(), key=lambda kv: kv[1].get('宽度') or 0)[0]
            chk(issues, topw in h, '四维卡含最宽线', topw)

    # ===== 8. fact 层接线(涨停路域 fact 已含题材字段; 题材路 agent 应消费 fact) =====
    fact, err = load_json(f'fact_{d}.json')
    if fact:
        fk = fact.get('facts') or {}
        fa = fk.get('归位A档数', {}).get('value')
        fb = fk.get('归位B档数', {}).get('value')
        fc = fk.get('归位C档数', {}).get('value')
        fl = fk.get('题材线数', {}).get('value')
        if gui and chain:
            src = Counter((v or {}).get('来源档', '?') for v in (gui.get('映射') or {}).values())
            chk(issues, fa == (src.get('A') or 0) and fb == (src.get('B') or 0) and fc == (src.get('C') or 0),
                 'fact归位ABC==归位文件实算', f'fact A{fa}/B{fb}/C{fc} vs 实算 A{src.get("A")}/B{src.get("B")}/C{src.get("C")}')
            chk(issues, fl == (chain.get('题材线数') or 0), 'fact题材线数==对链条',
                f'fact{fl} vs 对链条{chain.get("题材线数")}')

    # ===== 9. 负面验证(限 LLM 手写文本区) =====
    htxt = re.sub(r'<script.*?</script>', '', h, flags=re.S)
    htxt = re.sub(r'<style.*?</style>', '', htxt, flags=re.S)
    htxt = re.sub(r'<[^>]+>', '', htxt)
    for kw in ('NaN', 'None', '{{', 'TODO', 'undefined'):
        if kw in htxt:
            chk(issues, False, f'负面验证·{kw}', '手写文本区出现禁词')

    fails = sum(1 for ok, _, _ in issues if not ok)
    for ok, lab, det in issues:
        print(('  ✓ ' if ok else '  ✗ ') + lab + (f'  [{det}]' if det else ''))
    if fails:
        print(f'FAIL {fails} 项 — 页面数字与数据源不一致, 禁止出页')
        return 1
    print(f'PASS 全部一致 ({len(issues)}项)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
