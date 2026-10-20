# -*- coding: utf-8 -*-
"""hb-e 14:30 口径统一: 封板/炸板一律用『板块涨停价』判(before: 环境块沿用了 naive pct>=9.7, 把 20cm 金盾股份误计为封板) → 重算 11:05 与 14:37 两帧, 同法可比。"""
import json, statistics

D = r"D:\股票数据\市场数据\盘中\20261019"
P = D + r"\尾盘备料_20261019_1430.json"
frames = [json.loads(l) for l in open(D + r"\realtime_ticks.jsonl", encoding="utf-8") if l.strip()]

def limi(pc, code):
    return round(pc * 1.2, 2) if code[:3] in ("688", "300", "301") else round(pc * 1.1, 2)

def stat(f):
    rows = f["rows"]
    seal, touch = [], []
    for r in rows:
        L = limi(r["preClose"], r["code"])
        if r["latest"] >= L - 0.005:
            seal.append(r)
        if r["high"] >= L - 0.005:
            touch.append(r)
    pcts = [r["pct"] for r in rows]
    return dict(ts=f["ts"], n=len(rows), seal=len(seal), touch=len(touch),
                zha=len(touch) - len(seal), rate=round(len(seal) / max(len(touch), 1), 3),
                median=round(statistics.median(pcts), 2), mean=round(statistics.mean(pcts), 2),
                up=sum(1 for p in pcts if p > 0), dn=sum(1 for p in pcts if p < 0),
                dn5=sum(1 for p in pcts if p <= -5), dn8=sum(1 for p in pcts if p <= -8),
                dt=[(r["code"], r["name"], r["pct"]) for r in rows if r["pct"] <= -9.8],
                seal_names=[(r["code"], r["name"], r["pct"]) for r in seal])

a = stat([f for f in frames if f["ts"] <= "2026-10-19 11:05:00"][-1])
b = stat(frames[-1])

doc = json.load(open(P, encoding="utf-8"))
doc["环境"] = {
    "口径": "封板=最新价≥板块涨停价(主板 round(preClose*1.1,2), 创业/科创 round(preClose*1.2,2)); 触板=最高价≥该价; 炸板=触而未封。11:05 与 14:37 两帧同法重算, 避免与 11:00 件的 naive(pct≥9.7)口径混比。",
    "池内截面_1105": {"帧": a["ts"], "n": a["n"], "封板": a["seal"], "触板": a["touch"], "炸板": a["zha"], "封板率": a["rate"],
                    "中位pct": a["median"], "均值pct": a["mean"], "涨/跌": [a["up"], a["dn"]], "跌>5%": a["dn5"], "跌>8%": a["dn8"], "跌停": len(a["dt"])},
    "池内截面_1437": {"帧": b["ts"], "n": b["n"], "封板": b["seal"], "触板": b["touch"], "炸板": b["zha"], "封板率": b["rate"],
                    "中位pct": b["median"], "均值pct": b["mean"], "涨/跌": [b["up"], b["dn"]], "跌>5%": b["dn5"], "跌>8%": b["dn8"],
                    "跌停": ["%s %s %.2f%%" % x for x in b["dt"]],
                    "封板票": ["%s %s %+.2f%%" % x for x in b["seal_names"]]},
    "对比": "封板 %d→%d, 炸板 %d→%d, 封板率 %.3f→%.3f, 中位 %+.2f→%+.2f, 均值 %+.2f→%+.2f" % (
        a["seal"], b["seal"], a["zha"], b["zha"], a["rate"], b["rate"], a["median"], b["median"], a["mean"], b["mean"]),
    "判读": ("池内(10/16涨停池)尾盘边际回暖: 封板 %d→%d、封板率 %.3f; 但中位 %+.2f%%、均值 %+.2f%% = 昨日涨停股今日赚钱效应微弱, 退潮底色未改。"
           "结构分化: 出版传媒线 4 只 ≤-9%%(3 只跌停)批量跳水, 设备/低空线多票封板; 在持三票(水泥/电力/电子)不在跳水线上。"
           "全市场封板率与两市量能 无源 → null, 不编。") % (a["seal"], b["seal"], b["rate"], b["median"], b["mean"]),
}
doc["本场判定"]["为何不买"] = ("①A级买入腿已全部作废(300045 开盘 gap +7.01%% 越上沿; 600802 受『与600668同线同持』剔除); "
                        "②池内封板率 %.3f、中位 %+.2f%% 仅属弱修复, 不构成退潮转攻证据; ③今日全场维持零新增暴露, 本场不开新口。" % (b["rate"], b["median"]))
doc["自审记录"].append({
    "ts": __import__("time").strftime("%Y-%m-%d %H:%M:%S"), "类型": "SELF_AUDIT_METHOD_UNIFY",
    "问题": "环境块首稿沿用 naive pct≥9.7 口径(封板12/触板20/炸板8), 把 20cm 金盾股份(+14.27%)误计为封板; 与本场判定里按涨停价判的 11/15/4 并存 → 同一件内两套口径。",
    "修正": "统一为板块涨停价口径: 11:05 帧 封板%d/触板%d/炸板%d/封板率%.3f; 14:37 帧 封板%d/触板%d/炸板%d/封板率%.3f; 环境块与判定文字同步改写。" % (
        a["seal"], a["touch"], a["zha"], a["rate"], b["seal"], b["touch"], b["zha"], b["rate"]),
    "未修正项": "零成交(fills=[])不变; 持仓结论不变; 未改账本/state/playbook/参数。"})

json.dump(doc, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("11:05", a["seal"], a["touch"], a["zha"], a["rate"], a["median"], "| 14:37", b["seal"], b["touch"], b["zha"], b["rate"], b["median"])
