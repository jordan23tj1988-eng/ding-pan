# -*- coding: utf-8 -*-
"""
横切面扫描.py —— ④产业逻辑·自主拓展的兜底触发器(2026-07-12,源起中报预增miss复盘)
================================================================================
问题: "页面早有发现,agent没深究"——盘面反复出现的现象级聚类(跨行业标签,如中报预增/
医药创新药),不是产业链条,链条纵深库和前置预期雷达两头都不管,掉在缝里,等用户追问才深挖。
机制: 每晚扫近3日题材归位大方向标签(含业绩类),凡【计数达标 + 不被链条纵深库覆盖】
→ 进待深挖清单;11号agent对清单逐项**强制应答**(立项深挖/并入已有链/观察+理由),
应答状态记入持久台账(深挖专题台账.json,只加不删,像链条纵深库一样是记忆)。
阈值: 近3日累计≥5 或 单日≥5(散票/待核/个股逻辑除外)。
用法: python3 横切面扫描.py YYYYMMDD
输出: _学习/待深挖清单_{d}.json
"""
import sys, os, json, glob, collections

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据")
    BASE = g[0] if g else BASE
LEARN = os.path.join(BASE, "_学习")
EXCLUDE = ("散票", "待核", "个股逻辑")

def main():
    d = sys.argv[1]
    days = sorted([f[5:13] for f in os.listdir(LEARN)
                   if f.startswith("题材归位_") and f.endswith(".json")])
    days = [x for x in days if x <= d][-3:]
    per_day, names = {}, collections.Counter()
    per_stock = collections.defaultdict(set)
    for day in days:
        try:
            j = json.load(open(os.path.join(LEARN, "题材归位_"+day+".json"), encoding="utf-8"))
        except Exception:
            continue
        c = collections.Counter()
        for code, v in (j.get("映射") or {}).items():
            if not isinstance(v, dict):
                continue
            ln = str(v.get("大方向", "")).strip()
            if not ln or any(k in ln for k in EXCLUDE):
                continue
            c[ln] += 1
            per_stock[ln].add(code)
        per_day[day] = dict(c)
        names.update(c)

    # 覆盖判定: 与链条纵深库链名互为子串=已有owner
    try:
        chains = [k for k in json.load(open(os.path.join(LEARN, "链条纵深库.json"), encoding="utf-8")) if k != "说明"]
    except Exception:
        chains = []
    def covered_by(ln):
        for ch in chains:
            if ch in ln or ln in ch:
                return ch
        return None

    # 持久台账(只加不删): {线索:{状态,立项日,结论,关联}}
    tp = os.path.join(LEARN, "深挖专题台账.json")
    ledger = {}
    if os.path.exists(tp):
        try:
            ledger = json.load(open(tp, encoding="utf-8"))
        except Exception:
            ledger = {}

    items = []
    for ln, total in names.most_common():
        daily = {day: per_day.get(day, {}).get(ln, 0) for day in days}
        if total < 5 and max(daily.values() or [0]) < 5:
            continue
        cov = covered_by(ln)
        led = ledger.get(ln)
        if cov and not led:
            continue  # 已有链条owner且无台账特记 → 不打扰
        items.append({
            "线索": ln, "近3日累计": total, "按日": daily,
            "涨停股数(去重)": len(per_stock[ln]),
            "纵深库覆盖": cov,
            "台账状态": (led or {}).get("状态", "★新"),
            "台账结论": (led or {}).get("结论"),
        })
    out = {"日期": d, "窗口": days,
           "口径": "近3日题材归位大方向计数(剔散票/待核);累计≥5或单日≥5;与纵深库链名互为子串=已覆盖不列;台账状态'★新'=强制应答项",
           "清单": items}
    fp = os.path.join(LEARN, "待深挖清单_"+d+".json")
    json.dump(out, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("OK", fp)
    for x in items:
        print(f' [{x["台账状态"]}] {x["线索"]} 累计{x["近3日累计"]} {x["按日"]} 覆盖={x["纵深库覆盖"]}')

if __name__ == "__main__":
    main()
