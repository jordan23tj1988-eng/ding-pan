# -*- coding: utf-8 -*-
"""lhb数据核对.py — lhb页数字核对哨兵(2026-08-12, 参照 limitup数据核对.py)
用法: python lhb数据核对.py 20260811   (exit 0=全过, 1=有FAIL)
核对项: 台账strip三数 / Top5荐票回源 / FUNDTEMP表 / 分档库窗口+档数 / 锚点成对 / 无重复h2 /
        最新台账日 / 分档表新鲜度 / 负面验证
数据源: _席位动向/{d}.csv + _席位分档.json + _资金温度.json + {d}/lhb.csv + 席位荐票卡_{d}.html
"""
import re, os, sys, json, csv, glob, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
SITE = os.path.join(BASE, '复盘', '盯盘台')

def load_page(d, page_path=None):
    """页面文件: 默认 SITE/lhb.html; --page 指定独立输出(如 lhb_20260811.html)"""
    p = page_path or os.path.join(SITE, 'lhb.html')
    if not os.path.exists(p): return None, os.path.basename(p) + ' 不存在'
    return open(p, encoding='utf-8').read(), None

def load_seats(d):
    p = os.path.join(L, '_席位动向', f'{d}.csv')
    if not os.path.exists(p): return None, f'_席位动向/{d}.csv 不存在'
    import pandas as pd
    mv = pd.read_csv(p, dtype={'代码': str})
    return mv, None

def load_lhb(d):
    p = os.path.join(BASE, d, 'lhb.csv')
    if not os.path.exists(p): return None, f'{d}/lhb.csv 不存在'
    return list(csv.DictReader(open(p, encoding='utf-8-sig'))), None

def load_lib():
    p = os.path.join(L, '_席位分档.json')
    if not os.path.exists(p): return None, '_席位分档.json 不存在'
    return json.load(open(p, encoding='utf-8')), None

def load_temp():
    p = os.path.join(L, '_资金温度.json')
    if not os.path.exists(p): return None, '_资金温度.json 不存在'
    return json.load(open(p, encoding='utf-8')), None

def load_seatcard(d):
    p = os.path.join(L, f'席位荐票卡_{d}.html')
    if not os.path.exists(p): return None, f'席位荐票卡_{d}.html 不存在'
    return open(p, encoding='utf-8').read(), None

def find_block(h, start_kw, end_kw, start_from=0):
    i = h.find(start_kw, start_from)
    if i < 0: return None, f'锚点 {start_kw} 未找到'
    j = h.find(end_kw, i + len(start_kw)) if end_kw else len(h)
    return h[i:j if j > 0 else len(h)], None

def chk(issues, ok, label, detail=''):
    issues.append((ok, label, detail))

