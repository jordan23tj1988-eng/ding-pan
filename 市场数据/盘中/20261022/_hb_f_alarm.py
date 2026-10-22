# -*- coding: utf-8 -*-
"""hb-f 14:45 追加报警(幂等: 同 session+type 不重复写)"""
import json, os

D = r"D:\股票数据\市场数据\盘中\20261022"
AF = os.path.join(D, "报警_20261022.jsonl")
recs = []
for line in open(AF, encoding="utf-8"):
    line = line.strip()
    if line:
        recs.append(json.loads(line))

new = {
 "ts": "2026-10-22 14:50:12",
 "session": "hb-f_1445",
 "level": "ALARM",
 "type": "ebb_tide_panic_stage",
 "scope": "market_gate",
 "detail": ("跌停池 46(14:31 为27 → 14 分钟 +19 只/+70%)，经腾讯 46/46 逐票确认在跌停价，非取数错误；"
            "全日跌停轨迹 1(10:32)→7(11:04)→14/16(13:31)→27(14:31)→46(14:45)，闸门阈值 12 的 3.8 倍。"
            "炸板率 24/(31+24)=43.64%，距 0.45 闸门仅 1.36pp。涨停 31(首板24/2板3/3板2/5板2)靠低位股维持未跌破 20 → "
            "按 11:00 场既定定义『退潮确认(涨停<20 且 跌停>12)』两腿未齐，定性=确认前一档『退潮恐慌段』。"
            "指数由背离转同向下杀：上证 3664.48(-1.31%)/深成 11405.72(-2.55%)/创业板 2596.61(-3.64%)，创业板较 14:31 再跌 0.58pp。"
            "池内(50)中位 -2.95%、涨19/跌31、≤-9% 9 只。天地板 002388(开=涨停10.01→收跌停8.19)。"
            "5 板 002724/603278 均为『一字开→破板→回封』(002724 今低 10.70)，非真一字。"
            "处置：C 档零新增延续至收盘+次日开盘；持仓 002242 今日 T+1 不可卖、明日 09:30~09:35 减半 450 股、保留 450 股硬止损=收盘破 20.50。"),
 "ref": "临盘决断_20261022_1445.json#当日第一手判断 / #在持票逐票表态"
}
key = (new["session"], new["type"])
if any((r.get("session"), r.get("type")) == key for r in recs):
    print("SKIP 已存在")
else:
    with open(AF, "a", encoding="utf-8") as f:
        f.write(json.dumps(new, ensure_ascii=False) + "\n")
    print("APPENDED, 文件现有行数", len(recs) + 1)
