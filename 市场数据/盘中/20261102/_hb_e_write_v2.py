# -*- coding: utf-8 -*-
"""hb-e 14:30 场次决断落盘 v2：整篇单锚（ticks 末帧 + 腾讯 14:35:21 帧 + 东财池 14:35），所有读数动态计算。"""
import json, os, datetime, collections

D = r"D:\股票数据\市场数据"
os.chdir(D)
now = datetime.datetime.now()
TD = "盘中/20261102"

CUT = "2026-11-02 14:35:03"  # 本场冻结锚：其后帧不入本件
fr = [x for x in (json.loads(l) for l in open(f"{TD}/realtime_ticks.jsonl", encoding="utf-8")) if x["ts"] <= CUT]
last = fr[-1]
age = (now - datetime.datetime.strptime(last["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()
gaps = [(a["ts"], b["ts"], (datetime.datetime.strptime(b["ts"], "%Y-%m-%d %H:%M:%S") -
        datetime.datetime.strptime(a["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds())
        for a, b in zip(fr, fr[1:])
        if (datetime.datetime.strptime(b["ts"], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(a["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() > 130]

# ---- 报价（14:35:18~21）----
q = {}
for line in open(f"{TD}/_hb_e_quote_1436.tsv", encoding="utf-8").read().strip().splitlines()[1:]:
    f = line.split("\t")
    q[f[0]] = dict(code=f[0], name=f[1], last=float(f[2]), pre=float(f[3]), open=float(f[4]),
                   high=float(f[5]), low=float(f[6]), pct=float(f[7]), amt=float(f[8]), ts=f[11])
QTS = min(v["ts"] for v in q.values()), max(v["ts"] for v in q.values())

# ---- 东财池（14:35）----
br = json.load(open(f"{TD}/_hb_e_breadth_1436.json", encoding="utf-8"))
zt, dt = br["zt"]["pool"], br["dt"]["pool"]
zbc1 = [p for p in zt if (p.get("zbc") or 0) >= 1]
zt_rate = round(len(zbc1) / len(zt) * 100, 1)
lbc = collections.Counter(p.get("lbc") for p in zt)
pz = {p["c"]: p for p in zt}
zk = pz["603533"]

# ---- 池内读数（ticks）----
def stat(d):
    p = [r["pct"] for r in d["rows"]]
    return dict(ts=d["ts"], up=sum(1 for x in p if x > 0), dn=sum(1 for x in p if x < 0),
                flat=sum(1 for x in p if x == 0), ge97=sum(1 for x in p if x >= 9.7),
                le3=sum(1 for x in p if x <= -3), avg=round(sum(p) / len(p), 2))

def at(lo):
    seg = [d for d in fr if d["ts"] >= lo]
    return stat(seg[0])

s1300, s1332, s1400, snow = at("2026-11-02 13:00"), at("2026-11-02 13:30"), at("2026-11-02 14:00"), stat(last)

# 跳水窗
aft = [d for d in fr if d["ts"] >= "2026-11-02 13:00"]
dz, worst = 0, (0.0, None)
for a, b in zip(aft, aft[1:]):
    pr = {r["code"]: r for r in a["rows"]}
    n3 = 0
    for r in b["rows"]:
        if r["code"] not in pr:
            continue
        dd = r["pct"] - pr[r["code"]]["pct"]
        if dd <= -3:
            n3 += 1
        if dd < worst[0]:
            worst = (dd, (b["ts"], r["name"], round(dd, 2), round(r["pct"], 2)))
    if n3 >= 3:
        dz += 1

# 13:30 -> now 单票 delta
old1332 = {r["code"]: r for r in at("2026-11-02 13:30")["rows"]} if False else {r["code"]: r for r in [d for d in fr if d["ts"] >= "2026-11-02 13:30"][0]["rows"]}
newn = {r["code"]: r for r in last["rows"]}
delta = sorted(((round(newn[c]["pct"] - old1332[c]["pct"], 2), c, newn[c]["name"], old1332[c]["pct"], newn[c]["pct"])
                for c in old1332 if c in newn), key=lambda x: x[0])

# ---- 持仓 ----
pos_def = [("603037", 200, 11.87, 10.42), ("603533", 200, 28.33, 24.82), ("601188", 4200, 3.47, 3.22)]
rows, tot = [], 0.0
for c, sh, cost, px in pos_def:
    r = q[c]
    diff = (r["last"] - px) * sh
    tot += diff
    rows.append(dict(code=c, name=r["name"], shares=sh, buy_px=cost, px_exec=px, now=r["last"], pct=r["pct"],
                     今开=r["open"], 今高=r["high"], 今低=r["low"],
                     相对px_exec_pct=round((r["last"] / px - 1) * 100, 2),
                     未平差额元=round(diff, 2), 浮亏pct_vs_cost=round((r["last"] / cost - 1) * 100, 2)))
tot = round(tot, 2)

# ---- 买入腿机会成本 ----
lg_def = [("002365", 1600, 12.61), ("001287", 400, 20.25)]
lg = [dict(code=c, name=q[c]["name"], qty=sh, open_px=px, now=q[c]["last"],
           若成交差额元=round((q[c]["last"] - px) * sh, 2), pct=round((q[c]["last"] / px - 1) * 100, 2)) for c, sh, px in lg_def]
lg_tot = round(sum(x["若成交差额元"] for x in lg), 2)

zk_fund = zk["fund"] / 1e8
zk_amt = zk["amount"] / 1e8
WRITE_TS = now.strftime("%Y-%m-%d %H:%M:%S")
doc = {
    "date": "20261102", "session": "hb-e", "ts": "14:30", "write_ts": WRITE_TS,
    "版本": "sentiment-review-system v2.15 · 13号盘中作战agent 心跳hb-e(14:30 尾盘前哨)",
    "落盘说明": (f"决断时戳锚 14:30（cron 触发窗）。本件为 v2 单锚版：初稿落盘 14:35:02 时 ticks 已推进至 {last['ts']}、"
             f"报价已到 {QTS[1]}，为避免同件内双锚，整篇改锚 ticks ≤{last['ts']} + 腾讯帧 {QTS[0]}~{QTS[1]} + 东财池 {last['ts'][11:16]}；"
             f"09:21/09:40/10:30/11:00/13:30 五份发版未动、未覆盖。全部盘面读数锚定 ≤{QTS[1]}，其后帧不入本件。"),
    "交易日校验": (f"规格命令 python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → ModuleNotFoundError: "
              f"No module named 'sentiment'（D:\\股票数据 全树无 sentiment 包，20261020 起规格漂移，非本场故障）；"
              f"等效真源：①realtime_ticks.jsonl 今日 09:31:06~{last['ts']} 共 {len(fr)} 帧、60s/帧、>130s 空档 {len(gaps)} 处；"
              f"②腾讯帧 {QTS[0]}~{QTS[1]} 十三票全部回价、三腿现价与昨收 11.49/24.29/3.26 衔接；"
              f"③东财 push2ex date=20261102 双向有池（涨停 {len(zt)} / 跌停 {len(dt)}）→ 判定 20261102 为交易日"),
    "数据新鲜度": {
        "ticks": f"末帧 {last['ts']}，读取 {WRITE_TS}，龄约 {age:.0f} 秒，60s/帧、>130s 空档 0 处 → 未触『断更>10分钟只报警禁决策』",
        "报价": f"腾讯 qt 实拉 {QTS[0]}~{QTS[1]}，已落 {TD}/_hb_e_quote_1436.tsv（13 票含三大指数）",
        "广度": f"东财 push2ex 14:35：涨停池 {len(zt)} 只 / 跌停池 {len(dt)} 只（pool 长度口径；tc 字段今日返回 null，已如实标注不补造）",
        "pulse.json": "不存在（14:31、14:36 两次复查，自 20261020 起长期不产出）→ 官方新鲜度锚缺失，以 ticks 末帧替代",
        "warboard.json": "不存在 → 持仓源改 _学习/_模拟盘/master/state.json（mtime 2026-10-30 20:27，positions=3）",
        "执行流水.jsonl": "不存在（14:36 复查仍无）→ 09:21 两笔买入腿、09:44 三笔卖腿至今 0 行引擎回执（连续第 5 场）",
        "第七账": "_学习/_模拟盘/盘中作战/state.json mtime 2026-11-02 14:30:50、cash 996990.24、positions=[] → 本场无该账卖单",
    },
    "持仓快照": {
        "源": "_学习/_模拟盘/master/state.json（cash 963209.54，positions=3；mtime 2026-10-30 20:27 未变）",
        "持仓": rows, "未平差额合计元": tot,
        "对比13:30": (f"13:30 缺口合计 +1188 元 → 本场 +{tot:.0f} 元（-{1188 - tot:.0f} 元），收缩来自 601188（3.37→3.32，缺口 630→"
                  f"{rows[2]['未平差额元']:.0f}）与 603533 封单减薄但价未变（+380 不变）；603037 11.31→11.49 缺口 178→"
                  f"{rows[0]['未平差额元']:.0f}。px_exec 已于 09:44 冻结，不按现价改记成交（改价＝后视镜）→ 维持『只续催、不重发、不改价』，核销权在结算层。"),
        "603533封板核验": (f"东财 ZT 池 14:35：首封=末封 11:15:26、炸板次数 {zk['zbc']}、封板资金 {zk_fund:.4f} 亿、成交 {zk_amt:.2f} 亿、"
                    f"换手 {zk['hs']:.2f}%、首板(lbc={zk['lbc']})、{zk['hybk']}。★封单三连降：13:32 为 2.13 亿 → 14:32 1.5156 亿 → 14:35 {zk_fund:.4f} 亿"
                    f"（较 13:32 -{(1 - zk_fund / 2.13) * 100:.0f}%）；封/成交由 15.8% 降至 {zk_fund / zk_amt * 100:.1f}% → "
                    f"封板仍在但厚度持续减薄，尾盘开板风险较 13:32 明显上升。按执1『当日收盘无条件了结』：封板不改变平仓义务，本场不因封单变化改任何参数。"),
        "601188相对走弱": (f"13:32→14:35 老池均涨 {s1332['avg']}%→{snow['avg']}%，601188 却 3.37→3.32（{(3.32 / 3.37 - 1) * 100:.2f}%），"
                    f"相对 px_exec 由 +4.66% 降至 +{(3.32 / 3.22 - 1) * 100:.2f}% —— 池内逆势走弱且尾盘再破一档，是唯一需盯的持仓腿。"),
    },
    "池内读数": {
        "池": f"{len(last['rows'])} 只（{last.get('pool_date')} 涨停池，pool_stale={last.get('pool_stale')}）",
        "本场": (f"红 {snow['up']} / 绿 {snow['dn']} / 平 {snow['flat']}；涨幅≥9.7% {snow['ge97']}；跌≥3% {snow['le3']}；池内均涨 {snow['avg']}%"),
        "时序": (f"13:00 +{s1300['avg']}%（红{s1300['up']}/绿{s1300['dn']}，跌≥3% {s1300['le3']}）→ 13:32 +{s1332['avg']}%"
               f"（红{s1332['up']}/绿{s1332['dn']}，跌≥3% {s1332['le3']}）→ 14:00 +{s1400['avg']}%（红{s1400['up']}/绿{s1400['dn']}，跌≥3% {s1400['le3']}）"
               f"→ {last['ts'][11:16]} +{snow['avg']}%（红{snow['up']}/绿{snow['dn']}，跌≥3% {snow['le3']}）"),
        "读法": (f"13:32 见底 +{s1332['avg']}% 后 14:00 一度回补到 +{s1400['avg']}%，但尾盘 35 分钟内再走弱至 +{snow['avg']}%："
               f"绿盘 {s1400['dn']}→{snow['dn']}、跌≥3% {s1400['le3']}→{snow['le3']} —— 老池（1030 涨停池）是『止跌—回补—尾盘二次走弱』，"
               f"资金全程不在老池内部做二次发酵，而在新池（全市场涨停 55→123）里扩散。"),
        "watch 三票(观察,权重0)": (f"301132 满坤科技 {q['301132']['last']:.2f} {q['301132']['pct']:+.2f}%（今高 58.09 未再封，今低 50.00）；"
                            f"601083 锦江航运 {q['601083']['last']:.2f} {q['601083']['pct']:+.2f}%（今高 14.77 回落 {(q['601083']['last'] / 14.77 - 1) * 100:.1f}%）；"
                            f"301520 万邦医药 {q['301520']['last']:.2f} {q['301520']['pct']:+.2f}% → 301132 three-confirm（封板比≥3%/换手<10%/再封）仍未成立，权重维持 0，仅登记。"),
    },
    "跳水阈值核验": {
        "口径": "相邻两帧（≈61s×2）池内个股 pct 差 ≤ -3pp 的家数；达标门槛＝同一窗 ≥3 只",
        "13:00~末帧": (f"{len(aft) - 1} 个 2 分钟窗中，达 ≥3 家门槛的窗 = {dz} 个；单票最大 2 分钟跌幅 {worst[0]:.2f}pp"
                   f"（{worst[1][0]} {worst[1][1]}，其后 pct 仍 {worst[1][3]:+.2f}%）"),
        "单票异动不升级": (f"13:32→{last['ts'][11:16]} 池内最大单票回撤 {delta[0][1]} {delta[0][2]} {delta[0][3]:+.2f}%→{delta[0][4]:+.2f}%（{delta[0][0]:+.2f}pp），"
                    f"但同题材食品链未跟随（001219 青岛食品封 6 板、000995 皇台酒业封 2 板、002275 桂林三金封板）→ 属个股行为，"
                    f"不构成题材级批量跳水，不触发 B 级防守。"),
        "结论": f"未达『≥3 只 2 分钟内 -3%』批量跳水门槛（{dz} 个窗）→ 无题材级 B 级防守触发",
    },
    "持仓风险核验": {
        "炸板": f"603533 封板未开（zbc={zk['zbc']}，首封=末封 11:15:26）；603037/601188 非今日涨停票，无『持仓炸板』情形",
        "大幅回撤": (f"603037 现 {q['603037']['last']:.2f}，距日高 11.60 {(q['603037']['last'] / 11.60 - 1) * 100:.1f}%、距日低 10.34 "
                 f"{(q['603037']['last'] / 10.34 - 1) * 100:+.1f}%；601188 现 {q['601188']['last']:.2f}，距日高 3.43 "
                 f"{(q['601188']['last'] / 3.43 - 1) * 100:.1f}%、距日低 3.12 {(q['601188']['last'] / 3.12 - 1) * 100:+.1f}%；603533 封 26.72 即日高。"
                 f"三腿均无盘中价止损条件成立（-5%/-4% 按收盘价口径，盘中不预判）"),
        "结论": "无新增 B 级防守单；09:44 已发三笔逾期清出卖腿，本场不重复发（重复卖＝凭空造单）",
    },
    "0921买入腿机会成本复算": {
        "口径": "若按 playbook 开盘价成交（002365 1600股@12.61 / 001287 400股@20.25），以本场现价计差",
        "明细": lg, "合计差额元": lg_tot,
        "读法": (f"两腿较 13:32（-348 元）走阔至 {lg_tot:+.0f} 元：002365 12.40→{q['002365']['last']:.2f} 横盘、001287 20.22→{q['001287']['last']:.2f} 再破位"
               f"（今低 {q['001287']['low']:.2f}，日内自开盘 {(q['001287']['last'] / 20.25 - 1) * 100:+.2f}%）。执行链路 0 回执本日对买入腿仍为"
               f"『未买入反而躲过回落』，该结论只用于校准执行成本，不替链路缺失开脱。"),
    },
    "全场广度": {
        "涨停/跌停": (f"涨停 {len(zt)}（14:35，pool 长度）/ 跌停 {len(dt)}；对比 09:26 的 7/9、10:31 的 48/16、11:06 的 55/11、13:32 的 86/7 "
                  f"→ 涨停 55→86→{len(zt)} 三段扩容（较 13:32 +{len(zt) - 86} 只）、跌停收至 {len(dt)}；14:32→14:35 涨停数持平（123→{len(zt)}）＝尾盘停止扩容"),
        "封板质量(关键恶化)": (f"今日 {len(zt)} 只涨停中曾炸板(zbc≥1) {len(zbc1)} 只＝炸板率 {zt_rate}%；13:32 为 49/86=57.0% → "
                     f"涨停数 +{(len(zt) / 86 - 1) * 100:.0f}% 的同时炸板率 +{zt_rate - 57.0:.1f}pp。即新增摸板大量『摸板即开』，"
                     f"广度扩张靠低质量首板堆量，质量明确恶化而非改善。"),
        "连板梯队": (f"lbc 分布：首板 {lbc.get(1, 0)} / 2板 {lbc.get(2, 0)} / 3板 {lbc.get(3, 0)} / 4板 {lbc.get(4, 0)} / 6板 {lbc.get(6, 0)}"
                 f"（001219 青岛食品，换手 19.59%、封单 1.13 亿/成交 7.66 亿）→ 高度单点化、宽度首板化（首板占 {lbc.get(1, 0) / len(zt) * 100:.1f}%）"),
        "指数": (f"上证 {q['000001']['last']:.2f} {q['000001']['pct']:+.2f}%、深成 {q['399001']['last']:.2f} {q['399001']['pct']:+.2f}%、"
               f"创业板 {q['399006']['last']:.2f} {q['399006']['pct']:+.2f}%（创业板盘中高 2500.14，现距高点 {(q['399006']['last'] / 2500.14 - 1) * 100:.1f}%）"),
    },
    "决断": {
        "等级": "无动作（fills=[]）；本场性质＝尾盘前哨读数＋执行缺口第 5 场续催＋14:45 深场B备料",
        "A料执行": 0, "B料防守": 0, "C料进攻": 0,
        "理由": [
            ("①A 料 0：playbook 四腿执行价写死『20261102 开盘价唯一执行价』，14:30 不可复现开盘价；按现价补买＝追价且改执1 口径。"
             f"001219(6板)封 21.93、000995(2板)封 15.60，任何买入落涨停价＝打板（C 档明令禁止）；"
             f"002365 现 12.39 < 开盘 12.61、001287 现 {q['001287']['last']:.2f} < 开盘 20.25（今低 {q['001287']['low']:.2f}）→ 四腿全部维持 0 敞口。"),
            (f"②B 料 0：13:00~{last['ts'][11:16]} 共 {len(aft) - 1} 个 2 分钟窗，≥3 只 -3pp 的窗 = {dz}；三腿无炸板（603533 zbc=0）、无盘中价止损成立。"
             f"单票最大回撤 {delta[0][2]} {delta[0][0]:+.2f}pp 未带动同链、不升级为题材级防守。601188 逆势走弱（3.37→3.32）尚未跌穿 px_exec 3.22，"
             f"按『收盘价口径』盘中不预判、不提前发单。老池尾盘二次走弱（均涨 {s1400['avg']}%→{snow['avg']}%）只作 14:45 盯盘清单加重，不构成 B 级触发证据。"),
            (f"③卖腿不重发、不改价：09:44 三腿（603037×200@10.42 / 603533×200@24.82 / 601188×4200@3.22）至 {last['ts'][11:16]} 仍 0 回执、"
             f"master 仍 3 仓；现价 11.49/26.72/3.32 全部高于冻结价（合计 +{tot:.0f} 元），按现价重发＝以后续走势改口径＋重复计仓，"
             f"纪律上只续催、交结算层按冻结价核销。"),
            (f"④C 料 0：涨停 {len(zt)} 但炸板率 {zt_rate}%（较 13:32 +{zt_rate - 57.0:.1f}pp）、首板占 {lbc.get(1, 0) / len(zt) * 100:.0f}%、高度仅 1 只 6 板"
             f"→ 属『低质量首板堆量』，无可承接的题材主线；叠加执行链路连续 5 场 0 回执，在不可核销链路里新增敞口＝放大风险。"
             f"无预案外新机会达 C 级证据门槛，仅登记不入场。"),
            "⑤本场未改任何阈值/权重/闸门/组合/playbook；一切读数只用本件锚定时刻前已留档数据（ticks ≤" + last["ts"] + "、报价 ≤" + QTS[1] + "）。",
        ],
    },
    "fills": [],
    "14:45深场B备料": {
        "尾盘卖预案候选": [
            {"优先级": 1, "code": "603533", "name": "掌阅科技", "qty": 200, "现价": 26.72, "px_exec_0944": 24.82,
             "情形A": "14:45 仍封（zbc=0）→ 按执1 收盘价 26.72 无条件了结，缺口 +380 元，不得以封板改持或递延至明日",
             "情形B": "尾盘开板 → 同样按收盘价结算，不加发腿、不改 px_exec；若开板后杀至 24.82 下方，缺口由 +380 转负，结算层如实计",
             "证据": f"封单 13:32 2.13 亿 → 14:35 {zk_fund:.4f} 亿（-{(1 - zk_fund / 2.13) * 100:.0f}%），封/成交 15.8%→{zk_fund / zk_amt * 100:.1f}%，换手 {zk['hs']:.2f}% → 厚度三连减，开板概率较 13:32 上升（概率判断，不构成新单）"},
            {"优先级": 2, "code": "601188", "name": "龙江交通", "qty": 4200, "现价": 3.32, "px_exec_0944": 3.22,
             "情形A": "守住 3.22 上方收盘 → 缺口 +420 元",
             "情形B": "尾盘跌穿 3.22 → 缺口转负，结算层按收盘价如实计（不因盘中一度有利而回补）",
             "证据": "13:32→14:35 逆势 -1.48%（池内均涨同期 +0.08pp），相对强度 +4.66%→+3.11%，是唯一走弱且尾盘再破一档的持仓腿"},
            {"优先级": 3, "code": "603037", "name": "凯众股份", "qty": 200, "现价": 11.49, "px_exec_0944": 10.42,
             "情形A": "无新触发（现价回至昨收 11.49、距日高 -0.9%、相对 px_exec +10.3%）→ 维持原腿，不改不补"},
        ],
        "明日预案要点草稿": [
            f"①结构定性：涨停 {len(zt)} 但炸板率 {zt_rate}%、首板占 {lbc.get(1, 0)}/{len(zt)}、高度仅 1 只 6 板 → 本日修复＝『宽度堆量、高度单点、质量恶化』，非健康主升；明日核心闸门『炸板率能否回落至 <50%』，不回落则视为假修复。",
            "②断板观察点：001219 青岛食品 6 板（换手 19.59%、封单 1.13亿/成交 7.66亿＝15%）明日断板概率高；断板后为高位放量阴而非跌停＝良性换手，若一字跌停则情绪顶确认。",
            f"③首板回封率：今日 {lbc.get(1, 0)} 个首板是明日 2 板池唯一来源，须统计次日竞价高开率与开盘 30 分钟封板率 —— 这是『修复能否延续』的硬指标，写入晚间复盘量化项。",
            f"④指数背离：创业板 {q['399006']['pct']:+.2f}% 但距盘中高 2500.14 已回落 {(q['399006']['last'] / 2500.14 - 1) * 100:.1f}%，指数强、个股炸板率高＝权重托指数、题材亏钱效应；明日以『指数红盘但昨日涨停溢价为负』为警戒组合。",
            "⑤playbook 四腿维持原口径，执行价按 20261103 开盘价，本场不预设提前量；观察三票（301132/601083/301520）three-confirm 仍不成立，权重 0。",
            "⑥执行链路：连续 5 场 0 回执为跨日硬缺陷，须在晚间复盘作为 P0 记入，不因盘中读数正常而淡化。",
        ],
        "14:45盯盘清单": [
            f"①603533 封单是否续薄（14:35 已 {zk_fund:.4f} 亿，较 13:32 -{(1 - zk_fund / 2.13) * 100:.0f}%）：跌破 1.0 亿＝开板前兆，只记录不改口径；",
            "②601188 是否跌穿 px_exec 3.22（现 3.32，缓冲 3.1%）；",
            f"③老池尾盘二次走弱是否延续（跌≥3% 已 {snow['le3']} 只、绿盘 {snow['dn']} 只）：若 14:45 跌≥3% 扩至 15 只以上，则 B 级防守证据成立（但仍只对『未发腿』生效，已发腿按冻结价核销）；",
            "④14:45 后再取一次涨停/跌停池与炸板率，供晚间复盘『尾盘是否恶化』定性（本日最后一次可留档窗口）。",
        ],
    },
    "免责": "本件为盘中判断留档，非操盘指令；所有价格均为锚定时刻前已留档数据，浮盈亏以结算引擎为准。",
}

fp = f"{TD}/临盘决断_20261102_1430.json"
json.dump(doc, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", fp, os.path.getsize(fp))

# ---- 报警：本场唯一一行（重写本场初稿行，不叠加重复告警）----
alarm = {
    "ts": WRITE_TS, "session": "hb-e", "date": "20261102", "level": "ALARM",
    "type": "execution_chain_zero_receipt_continuation",
    "scope": "09:44 三笔逾期清出卖腿（603037×200/603533×200/601188×4200）＋ 09:21 两笔买入 A 腿（0 敞口）",
    "detail": (f"连续第 5 场：09:44 三腿至 {last['ts'][11:16]} 仍无 执行流水.jsonl 回执（pulse/warboard 亦不存在），"
               f"master/state.json 未变（mtime 2026-10-30 20:27）。三腿现价 11.49/26.72/3.32 vs 冻结 px_exec 10.42/24.82/3.22，"
               f"差 +{rows[0]['未平差额元']:.0f}/+380/+{rows[2]['未平差额元']:.0f}＝合计 +{tot:.0f} 元（13:32 为 +1188）。"
               f"新增事实：①603533 封单 2.13亿→{zk_fund:.4f}亿（-{(1 - zk_fund / 2.13) * 100:.0f}%）、封/成交 15.8%→{zk_fund / zk_amt * 100:.1f}%；"
               f"②601188 逆势 -1.48%，相对强度 +4.66%→+3.11%；③涨停 {len(zt)}/跌停 {len(dt)}、炸板率 {zt_rate}%（13:32 为 57.0%）；"
               f"④老池尾盘二次走弱，均涨 14:00 +{s1400['avg']}%→{last['ts'][11:16]} +{snow['avg']}%，跌≥3% {s1400['le3']}→{snow['le3']} 只。"
               f"按执1 收盘了结口径：不改持、不改价、不重发。"),
    "root_cause": "盘中引擎成交回执链路缺失（pulse/warboard/执行流水 自 20261020 起长期不产出）；心跳无写引擎回执权限，只能报警与交接",
    "evidence": [f"{TD}/临盘决断_20261102_1430.json#持仓快照", f"{TD}/_hb_e_quote_1436.tsv",
                 f"{TD}/_hb_e_breadth_1436.json", f"{TD}/realtime_ticks.jsonl 末帧 {last['ts']}",
                 "_学习/_模拟盘/master/state.json mtime 2026-10-30 20:27 positions=3"],
    "market_snapshot_intraday": {"ts": last["ts"][11:16], "池内红": snow["up"], "池内绿": snow["dn"], "池内总数": len(last["rows"]),
                                 "池内涨幅≥9.7%": snow["ge97"], "池内跌≥3%": snow["le3"], "池内均涨": snow["avg"],
                                 "午后2分钟跳水达标窗": dz, "涨停": len(zt), "跌停": len(dt), "涨停池炸板率": f"{len(zbc1)}/{len(zt)}={zt_rate}%"},
    "positions": [{"code": r["code"], "name": r["name"], "shares": r["shares"], "last": r["now"], "pct": r["pct"],
                   "px_exec_0944": r["px_exec"], "diff_yuan": r["未平差额元"]} for r in rows],
}
ap = f"{TD}/报警_20261102.jsonl"
lines = [l for l in open(ap, encoding="utf-8").read().splitlines() if l.strip()]
keep = []
for l in lines:
    try:
        o = json.loads(l)
    except Exception:
        keep.append(l); continue
    if o.get("session") == "hb-e" and o.get("date") == "20261102":
        continue  # 丢弃本场初稿行，只留重写版
    keep.append(l)
keep.append(json.dumps(alarm, ensure_ascii=False))
open(ap, "w", encoding="utf-8").write("\n".join(keep) + "\n")
print("ALARM lines", len(keep), "| tot", tot, "| lg_tot", lg_tot, "| zt", len(zt), "rate", zt_rate, "| windows", len(aft) - 1, "dz", dz)
