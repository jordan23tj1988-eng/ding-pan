#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""题材质量跃迁.py —— 「质量跃迁须双日确认」可调用判据（20261023 由 theme 路落地）

判据（MA-20261022-03③ 原文，不改口径）：
    T日封单率 ≥ 1.5%  ∧  T-1日封单率 ≥ 1.0%  ∧  T日换手 ≤ T-1日换手 × 1.5
封单率 = 封板资金 / 流通市值 × 100（zt_pool 自算，与涨停对链条『封单比』同口径）。

用法：
    from 题材质量跃迁 import confirm          # 单票判定
    confirm("301502", "20261023")             # -> dict(pass, legs, 缺口原因, T/T-1 原始值)
    python 题材质量跃迁.py 20261023            # 全池扫描，列出当日 PASS 名单
    python 题材质量跃迁.py 20261023 --json     # 同上，输出 JSON

回测（20261013~20261022，执行口径=T+1开盘买→T+1收盘，本路荐票结算同口径）：
    PASS  n=22  执1胜率 40.9%  执1均收 -1.61%  误判率(执1≤0) 59.1%  T+1断板 45.5%
    近20笔 n=20 执1胜率 40.0%  执1均收 -1.63%  误判率 60.0%      T+1断板 45.0%
    参照  全样本 n=379 执1胜率 38.8%  执1均收 -0.86%  误判率 61.2%  T+1断板 77.0%
结论（写死在 docstring，避免下次重跑再抄错）：判据对『次日是否继续封板』有效
（断板45.5% 远低于全样本77.0%），对『执1执行收益』无效（-1.61% 差于全样本-0.86%）——
只能作线级质量延续筛，不能单独作荐票门槛；荐票必须叠加 gap 闸门。
换手条款单独验证：被换手条款剔除的 17 笔 执1均收 -3.32%、误判率 76.5%，
即该条款确有增量（+1.71pp），保留。
"""
import csv, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(BASE, "{d}", "zt_pool.csv")


def _load(d):
    """读 {d}/zt_pool.csv -> {代码: 指标}；缺文件返回 {}（零编造，不补造）。"""
    p = POOL.format(d=d)
    if not os.path.exists(p):
        return {}
    out = {}
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                fz = float(r["封板资金"]); fl = float(r["流通市值"]); hs = float(r["换手率"])
            except (KeyError, ValueError):
                continue
            out[r["代码"]] = dict(名称=r["名称"], 封单率=fz / fl * 100 if fl else None, 换手=hs,
                                  连板=int(float(r["连板数"] or 0)), 首封=str(r["首次封板时间"]).zfill(6),
                                  炸板=int(float(r["炸板次数"] or 0)))
    return out


def prev_day(d):
    """上一交易日 = 数据目录里存在 zt_pool.csv 的最近一个更早日期（不猜交易日历）。"""
    ds = sorted(x for x in os.listdir(BASE) if x.isdigit() and len(x) == 8
                and os.path.exists(POOL.format(d=x)) and x < d)
    return ds[-1] if ds else None


def confirm(code, d, prev=None):
    """单票双日确认。返回 dict：pass / legs(三条腿各自布尔) / T、T-1 原始值 / 缺口。"""
    cur = _load(d)
    if code not in cur:
        return dict(code=code, date=d, pass_=None, 缺口="T日不在 zt_pool（未涨停或数据缺失）")
    pd = prev or prev_day(d)
    pre = _load(pd) if pd else {}
    c = cur[code]; p = pre.get(code)
    legs = {"T日封单率≥1.5%": bool(c["封单率"] is not None and c["封单率"] >= 1.5),
            "T-1日封单率≥1.0%": bool(p and p["封单率"] is not None and p["封单率"] >= 1.0),
            "T日换手≤T-1×1.5": bool(p and p["换手"] and c["换手"] <= p["换手"] * 1.5)}
    return dict(code=code, 名称=c["名称"], date=d, prev_date=pd,
                pass_=all(legs.values()), legs=legs,
                T_封单率=round(c["封单率"], 2) if c["封单率"] is not None else None,
                T_换手=round(c["换手"], 1), T_连板=c["连板"], T_首封=c["首封"], T_炸板=c["炸板"],
                T1_封单率=round(p["封单率"], 2) if p and p["封单率"] is not None else None,
                T1_换手=round(p["换手"], 1) if p else None,
                缺口=None if p else "T-1 不在 zt_pool → 双日腿不可判（首板票天生不适用）")


def scan(d):
    cur = _load(d)
    return [confirm(c, d) for c in cur]


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    d = args[0]
    rows = scan(d)
    passed = [r for r in rows if r["pass_"]]
    if "--json" in args:
        print(json.dumps(dict(日期=d, 池=len(rows), PASS=passed), ensure_ascii=False, indent=1)); return
    print(f"{d} 全池 {len(rows)} 只，双日确认 PASS {len(passed)} 只（T-1={prev_day(d)}）")
    for r in passed:
        print(f"  {r['code']} {r['名称']:<8s} {r['T_连板']}板 封{r['T_封单率']}%(前{r['T1_封单率']}%) "
              f"换{r['T_换手']}(前{r['T1_换手']}) 首封{r['T_首封']} 炸{r['T_炸板']}")


if __name__ == "__main__":
    main()
