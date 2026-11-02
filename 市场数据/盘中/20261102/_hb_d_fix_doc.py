# -*- coding: utf-8 -*-
# 校正 决断 文件内部口径：池内读数/跳水窗/落盘说明 全部锚定 2026-11-02 13:32:53 最后一帧
import json, os
os.chdir(r"D:\股票数据\市场数据")
fp = "盘中/20261102/临盘决断_20261102_1330.json"
d = json.load(open(fp, encoding="utf-8"))
fr = [json.loads(l) for l in open("盘中/20261102/realtime_ticks.jsonl", encoding="utf-8")]
aft = [x for x in fr if "2026-11-02 13:00" <= x["ts"] <= "2026-11-02 13:32:53"]
a0, a1 = aft[0], aft[-1]


def st(x):
    rows = {r["code"]: r for r in x["rows"]}
    p = [r["pct"] for r in rows.values()]
    return dict(ts=x["ts"], up=sum(1 for v in p if v > 0), dn=sum(1 for v in p if v < 0),
                ge97=sum(1 for v in p if v >= 9.7), le3=sum(1 for v in p if v <= -3),
                avg=round(sum(p) / len(p), 2))


s0, s1 = st(a0), st(a1)
dz = 0
worst = (0.0, None)
for i in range(1, len(aft)):
    pr = {r["code"]: r for r in aft[i - 1]["rows"]}
    cu = {r["code"]: r for r in aft[i]["rows"]}
    c3 = 0
    for c, r in cu.items():
        if c not in pr:
            continue
        dd = r["pct"] - pr[c]["pct"]
        if dd <= -3:
            c3 += 1
        if dd < worst[0]:
            worst = (dd, (aft[i]["ts"], r["name"], round(dd, 2)))
    if c3 >= 3:
        dz += 1
nwin = len(aft) - 1

d["数据新鲜度"]["池内帧锚"] = "13:00:47（%s）→ 13:32:53（%s），共 %d 帧、%d 个 2 分钟窗" % (
    s0["ts"], s1["ts"], len(aft), nwin)

d["池内读数"]["13:00 → 13:32"] = ("红 %d→%d、绿 %d→%d、涨幅≥9.7%% %d→%d、跌≥3%% %d→%d、池内均涨 +%.2f%%→+%.2f%%"
                                % (s0["up"], s1["up"], s0["dn"], s1["dn"], s0["ge97"], s1["ge97"],
                                   s0["le3"], s1["le3"], s0["avg"], s1["avg"]))
d["池内读数"].pop("13:00 → 13:30", None)
d["池内读数"]["读法"] = ("午后半小时老池均涨由 +%.2f%% 回落至 +%.2f%%（-%.2fpp），红盘家数 %d→%d、跌≥3%% 家数 %d→%d —— "
                    "老池（1030 涨停池）在午后被抽血。同时全市场涨停由 55(11:06) 扩至 86、跌停由 11 收至 7、"
                    "创业板指 +2.04%% → 资金向新题材扩散、不在老池内部提升，属『换手式修复』而非老池二次发酵。"
                    % (s0["avg"], s1["avg"], s0["avg"] - s1["avg"], s0["up"], s1["up"], s0["le3"], s1["le3"]))

d["跳水阈值核验"]["13:00~13:32"] = ("%d 个 2 分钟窗（%s→%s）中，达 ≥3 家门槛的窗 = %d 个；单票最大 2 分钟跌幅 %.2fpp（%s %s）"
                             % (nwin, s0["ts"][11:], s1["ts"][11:], dz, worst[0],
                                worst[1][0] if worst[1] else "-", worst[1][1] if worst[1] else "-"))

d["决断"]["理由"][1] = ("②B 料 0：%s~%s 共 %d 个 2 分钟窗，≥3 只 -3pp 的窗 = %d；三腿无炸板（603533 封板未开）、"
                    "无盘中价止损成立（-5%%/-4%% 均按收盘价）。老池午后抽血（均涨 -%.2fpp）属阴跌不属急杀，"
                    "不达 B 级触发证据。" % (s0["ts"][11:], s1["ts"][11:], nwin, dz, s0["avg"] - s1["avg"]))

d["落盘说明"] = ("决断时戳锚 13:30（cron 触发窗）。本场取数 13:30:47~13:33:0x：realtime_ticks 池内帧 %s→%s（60s/帧、无断帧）；"
             "腾讯 qt 帧 20261102133245~133248 已落 _hb_d_quote_1331.tsv；东财 push2ex 13:32 采集 涨停 tc=86/pool 86、"
             "跌停 tc=7/pool 7（两侧自洽）。盘面读数一律锚定 ≤%s，其后帧不入本件。不回溯改时戳、不覆盖 09:21/09:44/10:30/11:00 已发版。"
             % (s0["ts"], s1["ts"], s1["ts"]))

json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK", fp, os.path.getsize(fp))
print(d["池内读数"]["13:00 → 13:32"])
print(d["跳水阈值核验"]["13:00~13:32"])
print(d["决断"]["理由"][1][:130])
