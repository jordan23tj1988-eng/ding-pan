# -*- coding: utf-8 -*-
"""涨停甜点结算.py {dprev} v1.0 —— 甜点票次日兑现结算(零后视镜、零编造)

作用: 每日涨停复盘时, 结算昨日"甜点票"(第3板一字开炸板<3%回封)的次日兑现, 验证定稿规则 +4.18% 是否成立。
规则对齐 量价因子库 M28 定稿(买入=回封价=涨停价, 次日 gap/量比分叉):
  买入 = dprev 日收盘价(涨停价=回封价)
  次日(dnext) gap = open/close - 1, 量比 = vol[dnext]/vol[dprev]
  · 低开(<-2%) 或 平开(±2%) 或 (高开>2% 且 量比>=1.5) → 开盘卖, 收益=open/close-1
  · 高开>2% 且 量比<1.5 → 持有到断板(断板日收盘卖)
  另出 S1 固定口径: 次日开盘卖(零后视镜, T+1 当日可完整结算)

数据源: _学习/_bars_cache/{code}.csv(open/high/low/close/volume) + 涨停甜点_{dprev}.json
口径: 甜点票极少(全历史471次/日均0.1~0.25次), 多数日子甜点票=0 → 空结算(诚实输出, 不编造)。
输出: _学习/涨停甜点结算_{dprev}.json + _涨停甜点结算.jsonl(审计线累积, 供跨期验证)
"""
import os, sys, csv, json, glob, re, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
LEARN = os.path.join(BASE, '_学习')
CDIR = os.path.join(LEARN, '_bars_cache')


def limit_pct(code):
    """涨停幅度: 创业板300/301、科创板688/689=20%; 其余主板=10%(北交所已排除)。"""
    if code[:3] in ('300', '301', '688', '689'):
        return 20.0
    return 10.0


def read_bars(code):
    """读全量日K → {date(str无横杠): (open,high,low,close,volume)}"""
    p = os.path.join(CDIR, code + '.csv')
    if not os.path.isfile(p):
        return None
    out = {}
    try:
        with open(p, encoding='utf-8') as f:
            rd = csv.DictReader(f)
            for r in rd:
                d = (r.get('date') or '').strip().replace('-', '')
                try:
                    o = float(r['open']); c = float(r['close'])
                    v = float(r.get('volume') or 0)
                    out[d] = (o, c, v)
                except (KeyError, ValueError, TypeError):
                    continue
    except Exception:
        return None
    return out


def next_trading_days(dates, dprev, k=20):
    """返回 dprev 之后的 k 个交易日(升序)。dates=已排序的日期列表。"""
    return [x for x in dates if x > dprev][:k]


def is_zt_close(close, prev_close, code):
    """是否涨停收盘(收盘价≈涨停价)。"""
    lp = limit_pct(code)
    return close >= round(prev_close * (1 + lp / 100), 2) - 0.011


def settle_one(code, dprev, bars_map, all_dates):
    """结算单只甜点票 → dict 或 None。"""
    b = bars_map.get(code)
    if not b or dprev not in b:
        return None
    buy = b[dprev][1]                      # 买入价=涨停价(回封价)
    if buy <= 0:
        return None
    dnext = next_trading_days(all_dates, dprev, 1)
    if not dnext or dnext[0] not in b:
        return None
    dn = dnext[0]
    o1, c1, v1 = b[dn]
    v0 = b[dprev][2]
    gap = o1 / buy - 1
    vol_ratio = (v1 / v0) if v0 else None

    # S1 固定口径: 次日开盘卖
    s1 = o1 / buy - 1

    # 定稿规则口径
    if gap < -0.02 or abs(gap) <= 0.02 or (gap > 0.02 and (vol_ratio is None or vol_ratio >= 1.5)):
        rule_ret = s1
        rule_action = '开盘卖'
    else:
        # 高开>2% 且 量比<1.5 → 持有到断板
        prev_c = buy
        brk_ret = s1                       # 兜底: 若一直没断板, 用次日开盘卖近似
        brk_found = False
        for dk in next_trading_days(all_dates, dn, 20):
            if dk not in b:
                break                      # 断板日数据缺失(票已离开涨停池,未被增量拉取)
            ck = b[dk][1]
            if not is_zt_close(ck, prev_c, code):
                brk_ret = ck / buy - 1     # 断板日收盘卖
                brk_found = True
                break
            prev_c = ck
        rule_ret = brk_ret
        rule_action = '持有到断板' if brk_found else '持有中(断板日数据未到)'

    return dict(代码=code, 名称='', 买入价=round(buy, 2), 次日开盘=round(o1, 2),
                次日量比=(round(vol_ratio, 2) if vol_ratio is not None else None),
                gap=round(gap * 100, 2), S1开盘卖=round(s1 * 100, 2),
                定稿动作=rule_action, 定稿收益=round(rule_ret * 100, 2))


