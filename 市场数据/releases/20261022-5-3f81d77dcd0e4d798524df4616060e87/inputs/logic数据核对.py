# -*- coding: utf-8 -*-
"""logic数据核对.py — 产业逻辑路(logic)路级数据核对哨兵(2026-10-23 立)
用法: python logic数据核对.py 20261022     (exit 0=全过, 1=有FAIL)

补的是五路里唯一没有路级核对的缺口: 此前 logic 只有 p1 claim 级文本检查,
claim 只要在页面出现即过, 数字对不对、段五是否空段、荐票与交易计划是否一致
全都没人管。本脚本按 cycle/auction/lhb/theme 四路同一口径补齐。

核对项(14):
  1  zt_pool 存在
  2  judgment_{d}.json 存在且 bodies.logic 非空
  3  bodies.logic 段数 >= 5 (契约段数)
  4  段五标题含「中报预增」(模板名, _body_import 靠它归位)
  5  段五正文非空 >= 200 字 (空段 => 页面 degraded)
  6  正文涨停代码 ⊆ zt_pool ∪ dt_pool (跌停回引合法)
  7  对链条.涨停总数 == zt_pool 行数
  8  对链条.题材线数 == len(题材线)
  9  正文出现当日涨停总数(可回源)
  10 交易计划_logic 存在 且 buys ⊆ zt_pool
  11 荐票结论与 buys 一致 (结论写 0 只 <=> buys 为空)
  12 中报预增雷达 存在 且 日期==d; 统计.成色A共振 == len(A共振池)
  13 渲染页 logic.html 存在 且 含段五模板名
  14 渲染页无裸 null/None% 占位

数据源: judgment_{d}.json + {d}/zt_pool.csv + {d}/dt_pool.csv
        + 涨停对链条_{d}.json + 交易计划_logic_{d}.json + 中报预增雷达_{d}.json
"""
import os
import re
import sys
import json

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
SITE = os.environ.get('POST_SITE_ROOT') or os.path.join(BASE, '复盘', '盯盘台')

issues = []
n_ok = 0


def chk(cond, name, detail=''):
    global n_ok
    if cond:
        n_ok += 1
        print('  PASS  %s' % name + (('  [%s]' % detail) if detail and detail != 'ok' else ''))
    else:
        issues.append('%s  %s' % (name, detail))
        print('  FAIL  %s  [%s]' % (name, detail))


def _codes(path):
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype={'代码': str})
        return set(df['代码'].astype(str).str.zfill(6))
    except Exception:
        return None