def main():
    if len(sys.argv) < 2:
        print('用法: python lhb数据核对.py <YYYYMMDD>'); return 2
    d = sys.argv[1]
    page_path = None
    if '--page' in sys.argv:
        page_path = os.path.join(SITE, sys.argv[sys.argv.index('--page') + 1])
    issues = []
    h, err = load_page(d, page_path)
    if err: print('FAIL', err); return 1

    # ===== 0. 锚点成对 + 无重复 h2(结构基线) =====
    # FUNDTEMP/LHBLEDGER 必须 1/1; PAPERTRADE 允许 0/0(独立页面不走模拟盘引擎注入, 全站页须 1/1)
    for anchor in ('FUNDTEMP', 'LHBLEDGER'):
        a = h.count(f'<!--{anchor}-->'); b = h.count(f'<!--/{anchor}-->')
        chk(issues, a == 1 and b == 1, f'锚点{anchor}成对', f'起{a}/止{b}')
    a = h.count('<!--PAPERTRADE-->'); b = h.count('<!--/PAPERTRADE-->')
    chk(issues, a == b and a <= 1, '锚点PAPERTRADE成对', f'起{a}/止{b}')
    hs = re.findall(r'<h2[^>]*>([^<]+)</h2>', h)
    dup = sorted({x for x in hs if hs.count(x) > 1})
    chk(issues, not dup, '无重复h2', '; '.join(dup) if dup else f'{len(hs)}个h2')

    # ===== 1. 台账 strip 三数(页面 vs 存档 summary 同源发出版; 零后视镜: 不用当前分档表复算历史) =====
    m = re.search(r'<summary><b>\d\d-\d\d</b> <span class="chip cold">最新</span> 上榜(\d+) · 机构在场(\d+)只 · S/A出手(\d+)笔</summary>', h)
    if not m:
        chk(issues, False, '台账最新日summary存在', '未找到 最新 日块summary')
    else:
        p_up, p_jg, p_sa = int(m.group(1)), int(m.group(2)), int(m.group(3))
        sp = os.path.join(L, '龙虎榜复盘存档', f'{d}.json')
        if os.path.exists(sp):
            arch = json.load(open(sp, encoding='utf-8'))
            sm = arch.get('summary', '')
            mm = re.search(r'上榜(\d+) · 机构在场(\d+)只 · S/A出手(\d+)笔', sm)
            if mm:
                a_up, a_jg, a_sa = int(mm.group(1)), int(mm.group(2)), int(mm.group(3))
                chk(issues, p_up == a_up, '台账·上榜数', f'页面{p_up} vs 存档{a_up}')
                chk(issues, p_jg == a_jg, '台账·机构在场', f'页面{p_jg} vs 存档{a_jg}')
                chk(issues, p_sa == a_sa, '台账·S/A出手', f'页面{p_sa} vs 存档{a_sa}')
            else:
                chk(issues, False, '台账三数', f'存档{d} summary格式异常:{sm[:60]}')
        else:
            # 无存档(如8/11补建前)→ 数据源复算(标注口径=当前分档表, 非零后视镜)
            mv, err = load_seats(d)
            if err:
                chk(issues, False, '台账三数', err)
            else:
                up = mv['代码'].nunique()
                jg = mv[mv['席位'].astype(str).str.contains('机构专用')]['代码'].nunique()
                lib, _ = load_lib()
                sa = []
                if lib:
                    try:
                        sa = [s for s, v in lib['席位'].items() if v['档'] in 'SA']
                    except Exception:
                        pass
                sa_n = len(mv[(mv['席位'].isin(sa)) & (mv['净额'] > 0) & (mv['买入金额'] >= 1e7)].drop_duplicates(subset=['代码', '席位']))
                chk(issues, p_up == up, '台账·上榜数(复算)', f'页面{p_up} vs 源{up}')
                chk(issues, p_jg == jg, '台账·机构在场(复算)', f'页面{p_jg} vs 源{jg}')
                chk(issues, p_sa == sa_n, '台账·S/A出手(复算)', f'页面{p_sa} vs 源{sa_n}')

    # ===== 2. Top5 荐票卡: 页面含卡文件内容 + 卡内股票回源 lhb.csv =====
    card, err = load_seatcard(d)
    if err:
        chk(issues, False, 'Top5荐票卡', err)
    else:
        chk(issues, card.strip() in h, 'Top5卡在页面', f'卡{len(card)}字符 页面含=OK')
        lhb_rows, lerr = load_lhb(d)
        if lerr:
            chk(issues, False, 'Top5回源', lerr)
        else:
            names = {r.get('名称', '') for r in lhb_rows}
            card_names = re.findall(r'<td[^>]*><b[^>]*>([^<]+)</b></td>', card)
            miss = [n for n in card_names if n and not any(n in x or x in n for x in names)]
            chk(issues, not miss, 'Top5股票回源lhb.csv', '全部命中' if not miss else f'缺:{miss}')

    # ===== 3. FUNDTEMP 表(最近5日 vs _资金温度.json) =====
    temp, terr = load_temp()
    if terr:
        chk(issues, False, 'FUNDTEMP表', terr)
    else:
        t5 = [r for r in temp if r['日'] <= d][-5:][::-1]  # 按核对日截断(零后视镜: 历史核对不用主表最新行)
        # ★2026-08-13: h2 可能因契约外板块插入重编号 → 按"资金温度"关键词定块, 不按"二"编号
        # ★优先按 FUNDTEMP 锚定块(权威标记, 防 agent 手写文本"资金温度"字样干扰关键词定位)
        ki = h.find('<!--FUNDTEMP-->')
        if ki >= 0:
            kj = h.find('<!--/FUNDTEMP-->', ki)
            tseg = h[ki:(kj if kj > 0 else len(h))]
        else:
            ki = h.find('资金温度')
            ti = h.rfind('<h2>', 0, ki) if ki >= 0 else -1
            if ti < 0:
                tseg = None
            else:
                tj = h.find('<h2>', ti + 4)
                tseg = h[ti:tj if tj > 0 else len(h)]
        trows = re.findall(r'<tr><td[^>]*>(\d\d-\d\d)</td>(.*?)</tr>', tseg or '')
        if not trows:
            chk(issues, False, 'FUNDTEMP表', '页面无温度表行')
        else:
            rows = []
            for dt, rest in trows:
                cells = [re.sub(r'<[^>]+>', '', x) for x in re.findall(r'<td[^>]*>(.*?)</td>', rest)]
                rows.append((dt, cells))
            # 数据源侧构建同样形态
            for i, r in enumerate(t5):
                dt = r['日'][4:6] + '-' + r['日'][6:]
                if i < len(rows):
                    pdt, pcells = rows[i]
                    chk(issues, pdt == dt, f'FUNDTEMP行{i+1}日期', f'页面{pdt} vs 源{dt}')
                    expect = [str(r['机构席次']), str(r['量化席次']), str(r['知名游资席次']), str(r['北向席次']), f"{r['总金额亿']}亿", str(r['温度分位'])]
                    for j, (pv, ev) in enumerate(zip(pcells, expect)):
                        if pv and ev and pv.split('/')[0] != ev:
                            chk(issues, False, f'FUNDTEMP行{i+1}第{j+1}列', f'页面{pv} vs 源{ev}')

    # ===== 4. 分档库窗口+档数(页面 vs _席位分档.json) =====
    lib, lerr = load_lib()
    if lerr:
        chk(issues, False, '分档库', lerr)
    else:
        m2 = re.search(r'窗口(\d+)~(\d+) (\d+)笔', h)
        if not m2:
            chk(issues, False, '分档库窗口', '页面无窗口标注')
        else:
            w = lib.get('窗口', '')
            w2 = (w or '').replace('~', '')
            chk(issues, f'{m2.group(1)}~{m2.group(2)}' == w, '分档库窗口', f'页面{m2.group(1)}~{m2.group(2)} vs 源{w}')
            chk(issues, int(m2.group(3)) == lib.get('笔数'), '分档库笔数', f'页面{m2.group(3)} vs 源{lib.get("笔数")}')
        from collections import Counter
        c = Counter(v['档'] for v in lib['席位'].values())
        m3 = re.search(r'<span class="chip">S(\d+)/A(\d+)/B(\d+)/C(\d+)/预备(\d+)</span>', h)
        if not m3:
            chk(issues, False, '分档库档数', '页面无档数标注')
        else:
            got = {'S': int(m3.group(1)), 'A': int(m3.group(2)), 'B': int(m3.group(3)), 'C': int(m3.group(4)), 'P': int(m3.group(5))}
            for k in ('S', 'A', 'B', 'C', 'P'):
                chk(issues, got[k] == c.get(k, 0), f'分档库档数{k}', f'页面{got[k]} vs 源{c.get(k, 0)}')

    # ===== 5. 分档表新鲜度(窗口末日 vs d) =====
    if lib and lib.get('窗口'):
        we = lib['窗口'].split('~')[-1]
        _cut = (datetime.datetime.strptime(d, '%Y%m%d') - datetime.timedelta(days=5)).strftime('%Y%m%d')
        chk(issues, we >= _cut, '分档表新鲜度', f'窗口末日{we} vs 核对日{d}(容忍{d}-5日)')

    # ===== 6. 负面验证(限 LLM 手写文本区: 头部+板块一/五/六; 不扫 CSS/JS/SVG 合法内容) =====
    htxt = re.sub(r'<script.*?</script>', '', h, flags=re.S)
    htxt = re.sub(r'<style.*?</style>', '', htxt, flags=re.S)
    # ★2026-08-21: 台账/存档折叠区(含已冻结历史发出版的"待结算None"占位)属机器区, 非LLM手写区
    #   与注释本意对齐: 折叠区剔除后再扫, 防历史存档占位误报阻断发布
    htxt = re.sub(r'<details class="chain".*?</details>', '', htxt, flags=re.S)
    htxt = re.sub(r'<[^>]+>', '', htxt)
    for kw in ('NaN', 'None', '{{', 'TODO', 'undefined', 'null</'):
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
