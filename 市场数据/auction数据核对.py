# -*- coding: utf-8 -*-
"""auction数据核对.py — auction页数字核对哨兵(2026-08-12 双轨版)
用法: python auction数据核对.py <YYYYMMDD> [--page 文件名] (exit 0=全过, 1=有FAIL)
★双轨(同 cycle/lhb):
  有 body 日(黄金版形态=body 整段保真, 机器数据嵌在 LLM body 内):
    机器锚 MACHSCORE/MACHPOOL/MACHSIG 必须缺席(0/0), body 自带 SCORECARD/POOLLEDGER 锚 1/1,
    温度/涨停/结算数字对 LLM body 文本核对(含 8/12 新六段格式与 7/16 旧八段格式)
  无 body 日(断档兜底): 机器折叠区三卡 + 断档卡, 机器锚 1/1, 池/结算/温度逐票回源
数据源: 竞价池发出_{d}.json + 竞价池结算_{d}.json + _竞价池结算.jsonl + _市场温度表.json + judgment_{d}.json
"""
import re, os, sys, json, csv

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
SITE = os.path.join(BASE, '复盘', '盯盘台')

def load_page(d, page_path=None):
    p = page_path or os.path.join(SITE, 'auction.html')
    if page_path and not os.path.isabs(p):
        p = os.path.join(SITE, page_path)
    if not os.path.exists(p): return None, os.path.basename(p) + ' 不存在'
    return open(p, encoding='utf-8').read(), None

def load_body(d):
    p = os.path.join(L, 'judgment_%s.json' % d)
    if not os.path.exists(p): return None, 'judgment_%s.json 不存在' % d
    try:
        b = json.load(open(p, encoding='utf-8'))['bodies'].get('auction')
        return (b or ''), None
    except Exception as e: return None, str(e)

def load_发出(d):
    p = os.path.join(L, '竞价池发出_%s.json' % d)
    if not os.path.exists(p): return None, '竞价池发出_%s.json 不存在' % d
    try: return json.load(open(p, encoding='utf-8')), None
    except Exception as e: return None, str(e)

def load_结算(d):
    p = os.path.join(L, '竞价池结算_%s.json' % d)
    if not os.path.exists(p): return None, '竞价池结算_%s.json 不存在(用jsonl汇总降级)'
    try: return json.load(open(p, encoding='utf-8')), None
    except Exception as e: return None, str(e)

def load_结账():
    p = os.path.join(L, '_竞价池结算.jsonl')
    if not os.path.exists(p): return None, '_竞价池结算.jsonl 不存在'
    rows = []
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l: continue
        try: j = json.loads(l)
        except Exception: continue
        if j.get('执行均收') is None: continue  # ★未结算占位(胜率0/0均收null)禁引用
        rows.append(j)
    return rows, None

def load_temp(d):
    p = os.path.join(L, '_市场温度表.json')
    if not os.path.exists(p): return None, '_市场温度表.json 不存在'
    return json.load(open(p, encoding='utf-8')), None

def chk(issues, ok, label, detail=''):
    issues.append((ok, label, detail))