def main(dprev):
    sp = os.path.join(LEARN, f'涨停甜点_{dprev}.json')
    if not os.path.isfile(sp):
        print('无甜点文件, 跳过')
        return
    sp_json = json.load(open(sp, encoding='utf-8'))
    sweets = sp_json.get('甜点', [])

    if not sweets:
        out = dict(甜点日=dprev, 结算状态='当日无甜点票(正常:甜点为稀有事件,全历史471次)', 甜点票数=0, 明细=[], 汇总=None)
        json.dump(out, open(os.path.join(LEARN, f'涨停甜点结算_{dprev}.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print(f'涨停甜点结算_{dprev}.json: 当日无甜点票, 空结算')
        return

    days = sorted([os.path.basename(x) for x in glob.glob(os.path.join(BASE, '2026*'))
                   if os.path.isdir(x)])
    # 预读甜点票的日K(甜点票极少, 全量读无压力)
    bars_map = {x['代码']: read_bars(x['代码']) for x in sweets}

    res = []
    for x in sweets:
        r = settle_one(x['代码'], dprev, bars_map, days)
        if r:
            r['名称'] = x.get('名称', '')
            r['炸开深度'] = x.get('炸开深度')
            res.append(r)

    s1_list = [r['S1开盘卖'] for r in res]
    rule_list = [r['定稿收益'] for r in res]
    s1_avg = round(sum(s1_list) / len(s1_list), 2) if s1_list else None
    rule_avg = round(sum(rule_list) / len(rule_list), 2) if rule_list else None
    s1_win = sum(1 for v in s1_list if v > 0)
    rule_win = sum(1 for v in rule_list if v > 0)

    out = dict(
        甜点日=dprev,
        甜点票数=len(sweets),
        结算票数=len(res),
        明细=res,
        汇总=dict(
            S1开盘卖均收=s1_avg, S1胜率=f'{s1_win}/{len(s1_list)}' if s1_list else '0/0',
            定稿规则均收=rule_avg, 定稿胜率=f'{rule_win}/{len(rule_list)}' if rule_list else '0/0',
            研究基准='量价因子库M28: 471次/胜68%/单笔+4.18%(26年)',
        ),
        口径='买入=回封价(涨停价);S1=次日开盘卖(零后视镜固定);定稿=次日gap/量比分叉(低开/平开/放量高开开盘卖,高开缩量持有到断板)',
    )
    json.dump(out, open(os.path.join(LEARN, f'涨停甜点结算_{dprev}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    with open(os.path.join(LEARN, '_涨停甜点结算.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(dict(甜点日=dprev, 甜点票数=len(sweets), 结算票数=len(res),
                                S1均收=s1_avg, S1胜率=out['汇总']['S1胜率'],
                                定稿均收=rule_avg, 定稿胜率=out['汇总']['定稿胜率']), ensure_ascii=False) + '\n')

    print(f'涨停甜点结算_{dprev}.json: 甜点{len(sweets)}只/结算{len(res)}只 | '
          f'S1均收{s1_avg}% 胜率{out["汇总"]["S1胜率"]} | 定稿均收{rule_avg}% 胜率{out["汇总"]["定稿胜率"]}')
    # ── 注入日块开头(有甜点票才注入; 空结算不碰日块, 避免噪音) ──
    if res:
        disp = dprev[4:6] + '-' + dprev[6:8]
        rows_h = ''.join(
            f'<tr><td style="white-space:nowrap"><b>{r["名称"]}</b><br><span class="mut">{r["代码"]}</span></td>'
            f'<td style="white-space:nowrap">炸开{(r["炸开深度"]*100):.1f}%</td>'
            f'<td style="white-space:nowrap">gap{r["gap"]:+.1f}%·量比{r["次日量比"]}</td>'
            f'<td style="white-space:nowrap">S1 {r["S1开盘卖"]:+.2f}%</td>'
            f'<td class="{"dA" if (r["定稿收益"] or 0) > 0 else "dC"}" style="white-space:nowrap">'
            f'{r["定稿动作"]} {r["定稿收益"]:+.2f}%</td></tr>' for r in res)
        blk = (f'<p style="font-weight:700;margin:4px 0 4px;border-left:3px solid var(--accent);padding-left:8px">'
               f'第3板甜点 · T+1结算对账(一字开炸板&lt;3%回封)</p>'
               f'<div class="hint">甜点{len(sweets)}只 · S1次日开盘卖均收{s1_avg}% 胜率{out["汇总"]["S1胜率"]} · '
               f'定稿均收{rule_avg}% 胜率{out["汇总"]["定稿胜率"]}。研究基准:量价因子库M28=471次/胜68%/单笔+4.18%(26年17/17年正)。'
               f'甜点为稀有事件,无甜点日正常空结算。</div>'
               f'<div class="card"><table style="table-layout:fixed;width:100%">'
               f'<tr><th>标的</th><th>炸开</th><th>次日gap·量比</th><th>S1开盘卖</th><th>定稿规则</th></tr>{rows_h}</table></div>')
        dp = os.path.join(LEARN, '涨停复盘存档', f'{dprev}.json')
        if os.path.isfile(dp):
            D = json.load(open(dp, encoding='utf-8'))
            h = re.sub(r'<p style="[^"]*">第3板甜点 · T\+1结算对账.*?(?=<p style|<div class="strip")', '',
                       D['html'], flags=re.S)  # 幂等:先删旧结算块
            D['html'] = blk + h
            json.dump(D, open(dp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            subprocess.run([sys.executable, os.path.join(BASE, '涨停复盘台账.py')], check=True)
            print('  已注入甜点结算块到日块' + dprev + ' + 台账重组装')
        else:
            print('  ⚠无该日日块,结算json已存但未注入页面')

    for r in res:
        print(f"  {r['名称']}({r['代码']}) gap{r['gap']}% 量比{r['次日量比']} → "
              f"S1 {r['S1开盘卖']:+.2f}% / 定稿[{r['定稿动作']}] {r['定稿收益']:+.2f}%")
    print('DONE')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python 涨停甜点结算.py YYYYMMDD')
        sys.exit(2)
    main(sys.argv[1])
