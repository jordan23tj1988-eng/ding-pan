# -*- coding: utf-8 -*-
"""MA-20261022-02 ① 极寒|跌停≥30|高开0~5 扩样 + 可成交剔除双版 (本路自算,A档口径同 竞价池分桶回填.py)"""
import os, sys, json, importlib.util
BASE = r"D:/股票数据/市场数据"
sys.path.insert(0, BASE)
spec = importlib.util.spec_from_file_location("bf", os.path.join(BASE, "竞价池分桶回填.py"))
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)
L = os.path.join(BASE, "_学习")

ths = json.load(open(os.path.join(L, "_ths_zt_pool.json"), encoding="utf-8"))
wdt = json.load(open(os.path.join(L, "_市场温度表.json"), encoding="utf-8"))
days = sorted(ths.keys())
S = []
for di, d in enumerate(days[:-1]):
    dn = days[di + 1]
    pool = bf.build_pool(ths[d])
    w = wdt.get(d) or {}
    wd, dt = w.get("温度"), w.get("跌停数")
    nset = {x["code"] for x in ths.get(dn, [])}
    for t in pool:
        b = bf.bars(t["代码"])
        if b is None: continue
        idx = b.index[b['date'] == d.replace('-', '')]
        if not len(idx): continue
        i = idx[0]
        if i + 1 >= len(b) or str(b.loc[i + 1, 'date']) != dn: continue
        o1, h1, l1, c1 = [float(b.loc[i + 1, k]) for k in ('open', 'high', 'low', 'close')]
        Tc = float(b.loc[i, 'close'])
        o0 = float(b.loc[i, 'open'])
        gap = round((o1 / Tc - 1) * 100, 2)
        ex = round((c1 / o1 - 1) * 100, 2)
        mv = b.loc[i, 'circ_mv亿'] if 'circ_mv亿' in b.columns else None
        mv = float(mv) if (mv is not None and mv == mv) else None
        fdb = round(t["封单额亿"] / mv * 100, 2) if (mv and mv > 0) else None
        # 可成交剔除判据
        ziyi = (abs(o1 - h1) < 1e-6 and abs(o1 - l1) < 1e-6 and abs(h1 - l1) < 1e-6)  # open==high==low
        yizi_feng = (gap >= 9.5 and abs(o1 - h1) < 1e-6)                             # gap>=9.5 且 open==high
        S.append(dict(日=d, 代码=t["代码"], 名称=t["名称"], 信号=t["信号"].split("·")[0], 连板=t["连板"],
                      炸板=t["炸板"], 封单比=fdb, 温度=wd, 跌停=dt, T1高开=gap, 执行=ex,
                      次日封板=t["代码"] in nset, 剔1=ziyi, 剔2=yizi_feng))
print("总样本", len(S), "窗口", days[0], "~", days[-2])


def agg(s):
    if not s: return dict(n=0)
    ex = [x["执行"] for x in s]
    return dict(n=len(s), 胜率=round(sum(1 for e in ex if e > 0) / len(ex) * 100, 1),
                均收=round(sum(ex) / len(ex), 2),
                封板率=round(sum(1 for x in s if x["次日封板"]) / len(s) * 100, 1),
                天数=len({x["日"] for x in s}))


def rep(tag, cond):
    a = [x for x in S if cond(x)]
    b = [x for x in a if not (x["剔1"] or x["剔2"])]
    A, B = agg(a), agg(b)
    print(f"{tag:38s} 全样本 n={A.get('n')} {A.get('胜率')}%/{A.get('均收')}%  可成交 n={B.get('n')} {B.get('胜率')}%/{B.get('均收')}%  剔{A.get('n',0)-B.get('n',0)}只 差={round((B.get('均收') or 0)-(A.get('均收') or 0),2)}pp 池日{A.get('天数')}")
    return A, B


print("\n== ① 原口径(严) 极寒<20 | 跌停≥30 ==")
rep("极寒<20|跌停≥30 全档", lambda x: x["温度"] is not None and x["温度"] < 20 and (x["跌停"] or 0) >= 30)
rep("   └ 高开0~5 (原 n=12 格)", lambda x: x["温度"] is not None and x["温度"] < 20 and (x["跌停"] or 0) >= 30 and 0 < x["T1高开"] < 5)

print("\n== ① 扩样(温度<25 | 跌停≥20 并集) ==")
rep("极寒区(<25|跌停≥20) 全档", lambda x: x["温度"] is not None and x["温度"] < 25 and (x["跌停"] or 0) >= 20)
rep("   └ 高开0~5", lambda x: x["温度"] is not None and x["温度"] < 25 and (x["跌停"] or 0) >= 20 and 0 < x["T1高开"] < 5)

print("\n== ① 扩样(温度<25 且 跌停≥15) ==")
rep("温度<25|跌停≥15 全档", lambda x: x["温度"] is not None and x["温度"] < 25 and (x["跌停"] or 0) >= 15)
rep("   └ 高开0~5", lambda x: x["温度"] is not None and x["温度"] < 25 and (x["跌停"] or 0) >= 15 and 0 < x["T1高开"] < 5)

print("\n== ① 扩样(跌停≥30 单维, 不限温度) ==")
rep("跌停≥30 全档", lambda x: (x["跌停"] or 0) >= 30)
rep("   └ 高开0~5", lambda x: (x["跌停"] or 0) >= 30 and 0 < x["T1高开"] < 5)

print("\n== 参照: 全库 & 高开档基线 ==")
rep("全库", lambda x: True)
rep("高开0~5 全库", lambda x: 0 < x["T1高开"] < 5)
rep("高开≥5 全库", lambda x: x["T1高开"] >= 5)
rep("低开≤0 全库", lambda x: x["T1高开"] <= 0)

print("\n== 今日 regime 相关: 温度50~65(中档) ==")
rep("中40~65 全档", lambda x: x["温度"] is not None and 40 <= x["温度"] < 65)
rep("   └ 高开0~5", lambda x: x["温度"] is not None and 40 <= x["温度"] < 65 and 0 < x["T1高开"] < 5)
rep("   └ 低开≤0", lambda x: x["温度"] is not None and 40 <= x["温度"] < 65 and x["T1高开"] <= 0)
rep("   └ 高开≥5", lambda x: x["温度"] is not None and 40 <= x["温度"] < 65 and x["T1高开"] >= 5)

print("\n== V型修复日(前日温度<25 且 当日温度≥45) 次日执行 ==")
dk = [d for d in days[:-1]]
wmap = {d: (wdt.get(d) or {}).get("温度") for d in days}
i_prev = {d: days[i - 1] if i else None for i, d in enumerate(days)}


def vrev(x):
    p = i_prev.get(x["日"])
    if not p: return False
    wp, wc = wmap.get(p), x["温度"]
    return (wp is not None and wp < 25 and wc is not None and wc >= 45)


rep("V型修复日 全档", vrev)
rep("   └ 高开0~5", lambda x: vrev(x) and 0 < x["T1高开"] < 5)
rep("   └ 低开≤0", lambda x: vrev(x) and x["T1高开"] <= 0)
rep("   └ 高开≥5", lambda x: vrev(x) and x["T1高开"] >= 5)
print("V型日清单:", sorted({x["日"] for x in S if vrev(x)}))

# 今日池(20261023)个股明细落盘备用
json.dump(S, open(os.path.join(BASE, "_tmp", "auction_samples_1023.json"), "w", encoding="utf-8"), ensure_ascii=False)
