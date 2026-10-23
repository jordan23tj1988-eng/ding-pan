# -*- coding: utf-8 -*-
"""身位分桶历史对照（logic 20261023 用）
从本地 71 日 zt_pool + bars_cache 复算各『身位桶』的执1(次日开盘买→次日收盘卖)
输出: _学习/身位分桶_20261023.json
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
    out = []
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                out.append({"date": r["date"].replace("-", ""), "open": float(r["open"]),
                            "high": float(r["high"]), "low": float(r["low"]),
                            "close": float(r["close"])})
            except (ValueError, KeyError):
                continue
    return out


def main():
    days = sorted(os.path.basename(os.path.dirname(p))
                  for p in glob.glob(os.path.join(BASE, "20*", "zt_pool.csv")))
    days = [d for d in days if "20260601" <= d <= DATE]
    bars, ev = {}, []
    for d in days:
        for r in csv.DictReader(open(os.path.join(BASE, d, "zt_pool.csv"), encoding="utf-8-sig")):
            code = r["代码"].zfill(6)
            if code not in bars:
                bars[code] = load_bars(code)
            b = bars[code]
            if not b:
                continue
            i = next((k for k, x in enumerate(b) if x["date"] == d), None)
            if i is None or i + 1 >= len(b):
                continue
            nxt = b[i + 1]
            if not nxt["open"]:
                continue
            fbt = r.get("首次封板时间") or ""
            try:
                fbt_i = int(fbt.zfill(6))
            except ValueError:
                fbt_i = 0
            ev.append({
                "d": d, "code": code, "名": r["名称"],
                "执1": (nxt["close"] / nxt["open"] - 1) * 100,
                "首板": str(r.get("连板数")) == "1",
                "连板": int(r.get("连板数") or 0),
                "首封": fbt_i,
                "晚封": fbt_i >= 140000,
                "早封": fbt_i <= 100000,
                "封单比": (float(r["封板资金"]) / float(r["流通市值"]) * 100
                        if r.get("封板资金") and r.get("流通市值") else None),
                "炸": int(r.get("炸板次数") or 0),
                "20cm": code.startswith(("300", "301", "688")),
                "成交亿": float(r["成交额"]) / 1e8 if r.get("成交额") else None,
            })

    def s(rows, label):
        n = len(rows)
        if n < 1:
            return {"桶": label, "n": 0}
        rs = sorted(x["执1"] for x in rows)
        return {"桶": label, "n": n,
                "胜率pct": round(sum(1 for x in rs if x > 0) / n * 100, 1),
                "均收pct": round(sum(rs) / n, 2), "中位pct": round(rs[n // 2], 2)}

    cuts = {
        "A_全池": ev,
        "B_首板": [x for x in ev if x["首板"]],
        "C_首板∧晚封>=1400": [x for x in ev if x["首板"] and x["晚封"]],
        "D_首板∧早封<=1000": [x for x in ev if x["首板"] and x["早封"]],
        "E_首板∧封单比>=1%": [x for x in ev if x["首板"] and (x["封单比"] or 0) >= 1],
        "F_首板∧封单比<0.5%": [x for x in ev if x["首板"] and x["封单比"] is not None and x["封单比"] < 0.5],
        "G_20cm首板": [x for x in ev if x["首板"] and x["20cm"]],
        "H_20cm首板∧晚封": [x for x in ev if x["首板"] and x["20cm"] and x["晚封"]],
        "I_首板∧炸0": [x for x in ev if x["首板"] and x["炸"] == 0],
        "J_首板∧晚封∧炸0": [x for x in ev if x["首板"] and x["晚封"] and x["炸"] == 0],
        "K_首板∧成交>=20亿": [x for x in ev if x["首板"] and (x["成交亿"] or 0) >= 20],
        "L_首板∧晚封∧封单比>=1%": [x for x in ev if x["首板"] and x["晚封"] and (x["封单比"] or 0) >= 1],
        "M_2板∧早封": [x for x in ev if x["连板"] == 2 and x["早封"]],
        "N_2板∧封单比>=2%": [x for x in ev if x["连板"] == 2 and (x["封单比"] or 0) >= 2],
        "O_首板∧成交>=20亿∧晚封": [x for x in ev if x["首板"] and (x["成交亿"] or 0) >= 20 and x["晚封"]],
    }
    out = {"日期": DATE, "口径": "执1=T+1开盘买→T+1收盘卖; 样本=本地zt_pool 20260601~20261023 全部涨停事件(需有T+1 bars)",
           "样本": len(ev), "分桶": [s(v, k) for k, v in cuts.items()]}
    p = os.path.join(BASE, "_学习", "身位分桶_%s.json" % DATE)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WROTE", p, os.path.getsize(p), "事件", len(ev))
    for r in out["分桶"]:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