def main(d):
    print('=' * 60)
    print('logic数据核对  %s' % d)
    print('=' * 60)

    zt_p = os.path.join(BASE, d, 'zt_pool.csv')
    zt = _codes(zt_p)
    chk(zt is not None, '1 zt_pool存在', '%d 行' % len(zt) if zt else zt_p)
    dt = _codes(os.path.join(BASE, d, 'dt_pool.csv')) or set()

    # ---- judgment / bodies ----
    jp = os.path.join(L, 'judgment_%s.json' % d)
    jud = None
    if os.path.exists(jp):
        try:
            jud = json.load(open(jp, encoding='utf-8'))
        except Exception as e:
            jud = None
            print('  !! judgment 解析失败:', str(e)[:80])
    bt = ((jud or {}).get('bodies') or {}).get('logic') or ''
    chk(bool(bt.strip()), '2 bodies.logic非空', '%d 字符' % len(bt))

    h2 = [re.sub(r'<[^>]+>', '', m.group(1)).strip()
          for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', bt, re.S)]
    chk(len(h2) >= 5, '3 段数>=5', 'h2=%d %s' % (len(h2), '/'.join(h2[:6])))

    sec5 = ''
    m5 = None
    for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', bt, re.S):
        t = re.sub(r'<[^>]+>', '', m.group(1))
        if '中报预增' in t:
            m5 = m
    if m5:
        nxt = bt.find('<h2', m5.end())
        sec5 = bt[m5.end(): nxt if nxt > 0 else len(bt)]
    chk(m5 is not None, '4 段五=中报预增雷达(模板名)',
        ('ok %s' % re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m5.group(1))).strip()) if m5 else '未找到含「中报预增」的 h2')
    _t5 = re.sub(r'<[^>]+>', '', sec5)
    chk(len(_t5) >= 200, '5 段五正文非空', '%d 字' % len(_t5))

    # ---- 代码可溯源 ----
    # logic 与 theme 不同: 正文合法引用「产业链上但当日未涨停」的公司(卡位池155只来自F10主营),
    # 不能要求 ⊆ 涨停池。改为两道: ①荐票/买入级代码必须 ∈ zt_pool(见第10项);
    # ②正文出现的其它代码必须是真实存在的A股(在 _bars_cache 有K线), 防手滑打错代码。
    if zt:
        rec = set(re.findall(r'(\d{6})', bt))
        rec = {c for c in rec if not re.match(r'20\d{4}', c)}
        outside = rec - zt - dt
        fake = {c for c in outside
                if not os.path.exists(os.path.join(L, '_bars_cache', c + '.csv'))}
        if outside:
            print('  INFO  6a 正文引用非当日涨停代码 %d 个(产业链/卡位口径, 允许): %s'
                  % (len(outside), ';'.join(sorted(outside)[:8])))
        chk(not fake, '6 正文代码可溯源(∉池者须为真实A股)', ';'.join(sorted(fake)[:5]) or 'ok')

    # ---- 对链条 ----
    cp = os.path.join(L, '涨停对链条_%s.json' % d)
    chain = None
    if os.path.exists(cp):
        try:
            chain = json.load(open(cp, encoding='utf-8'))
        except Exception:
            chain = None
    tot = (chain or {}).get('涨停总数')
    chk(chain is not None and zt is not None and tot == len(zt),
        '7 对链条.涨停总数==zt_pool行数', 'chain=%s zt=%s' % (tot, len(zt) if zt else None))
    lines = (chain or {}).get('题材线') or []
    nline = (chain or {}).get('题材线数')
    chk(chain is not None and isinstance(lines, list) and nline == len(lines),
        '8 对链条.题材线数==len(题材线)', 'line_cnt=%s list=%s' % (nline, len(lines) if isinstance(lines, list) else '?'))

    # ---- 正文数字回源 ----
    if zt:
        chk(('涨停' in bt) and (str(len(zt)) in bt), '9 正文含当日涨停总数', 'zt=%d 是否出现在正文' % len(zt))

    # ---- 交易计划 / 荐票一致 ----
    tp = os.path.join(L, '交易计划_logic_%s.json' % d)
    plan = None
    if os.path.exists(tp):
        try:
            plan = json.load(open(tp, encoding='utf-8'))
        except Exception:
            plan = None
    buys = (plan or {}).get('buys') or []
    buy_codes = set()
    for b in buys:
        c = str((b or {}).get('代码') or (b or {}).get('code') or '')
        if c:
            buy_codes.add(c.zfill(6))
    chk(plan is not None and (not zt or not (buy_codes - zt)),
        '10 交易计划.buys⊆zt_pool', 'buys=%s 越界=%s' % (len(buys), sorted(buy_codes - (zt or set()))[:4]))

    jd = os.path.join(L, 'logic判断_%s.json' % d)
    jj = None
    if os.path.exists(jd):
        try:
            jj = json.load(open(jd, encoding='utf-8'))
        except Exception:
            jj = None
    _rec_txt = json.dumps((jj or {}).get('荐票') or {}, ensure_ascii=False)
    _says_zero = ('0只' in _rec_txt) or ('空仓' in _rec_txt) or ('不建新仓' in _rec_txt)
    chk(plan is not None and ((_says_zero and not buys) or ((not _says_zero) and buys)),
        '11 荐票结论与buys一致', '结论空仓=%s buys=%d' % (_says_zero, len(buys)))

    # ---- 中报雷达 ----
    rp = os.path.join(L, '中报预增雷达_%s.json' % d)
    radar = None
    if os.path.exists(rp):
        try:
            radar = json.load(open(rp, encoding='utf-8'))
        except Exception:
            radar = None
    st = (radar or {}).get('统计') or {}
    a_pool = (radar or {}).get('A共振池(重要度排序)') or []
    chk(radar is not None and str((radar or {}).get('日期')) == str(d) and st.get('成色A共振') == len(a_pool),
        '12 雷达存在/日期/A共振计数', 'file=%s 日期=%s 统计A=%s len=%s' % (
            os.path.exists(rp), (radar or {}).get('日期'), st.get('成色A共振'), len(a_pool)))

    # ---- 渲染页 ----
    pp = os.path.join(SITE, 'logic.html')
    page = open(pp, encoding='utf-8').read() if os.path.exists(pp) else ''
    chk(bool(page) and '中报预增' in page, '13 渲染页含段五模板名', 'page=%d字符' % len(page))
    _junk = page.count('>null<') + page.count('None%')
    chk(bool(page) and _junk == 0, '14 渲染页无裸null/None%', 'null=%d None%%=%d' % (page.count('>null<'), page.count('None%')))

    print('-' * 60)
    print('共 %d 项, PASS %d, FAIL %d' % (n_ok + len(issues), n_ok, len(issues)))
    if issues:
        print('FAIL 明细:')
        for x in issues:
            print('  -', x)
        return 1
    print('全部通过')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python logic数据核对.py YYYYMMDD')
        sys.exit(2)
    sys.exit(main(sys.argv[1].strip()))
