# -*- coding: utf-8 -*-
"""hb-b 10:30 心跳决断生成器（20261102）——只读 tick/报价，写 临盘决断_20261102_1030.json + 报警追加行。"""
import json, datetime, os, urllib.request

D = r"D:\股票数据\市场数据\盘中\20261102"
fr = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
last = fr[-1]
ts_list = [datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") for f in fr]
now = datetime.datetime.now()

def snap(f):
    rr = f["rows"]
    return dict(ts=f["ts"], mean=round(sum(r["pct"] for r in rr) / len(rr), 2),
                red=sum(1 for r in rr if r["pct"] > 0), green=sum(1 for r in rr if r["pct"] < 0),
                zt=sum(1 for r in rr if r["pct"] >= 9.7), lt3=sum(1 for r in rr if r["pct"] <= -3))

s944 = snap([f for f in fr if f["ts"] == "2026-11-02 09:44:08"][0])
snow = snap(last)

# 全时段两分钟窗批量跳水扫描
worst_n, worst_d, worst_t, recent = 0, None, None, []
for i in range(len(fr)):
    j = max([k for k in range(i + 1) if (ts_list[i] - ts_list[k]).total_seconds() >= 110], default=None)
    if j is None:
        continue
    m = {r["code"]: r["pct"] for r in fr[j]["rows"]}
    drops = [((r["pct"] - m[r["code"]]), r["code"], r["name"]) for r in fr[i]["rows"] if r["code"] in m]
    n = sum(1 for d in drops if d[0] <= -3)
    if n > worst_n:
        worst_n, worst_d, worst_t = n, min(drops), fr[i]["ts"]
    if (now - ts_list[i]).total_seconds() <= 8 * 61:
        recent.append((fr[i]["ts"], n, round(min(drops)[0], 2), min(drops)[2]))
recent_max = max(x[1] for x in recent)

# 持仓报价（腾讯 qt，只读取价）
codes = ["sh603037", "sh603533", "sh601188", "sh000001", "sz399001", "sz399006"]
req = urllib.request.Request("https://qt.gtimg.cn/q=" + ",".join(codes),
                             headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
txt = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
q, rows_tsv = {}, ["tick\tname\tlast\tpct\topen\thigh\tlow\tbid1\task1"]
for seg in txt.strip().split(";"):
    if '="' not in seg:
        continue
    f = seg.split('="', 1)[1].strip('"\n').split("~")
    if len(f) < 40:
        continue
    q[f[2]] = dict(ts=f[30], name=f[1], last=float(f[3]), pct=float(f[32]), open=float(f[5]),
                   high=float(f[33]), low=float(f[34]), bid1=float(f[9]), ask1=float(f[19]))
    rows_tsv.append("\t".join([f[30], f[1] + f[2], f[3], f[32], f[5], f[33], f[34], f[9], f[19]]))
open(os.path.join(D, "_hb_b_quote_1033.tsv"), "w", encoding="utf-8").write("\n".join(rows_tsv) + "\n")

pos = [("603037", "凯众股份", 200, 11.87, 10.42), ("603533", "掌阅科技", 200, 28.33, 24.82),
       ("601188", "龙江交通", 4200, 3.47, 3.22)]
pos_rows, tot_gap = [], 0.0
for code, name, sh, cst, pxe in pos:
    l = q[code]
    d = (l["last"] - pxe) * sh
    tot_gap += d
    pos_rows.append(dict(code=code, name=name, shares=sh, buy_px=cst, now=l["last"], now_pct=l["pct"],
                         今开=l["open"], 今高=l["high"], 今低=l["low"], px_exec_0944=pxe,
                         相对px_exec_pct=round((l["last"] / pxe - 1) * 100, 2),
                         未平差额元=round(d, 2),
                         浮亏pct_vs_cost=round((l["last"] / cst - 1) * 100, 2)))

doc = {
 "date": "20261102", "session": "hb-b", "ts": "10:30",
 "write_ts": now.strftime("%Y-%m-%d %H:%M:%S"),
 "版本": "sentiment-review-system v2.15 · 13号盘中作战agent 心跳hb-b(10:30趋势确认段)",
 "落盘说明": ("决断时戳锚 10:30（cron 触发窗）。本场取数 10:31:18~10:33:22：realtime_ticks 末帧 10:33:18（63 帧），"
           "腾讯 qt 帧 20261102103256~103300 已留档 _hb_b_quote_1033.tsv。不回溯改时戳、不覆盖 09:21/09:44 已发版。"),
 "交易日校验": ("规格命令 python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → "
             "ModuleNotFoundError: No module named 'sentiment'（D:\\股票数据 全树无 sentiment 包，20261020 起规格漂移，非本场故障）；"
             "等效真源：①realtime_ticks.jsonl 今日 09:31:06~10:33:18 共 63 帧连续非空、最大帧间隔 61s 无断帧；"
             "②腾讯帧时间戳 20261102103256~103300，三票现价与昨收（11.49/24.29/3.26）衔接；"
             "③东财 push2ex 涨停/跌停池 qdate=20261102 有数据（tc=48/16）→ 判定 20261102 为交易日"),
 "数据新鲜度": {
   "ticks": f"realtime_ticks.jsonl 末帧 {last['ts']}，读取 {now.strftime('%H:%M:%S')}，龄约 {(now - datetime.datetime.strptime(last['ts'],'%Y-%m-%d %H:%M:%S')).total_seconds():.0f} 秒，60s/帧无断更 → 未触『断更>10分钟只报警禁决策』",
   "报价": "腾讯 qt 实拉 10:32:56~10:33:00，已落 _hb_b_quote_1033.tsv",
   "广度": "东财 push2ex 10:31 采集：涨停池 48 只 / 跌停池 16 只（qdate=20261102）",
   "pulse.json": "不存在（自 20261020 起长期不产出）→ 官方新鲜度锚缺失，改用 ticks 末帧替代",
   "warboard.json": "不存在 → 持仓源改 master/state.json（mtime 2026-10-30 20:27，positions=3）",
   "执行流水.jsonl": "不存在（10:33 复查仍无）→ 09:21 两笔买入腿、09:44 三笔卖腿至今 0 行引擎回执",
 },
 "数据缺口登记": [
   "①pulse.json / warboard.json / 执行流水.jsonl 三件自 20261020 起长期不产出（成交回执链路缺失），本场仍无引擎回执 → 本件所有权衡均为『决断单』，非引擎确认单；",
   "②playbook.json（盘中/20261102，mtime 10-30 19:50）date=20261030、sells=[]：预案认为 0 持票，与 master/state.json 3 只持仓口径分歧（09:44 已登记，本场不重复处置、不改 playbook）；",
   "③sentiment 包全树缺失（长期规格漂移，连续登记）；",
   "④心跳无写引擎回执权限，也无权改权重/闸门 → 缺口只能报警与交接，不得以『视为已成交』自愈。",
 ],
 "持仓快照": {
   "源": "_学习/_模拟盘/master/state.json（cash 963209.54，positions 3 只；mtime 2026-10-30 20:27 未变）",
   "持仓": pos_rows,
   "未平差额合计元": round(tot_gap, 2),
   "解读": ("三腿差额为正＝09:44 决断价至今『没卖出反而更值钱』（603037 由 -9.66% 反抽至 -4% 附近、601188 由 -1.84% 转红）。"
          "但这是执行缺口带来的偶然结果，不是本场可以追认的成交价：px_exec 已于 09:44 冻结（10.42/24.82/3.22），"
          "本场不得按现价改记成交（否则＝用后来走势改口径，属后视镜）。"),
   "第七账(盘中作战)": "_学习/_模拟盘/盘中作战/state.json：cash 996990.24、positions=[]（mtime 2026-11-02 09:25:52）→ 本场无该账卖单",
 },
 "池内读数": {
   "池": f"47 只（20261030 涨停池，pool_stale={'false' if last.get('pool_date')=='20261030' else 'true'}）",
   "09:44 → 10:33": (f"红 {s944['red']}→{snow['red']}、绿 {s944['green']}→{snow['green']}、"
                    f"涨幅≥9.7% {s944['zt']}→{snow['zt']}、跌≥3% {s944['lt3']}→{snow['lt3']}、"
                    f"池内均涨 {s944['mean']:+.2f}%→{snow['mean']:+.2f}%"),
   "读法": "池内均涨抬升、涨幅≥9.7% 由 6 增至 10 → 昨日涨停池的赚钱效应回暖，但池内炸板仍 6 只（盛洋科技/上海沪工/黑芝麻/沈阳机床/迎驾贡酒/古井贡酒），属『指数回暖、池内分化』而非全面转强",
   "watch 三票(观察,权重0)": "301132 满坤科技 09:31 -9.65% → 10:33 -0.98%；601083 锦江航运 2.66%→1.79%；301520 万邦医药 -2.60%→-1.78% → 301132 three-confirm（封板比≥3%/换手<10%/再封）本场均未成立，权重维持 0",
 },
 "跳水阈值核验": {
   "口径": "相邻两帧（≈61s×2）池内个股 pct 差 ≤ -3pp 的家数",
   "全时段最大同窗家数": worst_n, "最差时点": worst_t,
   "最差单票": f"{worst_d[2]}({worst_d[1]}) {round(worst_d[0],2)}pp" if worst_d else None,
   "近8窗(10:14~10:33)最大同窗家数": recent_max,
   "结论": f"10:27~10:33 各窗 ≤-3pp 家数均为 0（最差单票迎驾贡酒 -2.29pp 属炸板非批量），未达『≥3 只 2 分钟内 -3%』批量跳水门槛 → 不触发题材级 B 级防守；全时段最大 6 只出现在 09:33（早于本场且非持仓）",
 },
 "持仓风险核验": {
   "炸板": "三腿均非今日涨停票，无『持仓炸板』情形（603037 昨收 11.49、今开 10.89 低开 5.2%）",
   "大幅回撤": "最深回撤 603037 当日最低 10.34（10.34＝跌停价 11.49×0.9，曾触板），当前 11.03 距日低 +6.7%；三腿均无新的 -5% 收盘价止损触发（收盘价口径，盘中不预判）",
   "结论": "无新增 B 级防守单；09:44 已发三笔逾期清出卖腿（A 级既有纪律）本场不重复发（重复卖＝凭空造单）",
 },
 "全场广度": {
   "涨停/跌停": "涨停 48 / 跌停 16（10:31 东财；对比 09:26 的 7/9 → 两头同时变厚）",
   "指数": f"上证 {q['000001']['last']} {q['000001']['pct']:+.2f}%、深成 {q['399001']['last']} {q['399001']['pct']:+.2f}%、创业板指 {q['399006']['last']} {q['399006']['pct']:+.2f}%",
   "读法": "指数翻红＋涨停扩容，但跌停同步由 9 增至 16＝分化极端化；昨日涨停池炸弹率 6/47≈12.8%，池内封板率未见改善 → 属退潮中的指数反抽，非情绪反转确认",
 },
 "决断": {
   "等级": "无新增买卖（fills=[]）；本场性质＝执行缺口续催告警＋趋势确认段读数",
   "A料执行": 0, "B料防守": 0, "C料进攻": 0,
   "理由": [
     "①预案内 buys 已过期：playbook 四腿（002365 2.0%/001287 1.0%/001219/000995）的执行价写死为『20261102 开盘价唯一执行价、不追价不摊薄』；10:33 开盘价不可得，按现价 12.69/20.42 补买＝追价且改执1口径 → 沿 09:44 结论维持 0 敞口。机会成本实测量级：两腿自开盘仅 +0.71%/+0.84%（名义 3.0% → 约 +250 元未发生），不构成补买理由。",
     "②预案内 sells 已在 09:44 发版（603037×200@10.42 / 603533×200@24.82 / 601188×4200@3.22），本场复查 0 回执、master 账仍 3 仓 → 按纪律只续催、不重发、不改 px（见 报警 第 2 条）。",
     "③防守未触发：10:27~10:33 各 2 分钟窗 ≤-3pp 家数 0（最差 -2.29pp），未达 ≥3 只批量跳水；三腿无炸板、无新的收盘止损条件成立 → 不立 B 单。",
     "④进攻不做：全市场涨停 48/跌停 16 呈两头变厚、池内炸板 6 只、指数仅收复至 +0.23%/+0.61%/+0.77%，属退潮中反抽而非反转；叠加执行链路 0 回执（连既有 5 笔都无法核销），在无法确认成交的链路里新增敞口＝放大不可核销仓位 → 无 C 级证据，仅记录不入场。",
     "⑤本场未改任何阈值/权重/闸门/组合，未产生新的价格基准；一切读数只用 10:33 前已留档 tick。",
   ],
 },
 "fills": [],
 "报警": {
   "file": "盘中/20261102/报警_20261102.jsonl",
   "type": "execution_chain_zero_receipt_continuation",
   "等级": "ALARM",
   "内容": ("09:44 三笔卖腿（603037×200@10.42 / 603533×200@24.82 / 601188×4200@3.22，名义 20,572 元）至 10:33 仍无执行流水回执，"
          "master/state.json 持仓未变（mtime 仍 2026-10-30 20:27）；同期三腿现价 11.03/24.75/3.31 相对 px_exec 差 +122/-14/+378 元（合计 +486 元，"
          "方向偶然有利）→ 缺口当前未致损，但敞口仍真实存在、无法核销。"),
 },
 "下一场交接": {
   "hb-c(11:00)": ("①继续查 执行流水.jsonl / warboard.json / pulse.json 是否出现：若出回执→按回执核销；若仍 0 行且 master 仍 3 仓→继续告警，不由心跳重复发 fill；"
                 "②三腿价格跟踪（603037 已由跌停 10.34 反抽至 11.03，若回到 11.0 上方仍属超出 09:44 px_exec，须由结算层按冻结价核销，不得改价）；"
                 "③全市场涨停 48/跌停 16 的剪刀差是否继续扩大，池内炸板 6 只是否回封；"
                 "④watch 301132 若真封板，仅登记不进 buys（预案条款：次日评审）。"),
 },
 "免责": "本件为盘中判断留档，非操盘指令；所有价格均为决断前已留档 tick，浮盈亏以结算引擎为准。",
}

out = os.path.join(D, "临盘决断_20261102_1030.json")
json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", out, os.path.getsize(out))
alarm = {
 "ts": now.strftime("%Y-%m-%d %H:%M:%S"), "session": "hb-b", "date": "20261102", "level": "ALARM",
 "type": "execution_chain_zero_receipt_continuation",
 "scope": "09:44 场 3 笔逾期清出卖腿（603037×200/603533×200/601188×4200，名义 20,572 元）＋ 0921 场 2 笔买入 A 腿（0 敞口）",
 "detail": doc["报警"]["内容"],
 "root_cause": "盘中引擎成交回执链路缺失（pulse/warboard/执行流水 自 20261020 起长期不产出）；心跳无写回执权限，只能报警与交接",
 "evidence": ["盘中/20261102/临盘决断_20261102_1030.json#决断", "盘中/20261102/_hb_b_quote_1033.tsv",
              "盘中/20261102/realtime_ticks.jsonl 末帧 " + last["ts"],
              "_学习/_模拟盘/master/state.json mtime 2026-10-30 20:27 positions=3"],
 "market_snapshot_intraday": {"ts": "2026-11-02 10:33", "池内红": snow["red"], "池内绿": snow["green"],
                              "池内总数": len(last["rows"]), "池内涨幅≥9.7%": snow["zt"], "池内炸板": 6,
                              "两分钟最大跌幅pp": round(worst_d[0], 2) if worst_d else None,
                              "涨停": 48, "跌停": 16},
 "positions": [{"code": p["code"], "name": p["name"], "shares": p["shares"], "last": p["now"], "pct": p["now_pct"],
                "px_exec_0944": p["px_exec_0944"], "diff_yuan": p["未平差额元"]} for p in pos_rows],
}
with open(os.path.join(D, "报警_20261102.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps(alarm, ensure_ascii=False) + "\n")
print("ALARM appended")
print(json.dumps({"pool": doc["池内读数"]["09:44 → 10:33"], "gap": round(tot_gap, 2), "recent_max": recent_max}, ensure_ascii=False))
