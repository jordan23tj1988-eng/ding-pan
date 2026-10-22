# -*- coding: utf-8 -*-
"""auction 路 20261022 深挖:承接 MA-20261021-02 ①②③ + 极寒温度桶/薄封污染检验。
复用 竞价池分桶回填.py 的 build_pool/settle 口径(import 不重写),零后视镜。
产出 _学习/子agent增强/auction_深挖_20261022.json
"""
import os, sys, json, csv
BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
L = os.path.join(BASE, "_学习")
import importlib.util
spec = importlib.util.spec_from_file_location("bf", os.path.join(BASE, "竞价池分桶回填.py"))
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)

ths = json.load(open(os.path.join(L, "_ths_zt_pool.json"), encoding="utf-8"))
wdt = json.load(open(os.path.join(L, "_市场温度表.json"), encoding="utf-8"))
days = sorted(ths.keys())

S = []
miss = 0; total_pool = 0
for di, d in enumerate(days[:-1]):
    dn = days[di+1]
    pool = bf.build_pool(ths[d]); total_pool += len(pool)
    wd = (wdt.get(d) or {}).get("温度")
    nx = {x["code"] for x in ths.get(dn, [])}
    for t in pool:
        r = bf.settle(t["代码"], d, dn)
        if r is None:
            miss += 1; continue
        gk, ex, sg, mv = r
        fdb = round(t["封单额亿"]/mv*100, 2) if (mv and mv > 0) else None
        S.append(dict(d=d, code=t["代码"], name=t["名称"], fb=t["首封"], lb=t["连板"],
                      sig=t["信号"], zha=t["炸板"], fdb=fdb, wd=wd, gk=gk, ex=ex,
                      sg=sg, seal=t["代码"] in nx))

def agg(rows):
    n = len(rows)
    if n == 0: return None
    ex = [r["ex"] for r in rows]
    return dict(n=n, 胜率=round(sum(1 for e in ex if e > 0)/n*100, 1),
                均收=round(sum(ex)/n, 2),
                封板率=round(sum(1 for r in rows if r["seal"])/n*100, 1),
                信号均涨=round(sum(r["sg"] for r in rows)/n, 2),
                注=("小样本" if n < 25 else None))

def gk(r):
    return "低开≤0" if r["gk"] <= 0 else ("高开0~5" if r["gk"] < 5 else "高开≥5")

def wdb(r):
    if r["wd"] is None: return None
    w = r["wd"]
    return "极寒<20" if w < 20 else ("冷20~40" if w < 40 else ("中40~65" if w < 65 else "热≥65"))

out = {"窗口": f"{days[0]}~{days[-1]}", "样本": len(S), "池票总数": total_pool,
       "bars覆盖率pct": round((1-miss/max(total_pool, 1))*100, 1)}

# ① 封单比<0.5% × 炸板二分 (MA-20261021-02 要求)
thin = [r for r in S if r["fdb"] is not None and r["fdb"] < 0.5]
out["①封单比<0.5%_按炸板二分"] = {
    "全桶": agg(thin),
    "炸0-1": agg([r for r in thin if r["zha"] <= 1]),
    "炸≥2": agg([r for r in thin if r["zha"] >= 2]),
    "对照_封单比≥0.5%": agg([r for r in S if r["fdb"] is not None and r["fdb"] >= 0.5]),
}
# 薄封正桶污染检验:按高开档拆
out["①b薄封<0.5%_按高开档"] = {g: agg([r for r in thin if gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")}
out["①c薄封<0.5%_按信号"] = {s: agg([r for r in thin if r["sig"].split("·")[0] == s]) for s in ("一字", "秒板")}

# ② 开板一字 vs 一字未开 (MA-20261021-02 要求)
yz = [r for r in S if r["sig"].startswith("一字")]
out["②一字_按是否开板"] = {
    "一字未开(炸0)": agg([r for r in yz if r["zha"] == 0]),
    "开板一字(炸≥1)": agg([r for r in yz if r["zha"] >= 1]),
    "开板一字_按高开档": {g: agg([r for r in yz if r["zha"] >= 1 and gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")},
    "一字未开_按高开档": {g: agg([r for r in yz if r["zha"] == 0 and gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")},
    "开板深度_炸1-3": agg([r for r in yz if 1 <= r["zha"] <= 3]),
    "开板深度_炸≥4": agg([r for r in yz if r["zha"] >= 4]),
}

# ③ 极寒温度桶(本路自建:库现只有冷<40,今日11.2落更极端区)
out["③极寒温度桶"] = {b: agg([r for r in S if wdb(r) == b]) for b in ("极寒<20", "冷20~40", "中40~65", "热≥65")}
out["③b极寒x高开档"] = {g: agg([r for r in S if wdb(r) == "极寒<20" and gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")}
out["③c冷20~40x高开档"] = {g: agg([r for r in S if wdb(r) == "冷20~40" and gk(r) == g]) for g in ("低开≤0", "高开0~5", "高开≥5")}

# 首板×低开≤0(承接昨日新门,验正反)
out["④首板低开门"] = {
    "首板|低开≤0": agg([r for r in S if r["lb"] == 1 and gk(r) == "低开≤0"]),
    "2板|低开≤0": agg([r for r in S if r["lb"] == 2 and gk(r) == "低开≤0"]),
    "3板+|低开≤0": agg([r for r in S if r["lb"] >= 3 and gk(r) == "低开≤0"]),
    "首板|低开≤0_且薄封<0.5%": agg([r for r in S if r["lb"] == 1 and gk(r) == "低开≤0" and r["fdb"] is not None and r["fdb"] < 0.5]),
    "首板|低开≤0_且炸1+": agg([r for r in S if r["lb"] == 1 and gk(r) == "低开≤0" and r["zha"] >= 1]),
}
# 明日可执行的精确格:极寒×薄封×闸门内
out["⑤关键交叉_极寒x薄封x高开档"] = {
    f"{a}|{b}": agg([r for r in S if wdb(r) == a and gk(r) == b and r["fdb"] is not None and r["fdb"] < 0.5])
    for a in ("极寒<20", "冷20~40") for b in ("低开≤0", "高开0~5", "高开≥5")}
out["⑤b极寒x炸1+x高开档"] = {
    f"{b}": agg([r for r in S if wdb(r) == "极寒<20" and r["zha"] >= 1 and gk(r) == b])
    for b in ("低开≤0", "高开0~5", "高开≥5")}

# 近5日样本(库窗口尾部)供稳定性
out["⑥近5池日明细"] = {}
for d in days[-6:-1]:
    rows = [r for r in S if r["d"] == d]
    out["⑥近5池日明细"][d] = agg(rows)

json.dump(out, open(os.path.join(L, "子agent增强", "auction_深挖_20261022.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