def check_page(h, d):
    issues = []
    body, berr = load_body(d)
    has_body = bool(body)
    # ===== 0. 锚点成对 + 无重复h2 =====
    if has_body:
        # 含SCORECARD锚形态(2026-08-16六段化)=机器卡由渲染器注入空锚 → 成对且≤1
        # 纯LLM形态(无 SCORECARD 锚)=机器锚缺席 0/0
        golden8 = h.count('<!--SCORECARD-->') >= 1
        for anchor in ('MACHSCORE', 'MACHPOOL', 'MACHSIG'):
            a = h.count('<!--%s-->' % anchor); b = h.count('<!--/%s-->' % anchor)
            if golden8:
                chk(issues, a == b and a <= 1, '机器锚%s成对(机器注入)' % anchor, '起%d/止%d' % (a, b))
            else:
                chk(issues, a == 0 and b == 0, '机器锚%s应缺席(六段LLM形态)' % anchor, '起%d/止%d' % (a, b))
        for anchor in ('SCORECARD', 'POOLLEDGER'):
            a = h.count('<!--%s-->' % anchor); b = h.count('<!--/%s-->' % anchor)
            # body 自带机器卡锚(1/1); 纯 LLM 无锚(0/0) → 成对且≤1
            chk(issues, a == b and a <= 1, 'body锚%s成对(LLM原文)' % anchor, '起%d/止%d' % (a, b))
    else:
        for anchor in ('MACHSCORE', 'MACHPOOL', 'MACHSIG'):
            a = h.count('<!--%s-->' % anchor); b = h.count('<!--/%s-->' % anchor)
            chk(issues, a == 1 and b == 1, '机器锚%s成对(断档兜底)' % anchor, '起%d/止%d' % (a, b))
        for anchor in ('SCORECARD', 'POOLLEDGER'):
            a = h.count('<!--%s-->' % anchor); b = h.count('<!--/%s-->' % anchor)
            chk(issues, a == 0 and b == 0, 'body锚%s应缺席(无body)' % anchor, '起%d/止%d' % (a, b))
    a = h.count('<!--PAPERTRADE-->'); b = h.count('<!--/PAPERTRADE-->')
    chk(issues, a == b and a <= 1, '锚点PAPERTRADE成对', '起%d/止%d' % (a, b))
    hs = re.findall(r'<h2[^>]*>([^<]+)</h2>', h)
    dup = sorted({x for x in hs if hs.count(x) > 1})
    chk(issues, not dup, '无重复h2', '; '.join(dup) if dup else '%d个h2' % len(hs))

    # ===== 1. 竞价池回源(机器卡: 池票∈发出版; 有body日=文本含池数) =====
    fc, ferr = load_发出(d)
    if ferr:
        chk(issues, False, '竞价池', ferr)
    else:
        n_pool = len(fc['池'])
        codes = [str(r.get('代码', '')) for r in fc['池']]
        # 无 body 日: MACHSCORE 表逐票核对
        if not has_body:
            tbl = h[h.find('<!--MACHSCORE-->'):h.find('<!--/MACHSCORE-->')]
            miss = [c for c in codes if c not in tbl]
            chk(issues, not miss, 'MACHSCORE池票回源', '缺%d只:%s' % (len(miss), ','.join(miss)) if miss else '%d只全在' % n_pool)
        else:
            chk(issues, ('%d只' % n_pool) in h or str(n_pool) in h, '池数文本(LLM body)', '源池%d只' % n_pool)

    # ===== 2. 结算回源(封板/胜率/均收) =====
    hist, herr = load_结账()
    if herr:
        chk(issues, False, '结算', herr)
    else:
        cur = [r for r in hist if str(r.get('池日', '')) == str(d)]
        if not cur:
            chk(issues, '暂无%s池结算' % d, '结算(未到结算日)', 'jsonl无%s条目' % d)
        else:
            c = cur[-1]
            seg = h[h.find('<!--MACHPOOL-->'):h.find('<!--/MACHPOOL-->')] if not has_body else h
            for key, label in (('次日封板', '封板'), ('执行胜率', '胜率'), ('执行均收', '均收')):
                v = c.get(key)
                if v is None:
                    chk(issues, False, '结算·%s' % label, '源缺%s字段' % key)
                    continue
                vs = str(v)
                ok = vs in seg or vs.replace('.', '') in seg.replace('.', '')
                chk(issues, ok, '结算·%s回源(%s)' % (label, vs), '页面含%s' % vs)
            if not has_body:
                det = (c.get('明细') or [])
                if det:
                    tbl = h[h.find('<!--MACHPOOL-->'):h.find('<!--/MACHPOOL-->')]
                    codes = [str(r.get('代码', '')) for r in det]
                    miss = [x for x in codes if x not in tbl]
                    chk(issues, not miss, 'MACHPOOL结算明细回源', '缺%d只' % len(miss) if miss else '%d只全在' % len(det))

    # ===== 3. 温度/涨停回源 =====
    t, terr = load_temp(d)
    if terr:
        chk(issues, False, '温度', terr)
    else:
        days = sorted(k for k in t if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
        cur = t[days[-1]] if days else {}
        tmp = cur.get('温度')
        zt = cur.get('涨停数')
        if tmp is not None:
            chk(issues, (str(tmp) in h), '温度回源(%s)' % tmp, '页面含温度值')
        if zt is not None:
            chk(issues, (str(zt) in h), '涨停数回源(%s)' % zt, '页面含涨停数')

    # ===== 4. LLM 区完整性 =====
    if berr:
        chk(issues, False, 'LLM区', berr)
    elif body:
        need = ['<h2>一', '<h2>二', '<h2>三', '<h2>四', '<h2>五', '<h2>六']
        miss = [x for x in need if x not in h]
        chk(issues, not miss, 'LLM六段完整', '全部在位' if not miss else '缺:%s' % miss)
    else:
        chk(issues, '未产竞价复盘' in h, '断档卡存在', '无body须显式断档卡')
        # hero 区(前4000字符)禁旧日期: 只允许当日 MM-DD
        curd = d[4:6] + '-' + d[6:8]
        dates = re.findall(r'\d{2}-\d{2}', h[:4000])
        bad = [x for x in dates if x != curd]
        chk(issues, not bad, 'hero无旧日期', '出现旧日期:%s' % ','.join(set(bad)) if bad else '仅%s' % curd)

    # ===== 5. 负面验证(禁词) =====
    # ★形态区分(2026-08-12): 无 body 日页面全是渲染器新产出 → 全页禁 None;
    #   有 body 日=body 历史原文逐字节保真(7/16 原文含脚本注入期 None 占位=历史事实, 不改),
    #   → 只查渲染链路新注入区(PAPERTRADE 看板/首屏 hero 前 shell 区), body 原文宽容。
    htxt = re.sub(r'<script.*?</script>', '', h, flags=re.S)
    htxt = re.sub(r'<style.*?</style>', '', htxt, flags=re.S)
    if not has_body:
        htxt = re.sub(r'<[^>]+>', '', htxt)
    else:
        htxt = re.sub(r'<[^>]+>', '', htxt)
        pa = htxt.find('模拟盘')
        if pa >= 0:
            htxt = htxt[pa - 2000: pa + 6000]
        else:
            htxt = htxt[:2000]
    for kw in ('NaN', 'None', '{{', 'TODO', 'undefined'):
        if kw in htxt:
            chk(issues, False, '负面验证·%s' % kw, '文本区出现禁词')
    return issues

def main():
    if len(sys.argv) < 2:
        print('用法: python auction数据核对.py <YYYYMMDD>'); return 2
    d = sys.argv[1]
    page_path = None
    if '--page' in sys.argv:
        page_path = os.path.join(SITE, sys.argv[sys.argv.index('--page') + 1])
    h, err = load_page(d, page_path)
    if err: print('FAIL', err); return 1
    issues = check_page(h, d)
    fails = sum(1 for ok, _, _ in issues if not ok)
    for ok, lab, det in issues:
        print(('  ✓ ' if ok else '  ✗ ') + lab + (('  [%s]' % det) if det else ''))
    if fails:
        print('FAIL %d 项 — 页面数字与数据源不一致, 禁止出页' % fails)
        return 1
    print('PASS 全部一致 (%d项)' % len(issues))

    # ===== 6. 负面注入测试: 改坏当日温度值(有断言) → 哨兵必须 FAIL =====
    if '--skip-inject' not in sys.argv:
        t, terr = load_temp(d)
        tmp = None
        if not terr:
            days = sorted(k for k in t if re.fullmatch(r'\d{8}', str(k)) and str(k) <= str(d))
            if days: tmp = t[days[-1]].get('温度')
        if tmp is not None and str(tmp) in h:
            bad = h.replace(str(tmp), '99.9')
            if bad != h:
                bissues = check_page(bad, d)
                bfails = sum(1 for ok, _, _ in bissues if not ok)
                if bfails == 0:
                    print('FAIL 负面注入测试: 改坏温度值后哨兵未拦截(应 FAIL)')
                    return 1
                print('PASS 负面注入: 改坏温度 %s → 哨兵拦截(%d项FAIL)' % (tmp, bfails))
        else:
            print('⚠ 负面注入跳过(页面无当日温度值)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
