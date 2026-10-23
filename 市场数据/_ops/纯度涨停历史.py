# -*- coding: utf-8 -*-
"""纯度×涨停 历史结算（MA-20261022-04 ②）
子集: 卡位纯度>=50% (今日37只 ∪ 产业链模板内标的 的复算结果) ∧ 历史涨停
口径: 执1 = T+1 开盘买入 → T+1 收盘卖出 (与 _ops/ledger.py 一致)
基准: 同窗口全部涨停事件同口径
输出: _学习/纯度涨停历史_20261023.json
"""
import csv
import glob
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "20261023"


def load_bars(code):
    p = os.path.join(BASE, "_学习", "_bars_cache", "%s.csv" % code)
    if not os.path.exists(p):
        return None
    rows = []
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({"date": r["date"].replace("-", ""),
                             "open": float(r["open"]), "high": float(r["high"]),
                             "low": float(r["low"]), "close": float(r["close"]),
                             "turn": float(r.get("turnover") or 0)})
            except (ValueError, KeyError):
                continue
    return rows


def main():
    pur = json.load(open(os.path.join(BASE, "_学习", "卡位纯度_%s.json" % DATE), encoding="utf-8"))
    info = {}
    for r in pur["机器人涨停"] + pur["模板内标的"]:
        if r.get("purity") is not None:
            info[r["代码"]] = {"名称": r["名称"], "purity": r["purity"],
                             "strict": r["strict_template"], "节点": r.get("链上节点"),
                             "来源": "今日涨停" if r in pur["机器人涨停"] else "模板内"}
    uni = {c: v for c, v in info.items() if v["purity"] >= 50}

    days = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(BASE, "20*", "zt_pool.csv")))
    days = [d for d in days if d <= DATE and d.startswith("2026")]
    bars = {}
    events, base_events = [], []
    for d in days:
        rows = list(csv.DictReader(open(os.path.join(BASE, d, "zt_pool.csv"), encoding="utf-8-sig")))
        for r in rows:
            code = r["代码"].zfill(6)
            if code not in bars:
                bars[code] = load_bars(code)
            b = bars[code]
            if not b:
                continue
            idx = next((i for i, x in enumerate(b) if x["date"] == d), None)
            if idx is None or idx + 1 >= len(b):
                continue  # 无T+1数据 → 不可结算
            nxt = b[idx + 1]
            exec1 = (nxt["close"] / nxt["open"] - 1) * 100 if nxt["open"] else None
            if exec1 is None:
                continue
            rec = {"日期": d, "代码": code, "名称": r["名称"], "执1": round(exec1, 2),
                   "连板": r.get("连板数"), "炸板": r.get("炸板次数"),
                   "封单比": round(float(r["封板资金"]) / float(r["流通市值"]) * 100, 3)
                   if r.get("封板资金") and r.get("流通市值") else None,
                   "T+1开盘": nxt["open"], "T+1收盘": nxt["close"]}
            base_events.append(rec)
            if code in uni:
                rec2 = dict(rec)
                rec2["纯度"] = uni[code]["purity"]
                rec2["严格模板"] = bool(uni[code]["strict"] and uni[code]["strict"] >= 50)
                rec2["节点"] = uni[code]["节点"]
                events.append(rec2)

    def stat(rows, label):
        n = len(rows)
        if not n:
            return {"标签": label, "n": 0}
        rets = [r["执1"] for r in rows]
        win = sum(1 for x in rets if x > 0)
        srt = sorted(rets)
        return {"标签": label, "n": n, "胜率pct": round(win / n * 100, 1),
                "均收pct": round(sum(rets) / n, 2),
                "中位pct": round(srt[n // 2], 2),
                "最大单笔": max(rets), "最差单笔": min(rets),
                "样本起": min(r["日期"] for r in rows), "样本止": max(r["日期"] for r in rows)}

    out = {
        "日期": DATE,
        "口径": "执1=T+1开盘买→T+1收盘卖(_ops/ledger.py 同口径)；纯度=东财F10 2026H1主营构成机器人链节点占比；纯度>=50%为子集门槛",
        "前视偏差声明": ("纯度取2026H1最新主营构成(多数2026-08后披露)，用于2026-06~07的早期样本属事后口径；"
                    "故另给『20260811后』披露完成期子样本, 结论以该子样本为准。"),
        "子集构成": [{"代码": c, "名称": v["名称"], "纯度": v["purity"],
                   "严格模板": bool(v["strict"] and v["strict"] >= 50), "节点": v["节点"]}
                  for c, v in sorted(uni.items(), key=lambda x: -x[1]["purity"])],
        "子集": stat(events, "纯度>=50% ∧ 涨停"),
        "子集_严格模板节点": stat([r for r in events if r["严格模板"]], "纯度>=50% ∧ 模板节点 ∧ 涨停"),
        "子集_披露后": stat([r for r in events if r["日期"] >= "20260811"], "纯度>=50% ∧ 涨停 ∧ 20260811后"),
        "基准_全池涨停": stat(base_events, "全池涨停(同窗口)"),
        "基准_全池涨停_披露后": stat([r for r in base_events if r["日期"] >= "20260811"], "全池涨停 ∧ 20260811后"),
        "明细": sorted(events, key=lambda x: x["日期"]),
    }
    p = os.path.join(BASE, "_学习", "纯度涨停历史_%s.json" % DATE)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WROTE", p, os.path.getsize(p))
    for k in ["子集", "子集_严格模板节点", "子集_披露后", "基准_全池涨停", "基准_全池涨停_披露后"]:
        print(json.dumps(out[k], ensure_ascii=False))
    print("事件日数", len(days), "子集事件", len(events), "全池事件", len(base_events))
    for r in out["明细"]:
        print(r["日期"], r["代码"], r["名称"], "纯度", r["纯度"], "执1", r["执1"], "连板", r["连板"], "炸", r["炸板"])


if __name__ == "__main__":
    main()
