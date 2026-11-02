#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冰点触发器回测.py —— 冰点转机复合触发器 A档回测定阈值(P1,2026-07-11)。
主注册规则(回测前先定,防挑参过拟合):
  冰点区: 市场温度<25(温度表定义的冰点档)
  转机分量(全部T日收盘可知,零后视镜):
    c1 跌停缩减: 跌停数(T)<跌停数(T-1)
    c2 晋级回升: 1进2率(T)>1进2率(T-1)
    c3 溢价转正: 当日观察到的昨停执行均收(T)>0
  触发=冰点区 且 ≥2个分量成立。
目标变量(执行口径,唯一合法口径):
  y1=池(T)于T+1开盘买入→T+1收盘 全场涨停执行均收(=接力第一天肉)
  y3/y5=从T+1起连续玩3/5天的日均执行均收
网格仅做邻域稳健性检查(温度阈值/分量数),不以网格最优改主规则,除非主规则明显失效。
对照实验: 全样本基准/冰点未转机/过热日(≥85)/退潮确认(溢价连负3日)。
数据: _市场温度表.json(温度因果滚动分位)+_情绪先行指标.json(晋级/溢价)+_全场涨停执行均收_回填.json(bars_cache重建,--rebuild可再生)。
铁律: 样本小如实标注;单一牛市周期(2025-07~2026-07)的结论不外推,写明适用域。
"""
import os, sys, json
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")

def load():
    T = json.load(open(os.path.join(L, "_市场温度表.json"), encoding="utf-8"))
    F = json.load(open(os.path.join(L, "_情绪先行指标.json"), encoding="utf-8"))
    P = json.load(open(os.path.join(L, "_全场涨停执行均收_回填.json"), encoding="utf-8"))
    days = sorted(set(T) & set(F))
    rows = {}
    pdays = sorted(P)
    prem_on = {}   # 交易日->当日观察到的昨停执行均收(池日=前一交易日)
    for i, d in enumerate(pdays[:-1]):
        prem_on[pdays[i + 1]] = P[d].get("执行均收")
    for d in days:
        j = (F[d].get("晋级") or {})
        rows[d] = dict(
            temp=T[d].get("温度"),
            dt=T[d].get("跌停数"),
            j12=j.get("一进二率"),
            prem=prem_on.get(d),
            y1=P.get(d, {}).get("执行均收"))
    ds = sorted(rows)
    # y3/y5=未来3/5个池日的日均y1
    for i, d in enumerate(ds):
        for k in (3, 5):
            vs = [rows[ds[i + m]]["y1"] for m in range(k) if i + m < len(ds) and rows[ds[i + m]]["y1"] is not None]
            rows[d]["y%d" % k] = round(float(np.mean(vs)), 2) if len(vs) == k else None
    return rows, ds

def comps(rows, ds, i):
    """返回(c1,c2,c3)三分量,任一输入缺失该分量记None。"""
    d, p = ds[i], ds[i - 1]
    r, rp = rows[d], rows[p]
    c1 = (r["dt"] < rp["dt"]) if (r["dt"] is not None and rp["dt"] is not None) else None
    c2 = (r["j12"] > rp["j12"]) if (r["j12"] is not None and rp["j12"] is not None) else None
    c3 = (r["prem"] > 0) if (r["prem"] is not None) else None
    return c1, c2, c3

def stat(name, idx, rows, ds):
    y1 = [rows[ds[i]]["y1"] for i in idx if rows[ds[i]]["y1"] is not None]
    y3 = [rows[ds[i]]["y3"] for i in idx if rows[ds[i]]["y3"] is not None]
    y5 = [rows[ds[i]]["y5"] for i in idx if rows[ds[i]]["y5"] is not None]
    if not y1:
        return dict(组=name, n=0)
    return dict(组=name, n=len(y1),
                y1均=round(float(np.mean(y1)), 2), y1胜率=round(float(np.mean([x > 0 for x in y1])), 2),
                y3均=round(float(np.mean(y3)), 2) if y3 else None,
                y5均=round(float(np.mean(y5)), 2) if y5 else None,
                小样本=len(y1) < 25)

def run():
    rows, ds = load()
    n = len(ds)
    valid = [i for i in range(1, n) if rows[ds[i]]["temp"] is not None]
    out = {"样本域": f"{ds[0]}~{ds[-1]} 共{n}日(温度可用{len(valid)}日)", "对照": [], "主规则": None, "网格": []}

    def trig_idx(A, need, N=1):
        res = []
        for i in valid:
            if i < N:
                continue
            if any(rows[ds[i - m]]["temp"] is None or rows[ds[i - m]]["temp"] >= A for m in range(N)):
                continue
            cs = [c for c in comps(rows, ds, i) if c is not None]
            if len(cs) < 2:
                continue
            if sum(cs) >= need:
                res.append(i)
        return res

    ice_all = [i for i in valid if rows[ds[i]]["temp"] < 25]
    hot = [i for i in valid if rows[ds[i]]["temp"] >= 85]
    # 对照
    out["对照"].append(stat("全样本基准", valid, rows, ds))
    out["对照"].append(stat("冰点日全部(温度<25)", ice_all, rows, ds))
    prim = trig_idx(25, 2)
    ice_no = [i for i in ice_all if i not in set(prim)]
    out["对照"].append(stat("冰点未转机(<25且分量<2)", ice_no, rows, ds))
    out["对照"].append(stat("过热日(温度>=85)", hot, rows, ds))
    # 退潮确认对照: 溢价连负3日
    ebb = []
    for i in valid:
        if i < 3:
            continue
        ps = [rows[ds[i - m]]["prem"] for m in range(3)]
        if all(p is not None and p < 0 for p in ps):
            ebb.append(i)
    out["对照"].append(stat("退潮确认(溢价连负3日)", ebb, rows, ds))

    s = stat("★主规则:温度<25 且 ≥2/3转机分量", prim, rows, ds)
    s["触发日"] = [ds[i] for i in prim]
    out["主规则"] = s
    # 网格邻域稳健性
    for A in (20, 25, 30, 35):
        for need in (1, 2, 3):
            g = stat(f"温度<{A} 且≥{need}分量", trig_idx(A, need), rows, ds)
            out["网格"].append(g)
    # 连续2日冰点变体
    for A in (25, 30):
        g = stat(f"连续2日温度<{A} 且≥2分量", trig_idx(A, 2, N=2), rows, ds)
        out["网格"].append(g)
    json.dump(out, open(os.path.join(L, "_冰点触发器回测.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(out["样本域"])
    print("\n== 对照 ==")
    for x in out["对照"]:
        print(" ", x)
    print("\n== 主规则 ==\n ", {k: v for k, v in out["主规则"].items() if k != "触发日"})
    print("  触发日:", out["主规则"].get("触发日"))
    print("\n== 网格(邻域稳健性) ==")
    for x in out["网格"]:
        print(" ", x)

if __name__ == "__main__":
    run()
