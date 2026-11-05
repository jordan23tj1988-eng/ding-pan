# -*- coding: utf-8 -*-
"""lhb 分层真实率 + 当日榜覆盖率 复算器（承接 Master 指派 MA-20261104-05）
口径（固定，禁改）：
  源1 = {d}/lhb.csv 当日榜行（上榜原因不含 连续/累计/严重异常），按代码取首行，不累加多榜
  源2 = _学习/_席位动向/{d}.csv，剔 类型 含 连续/累计/严重异常 的行，(代码,席位) 去重取买入金额最大
  票级净买 = 源1 龙虎榜净买额；席位侧净额 = 源2 净额合计
  真实率 = 票级净买合计 / 席位侧净额合计（席位买五口径天然偏买，真实率是唯一纠偏项）
  分层 = 当日榜码 ∩ zt_pool(涨停) vs 当日榜码 - zt_pool(非涨停)
  覆盖率 = |当日榜码 ∩ 涨停| / 涨停数
用法：python lhb_分层真实率.py [20261105 ...]；不带参数则扫全部可用日期
"""
import csv, json, os, sys, math

ROOT = r'D:/股票数据/市场数据'
os.chdir(ROOT)
SKIP = ('连续', '累计', '严重异常')


def rd(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def one(d):
    lhb_p = f'{d}/lhb.csv'
    zt_p = f'{d}/zt_pool.csv'
    xd_p = f'_学习/_席位动向/{d}.csv'
    if not (os.path.exists(lhb_p) and os.path.exists(zt_p) and os.path.exists(xd_p)):
        return {'日': d, '状态': '缺件'}
    lh = {}
    for r in rd(lhb_p):
        if any(k in (r['上榜原因'] or '') for k in SKIP):
            continue
        lh.setdefault(r['代码'], float(r['龙虎榜净买额']) / 1e8)
    ztc = {r['代码']: r for r in rd(zt_p)}
    best = {}
    for r in rd(xd_p):
        if any(k in (r.get('类型') or '') for k in SKIP):
            continue
        k = (r['代码'], r['席位'])
        b = float(r['买入金额'] or 0)
        if k not in best or b > float(best[k]['买入金额'] or 0):
            best[k] = r
    seat = {}
    for (c, _), r in best.items():
        seat[c] = seat.get(c, 0) + float(r['净额'] or 0)
    zt_set = set(lh) & set(ztc)
    nz_set = set(lh) - set(ztc)

    def grp(codes):
        p = sum(lh[c] for c in codes)
        s = sum(seat.get(c, 0) for c in codes) / 1e8
        return {'n': len(codes), '票级亿': round(p, 4), '席位亿': round(s, 4),
                '真实率%': round(p / s * 100, 1) if s else None}

    out = {'日': d, '状态': 'ok', '涨停数': len(ztc), '当日榜码': len(lh), '席位笔': len(best),
           '覆盖数': len(zt_set),
           '覆盖率%': round(len(zt_set) / len(ztc) * 100, 1) if ztc else None,
           '涨停层': grp(zt_set), '非涨停层': grp(nz_set),
           '全场': grp(set(lh))}
    a, b = out['涨停层']['真实率%'], out['非涨停层']['真实率%']
    out['分层必要'] = (None if a is None or b is None else (a > 0 > b) or (a <= 0 < b))
    return out


def main():
    args = sys.argv[1:]
    if args:
        days = args
    else:
        days = sorted({x[:-4] for x in os.listdir('_学习/_席位动向') if x.endswith('.csv')})
    rows = [one(d) for d in days]
    ok = [r for r in rows if r['状态'] == 'ok']
    # 覆盖率 vs 涨停数 相关（Pearson + Spearman，单调性判据）
    def pear(xs, ys):
        n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs)); sy = math.sqrt(sum((y - my) ** 2 for y in ys))
        return 0.0 if sx * sy == 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    def spearman(xs, ys):
        def rk(v):
            s = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
            for pos, i in enumerate(s): r[i] = pos + 1
            return r
        return pear(rk(xs), rk(ys))
    zt = [r['涨停数'] for r in ok]; cov = [r['覆盖率%'] for r in ok]
    same = [r for r in ok if r['分层必要'] is False]
    res = {'口径': __doc__.split('口径')[1][:400], '日期数': len(ok), '明细': rows,
           '相关': {'pearson(涨停数,覆盖率)': round(pear(zt, cov), 3) if ok else None,
                    'spearman(涨停数,覆盖率)': round(spearman(zt, cov), 3) if ok else None},
           '分层判定': {'异号日': sum(1 for r in ok if r['分层必要']), '同号日': len(same),
                    '同号日列表': [r['日'] for r in same]}}
    json.dump(res, open('_学习/lhb_分层真实率_多日.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    f = lambda v: '  None' if v is None else f'{v:>7}'
    for r in ok:
        print(f"{r['日']} 涨停{r['涨停数']:>4} 榜码{r['当日榜码']:>3} 覆盖{r['覆盖数']:>3}={r['覆盖率%']:>5}% "
              f"全场{f(r['全场']['真实率%'])}% 涨停层{f(r['涨停层']['真实率%'])}%(n={r['涨停层']['n']}) "
              f"非涨停{f(r['非涨停层']['真实率%'])}%(n={r['非涨停层']['n']}) 分层必要={r['分层必要']}")
    print('相关', res['相关'], '分层', res['分层判定'])


if __name__ == '__main__':
    main()
