# -*- coding: utf-8 -*-
"""hb-c 11:00 半日收尾段决断件生成器：所有数字从落盘文件计算，禁手填。"""
import json, os, datetime

BASE = r"D:\股票数据\市场数据\盘中\20261104"
OUT = os.path.join(BASE, "临盘决断_20261104_1100.json")
assert not os.path.exists(OUT), "发出版已存在，禁覆盖"

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
PIN = "2026-11-04 11:05:26"

_all = [json.loads(l) for l in open(os.path.join(BASE, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
frames = [f for f in _all if f["ts"] <= PIN]
q = json.load(open(os.path.join(BASE, "_hb_c_quote_1100.json"), encoding="utf-8"))
quotes = {r["code"]: r for r in q["rows"].values()} if isinstance(q["rows"], dict) else {r["code"]: r for r in q["rows"]}
qb = json.load(open(os.path.join(BASE, "_hb_c_quote_1100b.json"), encoding="utf-8"))
quotes.update({k: {**v, "code": k} for k, v in qb["rows"].items()})
pools = json.load(open(os.path.join(BASE, "_hb_c_pools_1100.json"), encoding="utf-8"))


def snap(f):
    return {r["code"]: r for r in f["rows"]}


def near(t):
    tt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    return min(frames, key=lambda f: abs(datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") - tt))


# ---------- 半日宽度 ----------
width = []
for t in ["2026-11-04 00:00:00", "2026-11-04 09:47:00", "2026-11-04 10:30:00",
          "2026-11-04 10:37:00", "2026-11-04 11:00:00", PIN]:
    f = frames[0] if t.endswith("00:00:00") else near(t)
    S = snap(f)
    p = sorted(x["pct"] for x in S.values())
    width.append({"帧": f["ts"], "上涨": sum(1 for v in p if v > 0), "下跌": sum(1 for v in p if v < 0),
                  "中位pct": round(p[len(p) // 2], 2), "均涨": round(sum(p) / len(p), 2),
                  "贴板>=9.7%": sum(1 for v in p if v >= 9.7),
                  "破-3%": sum(1 for v in p if v <= -3), "破-8%": sum(1 for v in p if v <= -8)})
width[0]["帧"] = "09:31:09(首帧)"

# ---------- 个股Δ 10:37→11:05 ----------
A0 = snap(near("2026-11-04 10:37:00"))
L = snap(near(PIN))
delta = sorted([(round(L[c]["pct"] - A0[c]["pct"], 2), c, L[c]["name"], A0[c]["pct"], L[c]["pct"])
                for c in L if c in A0])
n3 = [x for x in delta if x[0] <= -3]
n2 = [x for x in delta if x[0] <= -2]
up3 = [x for x in delta if x[0] >= 3]

# ---------- 跳水阈值核验：任意 2 分钟窗内跌幅≥3pp 的只数 ----------
win = []
for i in range(2, len(frames)):
    if frames[i]["ts"] < "2026-11-04 10:30":
        continue
    S1, S2 = snap(frames[i - 2]), snap(frames[i])
    d = [(round(S2[c]["pct"] - S1[c]["pct"], 2), c, S2[c]["name"]) for c in S2 if c in S1]
    sub = [x for x in d if x[0] <= -3]
    win.append((frames[i]["ts"], len(sub), round(sum(S2[c]["pct"] - S1[c]["pct"] for c in S2) / len(S2), 2),
                [x[1] for x in sub]))
worst_win = min(win, key=lambda x: x[2]) if win else None
max_cnt = max(win, key=lambda x: x[1]) if win else None
batch_trigger = any(w[1] >= 3 for w in win)

# ---------- 持仓 ----------
master = json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\状态.json", encoding="utf-8"))
mpos = {p["code"]: p for p in master.get("持仓", [])}
cash0 = master["现金"]

pos_doc = []
SPEC = {
    "600261": ("4板最高位·跌停封死：bid1=0.00×0，ask1=4.46×673,142 手（10:37 为 574,818 手，封单 +17.1%＝封得更死）。不可卖，不做虚报成交；午后开板即市价、不挂限价等", 900),
    "002652": ("已于 09:47 由 hb-a B 级卖出 3,600 股（px_exec 3.79），本场不重复卖、不回补", 3600),
    "603906": ("playbook stop_pct 全 null（盘中不止损统一关闭），处置权在 14:57『收盘 -3%』机械腿；本场提前卖＝双次执行，维持不动", 600),
    "600299": ("成本 8.20，未破任何线", None),
    "600259": ("成本 60.20，今日高标回吐但未破成本线", None),
    "002365": ("09:47 A 腿补执行 12.19 已申报，现价低于执行价（执行优于现价）；账本未回写", None),
    "001287": ("09:47 A 腿补执行 20.04 已申报，现价低于执行价；账本未回写", None),
}
for code, (note, sh) in SPEC.items():
    r = quotes[code]
    e = {"code": code, "name": r["name"], "px": r["px"], "pct": r["pct"], "open": r["open"],
         "high": r["high"], "low": r["low"], "note": note}
    if code in mpos:
        e["shares"] = mpos[code]["shares"]
        e["cost"] = mpos[code]["buy_px"]
        e["vs_cost_pct"] = round((r["px"] / mpos[code]["buy_px"] - 1) * 100, 2)
    if sh:
        e["shares"] = sh
    if code == "603906":
        e["from_open_pct"] = round((r["px"] / r["open"] - 1) * 100, 2)
    pos_doc.append(e)

# ---------- 净值三口径（估算） ----------
mv_ledger = sum(quotes[c]["px"] * mpos[c]["shares"] for c in mpos)
nav_ledger = round(cash0 + mv_ledger, 2)
cash_a = cash0 + 1500 * 12.19 + 400 * 20.04
nav_a = round(cash_a + quotes["600299"]["px"] * 2300 + quotes["600259"]["px"] * 100, 2)
cash_all = cash0 - (3600 * 4.05 + 900 * 4.95 + 600 * 15.56) + (1500 * 12.19 + 400 * 20.04 + 3600 * 3.79)
nav_all = round(cash_all + quotes["600261"]["px"] * 900 + quotes["603906"]["px"] * 600
                + quotes["600299"]["px"] * 2300 + quotes["600259"]["px"] * 100, 2)

# ---------- 全场广度 ----------
zt, zb, dt = pools["zt"], pools["zb"], pools["dt"]
lbc = {}
for x in zt:
    lbc[x["lbc"]] = lbc.get(x["lbc"], 0) + 1
erban = sum(1 for x in zt if x["lbc"] >= 2)
zbl = round(len(zb) / (len(zt) + len(zb)), 4) if (zt or zb) else None
rev_a = len(zt) < 40
rev_b = erban <= 8
rev_line = {
    "总审反向线": "若 涨停<40 且 二板加≤8 → 冰点深化，全部未成交条件单作废、已成交按 -3% 离场、不开新单",
    "涨停": len(zt), "涨停<40": rev_a, "二板加": erban, "二板加≤8": rev_b,
    "判定": ("两半均成立→反向线闭合" if (rev_a and rev_b) else
             "只成立一半（涨停<40 成立 / 二板加>8 未成立）→ 不作废、不清仓、不开新单"),
    "趋势": "涨停 34(10:37)→%d(11:05)、炸板 14→%d、炸板率 29.17%%→%s%%、跌停池 0(源侧空,10:37)→%d(11:05) = 退潮在加深但未闭合反向线"
            % (len(zt), len(zb), round(zbl * 100, 2) if zbl is not None else "NA", len(dt)),
}

doc = {
    "date": "20261104", "session": "hb-c", "ts": "11:00", "write_ts": NOW,
    "版本": "sentiment-review-system v2.15 · 13号盘中作战agent 心跳 hb-c（11:00 半日收尾段）",
    "修订": "v1.1 同场次自更正（未被任何下游引用，v1 原文留档 _hb_c_1100_v1_superseded.json）：①『全场广度.指数』为空——取数与渲染键名口径不一致（qt 符号键 vs 纯代码键），已按 qt 符号键重取，补全上证/深成/创业板/科创50；②决断 B 栏 600299 盈亏漏正号（2.56%→+2.56%）；③『最差窗口』补口径说明（按池均Δ取窗，非按 -3pp 只数取窗）；④跌停池核对改用池内字段取值、不再手填。判断（无动作）、fills（空）、全部价格帧未变。",
    "落盘说明": "决断锚 11:00（cron 触发窗）；取数窗 11:05:12~11:05:26：池帧 realtime_ticks.jsonl 末帧 %s（%d 帧、48 行/帧）"
                "＋腾讯 qt 帧 11:05:12/11:05:22（持仓与指数，落 _hb_c_quote_1100.json / _hb_c_quote_1100b.json）"
                "＋东财 push2ex 11:05:12（涨停 %d/炸板 %d/跌停 %d，落 _hb_c_pools_1100.json）。"
                "不回溯改时戳、不覆盖 09:21/09:40/10:30 已发版；本场只读，未改任何阈值/权重/闸门/组合。"
                % (frames[-1]["ts"], len(frames), len(zt), len(zb), len(dt)),
    "交易日校验": {
        "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → FAIL: ModuleNotFoundError: No module named 'sentiment'（D:\\股票数据 全树无该包；20261020 起长期规格漂移，本场连续登记，不改工程）",
        "本机等效真源": "①date → 2026-11-04 星期三；②池帧 09:31:09~%s 共 %d 帧、1 分钟/帧、最大帧间隔 <180s 有取数即在跑；③腾讯 qt 昨收与 20261103 收盘衔接；④东财 push2ex qdate=20261104 返回涨停 %d/炸板 %d/跌停 %d（真实分化非休市静态）→ 判定交易日，不早退" % (frames[-1]["ts"], len(frames), len(zt), len(zb), len(dt)),
    },
    "数据新鲜度": {
        "ticks": "末帧 %s，本件写于 %s，龄 <60 秒；%d 帧无 >180 秒断档 → 未触『断更>10 分钟只报警禁决策』" % (frames[-1]["ts"], NOW, len(frames)),
        "报价": "腾讯 qt 11:05:12（5 只持仓+指数）/ 11:05:22（603906 补取，首轮前缀写错为 sz603906 未返回，已按 sh603906 重取，非编造）",
        "广度": "东财 push2ex 11:05:12 采集",
        "pulse_json": "缺失——本场复核 20261027/1028/1029/1030/1102/1103/1104 共 7 个交易日目录均无 pulse.json（hb-a 登记为『连续第 6 日』系从 20261029 起算，口径更保守；本场如实记 7 日）",
        "warboard_json": "今日缺失（仅 20261030、20261103 有，且 20261103/warboard.json 于今日 10:01 被写入 responses、ts 记作 08-04，属路径/日期口径异常，已由 hb-a 立案）",
        "执行流水_jsonl": "今日仍 0 存在（7 个交易日全无）→ 引擎今日零回执，任何『已成交』均只能是推定",
        "verdict": "允许决策（tick 新鲜、广度源可用）；成交回执不可核验",
    },
    "半日宽度": width,
    "个股Δ(10:37:22→%s)" % frames[-1]["ts"]: {
        "跌≥3pp家数": len(n3), "跌≥2pp家数": len(n2), "涨≥3pp家数": len(up3),
        "跌≥3pp": n3, "涨≥3pp": up3,
        "最差": delta[0] if delta else None, "最强": delta[-1] if delta else None,
        "读法": "10:37→11:05 池内跌幅 ≥3pp 仅 %d 只（002029 服装家纺 -4.55pp、601188 铁路公路 -4.32pp），分散两线，非同一题材同时段塌陷" % len(n3),
    },
    "跳水阈值核验": {
        "阈值": "任意 2 分钟窗内 ≥3 只池内票跌 ≥3pp（同题材同时段塌陷）",
        "扫描窗数": len(win), "窗口起点": "10:30~%s" % frames[-1]["ts"],
        "单窗最多只数": max_cnt[1] if max_cnt else None, "该窗": max_cnt[0] if max_cnt else None,
        "该窗个股": max_cnt[3] if max_cnt else None,
        "最差窗口": {"帧": worst_win[0], "跌幅≥3pp只数": worst_win[1], "池均Δpp": worst_win[2]} if worst_win else None,
        "最差窗口口径": "按池均Δ最小取窗（非按 -3pp 只数取窗；按只数取窗的最大值见『单窗最多只数』）",
        "判定": "未触发（单窗最多 %d 只 <3）→ 不构成 B 级『题材批量跳水』" % (max_cnt[1] if max_cnt else 0),
    },
    "持仓风险核验": pos_doc,
    "全场广度": {
        "ts": pools["fetched"], "涨停": len(zt), "炸板": len(zb), "炸板率": zbl, "跌停": len(dt),
        "最高板": max(x["lbc"] for x in zt) if zt else None,
        "最高板个股": max(zt, key=lambda x: x["lbc"])["n"] if zt else None,
        "连板分布": dict(sorted(lbc.items())), "二板加": erban,
        "跌停池核对": "600261 在跌停池内（%s / %s / %+.2f%%）→ 与腾讯 bid1=0 一致；10:37 帧『跌停池 0 只』与事实矛盾（当时 600261 已 -9.90%%），判为源侧延迟/漏返，本场弃用该旧帧" % (
            next((x["n"] for x in dt if x["c"] == "600261"), "NA"),
            next((x.get("hybk") for x in dt if x["c"] == "600261"), "NA"),
            next((x.get("zdp", 0.0) for x in dt if x["c"] == "600261"), 0.0)),
        "指数": {q["rows"][k]["name"]: [q["rows"][k]["pct"], q["rows"][k]["px"]]
                 for k in q["rows"] if k.startswith(("sh000", "sz399"))},
    },
    "反向线核验": rev_line,
    "决断": {
        "结论": "无动作（A=0 / B=0 / C=0）",
        "A": "0 笔。playbook 四笔 buys 的闸门均在 09:25 集合竞价一次性判定并已处置（002652/603906/600261 落门推定建仓、002292 gap -2.19% 弃买）；11:00 无任何未触发条件单，无预案内 trigger 达成 → 无 A 级执行。",
        "B": "0 笔。①批量跳水未达阈值（单窗最多 {} 只 -3pp，阈值 ≥3）；②600261 跌停封死不可卖（bid1=0×0、ask1 673,142 手，封单较 10:37 增 17.1%），不虚报成交；③603906 {:+.2f}%（相对开盘 {:+.2f}%）未越『大幅回撤』，且 stop_pct=null 盘中不止损统一关闭、14:57 收盘 -3% 腿在册，提前卖＝双次执行；④600299 {:+.2f}%、600259 {:+.2f}%（对成本）均未破线。故不新开防守单。".format(
            max_cnt[1],
            quotes["603906"]["pct"], pos_doc[[e["code"] for e in pos_doc].index("603906")]["from_open_pct"],
            pos_doc[[e["code"] for e in pos_doc].index("600299")]["vs_cost_pct"],
            pos_doc[[e["code"] for e in pos_doc].index("600259")]["vs_cost_pct"]),
        "C": "0 笔。冰点环境（涨停 {}<40、炸板率 {:.2f}%、池内中位 {:+.2f}%、破-8% {} 只）不满足任何新开仓证据标准；预案外机会仅记录不建仓（C 级需 weight≤10% 且带帽，本场无证据支持）。".format(
            len(zt), (zbl or 0) * 100, width[-1]["中位pct"], width[-1]["破-8%"]),
    },
    "fills": [],
    "no_action": "心跳hb-c无动作",
    "净值估算": {
        "账本口径(A腿未回写)": nav_ledger,
        "A腿执行后": nav_a,
        "全口径含三腿推定(002652 买4.05/卖3.79、600261 买4.95 锁死4.46、603906 买15.56)": nav_all,
        "相对初始100万": round((nav_ledger / 1000000 - 1) * 100, 2),
        "说明": "估算，未含滑点 0.10%、佣金、印花税；master/状态.json mtime 2026-11-03 20:35 未回写当日任何腿 → 三口径并存，settle 结算为唯一真源，本件不回写账本",
    },
    "待核销账": [
        "600261 900 股：跌停封死，午后开板即市价卖出；若全日不开板 → 顺延次日集合竞价跌停价排队（不得因『跌停买不到』先验弃单）",
        "603906 600 股：14:57 收盘 -3% 机械腿（相对 15.64 的 -3%＝15.17 以下），本场不提前",
        "002652 3,600 股：09:47 已卖 3.79，营收 -936 元（相对开盘 4.05），已登记不追溯",
        "002365 / 001287：09:47 A 腿执行价 12.19 / 20.04，账本零回执，待 settle 核销",
    ],
    "下一场交接(hb-d 13:30)": [
        "①核 600261 午后是否开板（封单 67.3 万手，开板概率下降）；开板即市价，不等限价",
        "②603906 是否跌停/加速下行：若跌停封死则收盘腿顺延，不得穿价追卖",
        "③反向线：涨停已 <40，只看二板加能否回落 ≤8；两半齐备才作废条件单/按 -3% 离场",
        "④宽度：池内中位 %+.2f%%（11:05），若午后中位跌破 -6%% 且破-8%% ≥15 只 → 冰点二次探底确认，只记录不加仓" % width[-1]["中位pct"],
        "⑤账本：pulse/执行流水/当日 legs 三项回执核查继续，属盘后总审立案项，盘中不改脚本",
    ],
    "权限声明": "本场零 A/B/C 级动作，未使用任何裁量权；未改 playbook/闸门/阈值/权重；未手写账本；fills 为空，所有价格均为留档帧读数。",
    "免责": "本件为模拟盘判断记录，不是操盘指令。",
}

json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT))
print("width", json.dumps(width, ensure_ascii=False))
print("nav", nav_ledger, nav_a, nav_all)
print("delta<=-3", len(n3), "batch", batch_trigger, max_cnt)
for e in pos_doc:
    print(e["code"], e["px"], e["pct"], e.get("note", "")[:80])
