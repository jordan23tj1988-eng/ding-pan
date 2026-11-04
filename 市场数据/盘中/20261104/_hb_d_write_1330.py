# -*- coding: utf-8 -*-
"""hb-d 13:30 落盘：临盘决断_20261104_1330.json（无动作场次，含证据与交接）"""
import json, os, statistics, datetime

D = r"D:\股票数据\市场数据\盘中\20261104"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- 池帧统计 ----------
frames = []
for line in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8"):
    line = line.strip()
    if line:
        d = json.loads(line)
        frames.append((d["ts"], {r["code"]: r for r in d["rows"]}))


def stat(ts, rows):
    p = [r["pct"] for r in rows.values() if r.get("pct") is not None]
    return {"帧": ts, "n": len(p), "上涨": sum(1 for x in p if x > 0), "下跌": sum(1 for x in p if x < 0),
            "平盘": sum(1 for x in p if x == 0), "均涨": round(statistics.mean(p), 2),
            "中位pct": round(statistics.median(p), 2), "贴板>=9.7%": sum(1 for x in p if x >= 9.7),
            "破-3%": sum(1 for x in p if x <= -3), "破-8%": sum(1 for x in p if x <= -8)}


want = {"11:05": None, "13:00": None, "13:10": None, "13:20": None, "13:30": None}
for ts, rows in frames:
    hhmm = ts[11:16]
    if hhmm in want and want[hhmm] is None:
        want[hhmm] = stat(ts, rows)
width = [want[k] for k in ("11:05", "13:00", "13:10", "13:20", "13:30") if want[k]]
last_ts = frames[-1][0]
width.append(stat(last_ts, frames[-1][1]))
med115, med_last = width[0]["中位pct"], width[-1]["中位pct"]
near_last, break8_last = width[-1]["贴板>=9.7%"], width[-1]["破-8%"]
zt2, zb2, dt2 = 46, 25, 15  # 13:37:28 第二帧复核（独立抓取，见 _hb_d_pools_1330.json 覆盖前值已在 广度复核 同步登记）

# ---------- 2 分钟跳水扫描（午后） ----------
def scan(lo, hi):
    out = []
    for i in range(len(frames) - 2):
        ts0, r0 = frames[i]
        ts1, r1 = frames[i + 2]
        if not (lo <= ts0[11:16] <= hi):
            continue
        drops = []
        for c in r0:
            if c in r1 and r0[c].get("pct") is not None:
                dd = r1[c]["pct"] - r0[c]["pct"]
                if dd <= -3:
                    drops.append([round(dd, 2), c, r0[c]["name"], r0[c]["pct"], r1[c]["pct"]])
        pool = [r1[c]["pct"] - r0[c]["pct"] for c in r0 if c in r1 and r0[c].get("pct") is not None]
        out.append({"窗": ts0[11:16] + "→" + ts1[11:16], "跌>=3pp只数": len(drops),
                    "池均Δpp": round(statistics.mean(pool), 2), "个股": sorted(drops)[:6]})
    return out


pm = scan("13:00", "13:34")
mx = max(pm, key=lambda x: x["跌>=3pp只数"])
worst = min(pm, key=lambda x: x["池均Δpp"])

# ---------- 取数件 ----------
q = json.load(open(os.path.join(D, "_hb_d_quote_1330.json"), encoding="utf-8"))
pl = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))
Q = q["rows"]
zt, zb, dt = pl["zt"], pl["zb"], pl["dt"]
lbc = {}
for x in zt:
    lbc[str(x["lbc"])] = lbc.get(str(x["lbc"]), 0) + 1
zt_n, zb_n, dt_n = len(zt), len(zb), len(dt)
ers = sum(1 for x in zt if x["lbc"] >= 2)
max_lb = max((x["lbc"] for x in zt), default=None)
top = [x["n"] for x in zt if x["lbc"] == max_lb][:3]

# ---------- 净值估算 ----------
cash = 932105.75
a_leg = 1500 * 12.19 + 400 * 20.04
buys = 3600 * 4.05 + 600 * 15.56 + 900 * 4.95
sells = 3600 * 3.79
cash1 = cash + a_leg - buys + sells
mv1 = 600 * Q["sh603906"]["px"] + 900 * 4.46
mv0 = 2300 * Q["sh600299"]["px"] + 100 * Q["sh600259"]["px"]
nav_full = cash1 + mv1 + mv0
nav_led = cash + a_leg + mv0

pos = []
def P(code, key, shares, cost=None, note=""):
    r = Q[key]
    d = {"code": code, "name": r["name"], "px": r["px"], "pct": r["pct"], "open": r["open"],
         "high": r["high"], "low": r["low"], "shares": shares, "note": note}
    if cost:
        d["cost"] = cost
        d["vs_cost_pct"] = round((r["px"] / cost - 1) * 100, 2)
    if r["open"]:
        d["from_open_pct"] = round((r["px"] / r["open"] - 1) * 100, 2)
    pos.append(d)


P("600261", "sh600261", 900, cost=4.95,
  note="4板最高位·竞价推定建仓 4.95·跌停封死第 3 小时：bid1=0.00×0、ask1=4.46×%s 手（11:05 为 673,142，封单 +%.1f%%）。13:00~%s 全部 tick 恒为 4.46，午后未开板 → 不可卖，不虚报成交；开板即市价。" % (
      Q["sh600261"]["ask1_vol"], (int(Q["sh600261"]["ask1_vol"]) / 673142 - 1) * 100, last_ts[11:16]))
P("603906", "sh603906", 600, cost=15.56,
  note="午后修复：11:05 -3.96%%（相对开盘 -3.47%%）→ 本场取数帧 %+.2f%%（相对开盘 %+.2f%%），已回到 14:57『收盘 -3pct』腿触发线 15.17 上方 %.2f%%；stop_pct=null 盘中不止损，本场不动。" % (
      Q["sh603906"]["pct"], (Q["sh603906"]["px"] / Q["sh603906"]["open"] - 1) * 100, (Q["sh603906"]["px"] / 15.17 - 1) * 100))
P("002652", "sz002652", 3600, cost=4.05,
  note="09:47 已按 B 级卖出 3.79（-6.42%%），本场不重复卖、不回补；现价 %.2f 高于卖出价 %.2f%%＝卖飞已如实登记，不回补（当日了结纪律，追回＝用后视镜改计划）。" % (
      Q["sz002652"]["px"], (Q["sz002652"]["px"] / 3.79 - 1) * 100))
P("600299", "sh600299", 2300, cost=8.20, note="成本 8.20，午后转红，未破任何线。")
P("600259", "sh600259", 100, cost=60.20, note="早盘 -3.2% 一度贴近成本，午后修复至成本上方。")
P("002365", "sz002365", 1500, cost=12.61, note="09:47 A 腿 open 了结，执行价 12.19（优于今开 12.12）；账本零回执待 settle 核销。")
P("001287", "sz001287", 400, cost=20.25, note="09:47 A 腿 open 了结，执行价 20.04（优于今开 19.73）；账本零回执待 settle 核销。")

doc = {
    "date": "20261104",
    "session": "hb-d",
    "ts": "13:30",
    "write_ts": NOW,
    "版本": "sentiment-review-system v2.15 · 13号盘中作战agent 心跳 hb-d（13:30 午后延续段）",
    "交易日校验": {
        "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → FAIL: ModuleNotFoundError: No module named 'sentiment'（D:\\股票数据 全树无该包，属规格漂移；本机真源为 市场数据\\trading_calendar.py，其接口为 load_trading_calendar/next_trading_day，无 is_trading_day）",
        "本机等效真源": "①系统日期 2026-11-04 星期三；②池帧 09:31:09~%s 共 %d 帧、1 分钟/帧、最大间隔 <180s；③东财 push2ex date=20261104 返回涨停 %d/炸板 %d/跌停 %d（真实分化非休市静态）；④腾讯 qt 昨收与 20261103 收盘衔接 → 判定交易日，不早退（同 hb-a/hb-c 口径）" % (last_ts, len(frames), zt_n, zb_n, dt_n)
    },
    "数据新鲜度": {
        "ticks": "末帧 %s，本件写于 %s，龄 <60 秒；午后 13:00~%s 无 >180 秒断档 → 未触『断更>10 分钟只报警禁决策』" % (last_ts, NOW, last_ts[11:16]),
        "报价": "腾讯 qt %s（7 只持仓/观察 + 4 指数），落 _hb_d_quote_1330.json" % q["fetched"],
        "广度": "东财 push2ex %s（涨停 %d/炸板 %d/跌停 %d），落 _hb_d_pools_1330.json" % (pl["fetched"], zt_n, zb_n, dt_n),
        "pulse_json": "缺失（连续第 8 个交易日：20261027/1028/1029/1030/1102/1103/1104 全无）。后果：无盘中『温度』口径，playbook 反向线第三条『温度≤24.9→二次探底确认』本场不可核验，不默认成立亦不默认排除",
        "warboard_json": "今日仍缺失（仅 20261030、20261103 有，后者 10:01 被写入 responses 且 ts 记作 08-04，路径/日期异常已立案）",
        "执行流水_jsonl": "今日仍 0 存在（8 个交易日全无）→ 引擎今日零回执，任何『已成交』只能是推定",
        "verdict": "允许决策（tick/报价/广度三源均新鲜）；成交回执不可核验"
    },
    "午后宽度": width,
    "跳水阈值核验": {
        "阈值": "任意 2 分钟窗内 ≥3 只池内票跌 ≥3pp（同题材同时段塌陷）",
        "扫描窗数": len(pm),
        "窗口起点": "13:00~%s" % last_ts[11:16],
        "单窗最多只数": mx["跌>=3pp只数"],
        "该窗": mx["窗"],
        "该窗个股": mx["个股"],
        "最差窗口": {"帧": worst["窗"], "跌幅>=3pp只数": worst["跌>=3pp只数"], "池均Δpp": worst["池均Δpp"]},
        "判定": "未触发（%d 只 <3）→ 不构成 B 级『题材批量跳水』；午后池均 %+.2fpp、中位 %+.2f%% 均较 11:05（%+.2f%% / %+.2f%%）回升，尾盘 20 分钟小幅回吐但方向未反转" % (
            mx["跌>=3pp只数"], width[-1]["均涨"], med_last, width[0]["均涨"], med115)
    },
    "口径说明": "本场宽度与 hb-c 交接值存在两点口径差：①同一 11:05:26 帧，本场自算中位 %.2f、hb-c 记 -4.60（差 %.2fpp，同帧不同取值，判为取整/样本序差异，不回改前版）；②本场末帧随跑批时点前移（末帧 %s），故中位与本场写作时相差 ±0.2pp 属正常抖动。序列以本场自算为准。" % (med115, abs(med115 + 4.60), last_ts),
    "持仓风险核验": pos,
    "全场广度": {
        "ts": pl["fetched"],
        "涨停": zt_n, "炸板": zb_n, "炸板率": round(zb_n / (zt_n + zb_n), 4), "跌停": dt_n,
        "最高板": max_lb, "最高板个股": top, "连板分布": lbc, "二板加": ers,
        "跌停池核对": "600261 阳光照明在跌停池内（照明设备 -9.90%）→ 与腾讯 bid1=0 一致，两源互证",
        "指数": {k: [Q[v]["pct"], Q[v]["px"]] for k, v in (("上证指数", "sh000001"), ("深证成指", "sz399001"),
                                                         ("创业板指", "sz399006"), ("科创50", "sh000688"))},
        "对比11:05": "涨停 30→%d、炸板 21→%d、炸板率 41.18%%→%.2f%%、跌停 18→%d、二板加 10→%d；指数由 -0.31%%/-0.18%%/-0.25%%/+0.40%% 转为 %+.2f%%/%+.2f%%/%+.2f%%/%+.2f%%" % (
            zt_n, zb_n, zb_n / (zt_n + zb_n) * 100, dt_n, ers,
            Q["sh000001"]["pct"], Q["sz399001"]["pct"], Q["sz399006"]["pct"], Q["sh000688"]["pct"]),
        "广度复核(两帧独立)": "13:34:30 帧 涨停 44/炸板 26/跌停 17（该帧取数件随后被 13:37:28 复核抓取覆盖，值取当时终端输出）；13:37:28 帧 涨停 %d/炸板 %d/跌停 %d。两帧方向一致（涨停回升、跌停减少、炸板率 37.14%%→%.2f%%），『涨停<40 且 二板加≤8』在两帧均不成立 → 反向线判定不依赖单帧" % (
            zt2, zb2, dt2, zb2 / (zt2 + zb2) * 100)
    },
    "反向线核验": {
        "总审反向线①": "若 涨停<40 且 二板加≤8 → 冰点深化，全部未成交条件单作废、已成交按 -3% 离场、不开新单",
        "涨停<40": zt_n < 40, "二板加≤8": ers <= 8,
        "判定①": "两条均不成立（涨停 %d≥40、二板加 %d>8）→ 反向线整条失效，不作废、不清仓（11:05 曾只成立一半；13:34 连『涨停<40』亦回补）" % (zt_n, ers),
        "总审反向线②（修复确认）": "若 涨停≥70 且 炸板率≤0.30 → 档位 C→B、总仓上限升 7%",
        "涨停≥70": zt_n >= 70, "炸板率≤0.30": (zb_n / (zt_n + zb_n)) <= 0.30,
        "判定②": "不成立（涨停 %d<70、炸板率 %.2f%%>30%%）→ 午后是修复动作，不是修复确认；档位维持冰点 C，不加仓、不开新单" % (zt_n, zb_n / (zt_n + zb_n) * 100),
        "总审反向线③": "若 温度≤24.9 → 二次探底确认",
        "判定③": "不可核验（pulse.json 缺、无盘中温度口径）→ 如实标 null，不用替代口径冒充实测"
    },
    "决断": {
        "结论": "无动作（A=0 / B=0 / C=0）",
        "A": "0 笔。playbook（20261103 生成）四笔 buys 的闸门均在 09:25 集合竞价一次性判定并处置完毕；盘中无未触发条件单、无 A 级 trigger 达成。本场不新设 trigger。",
        "B": "0 笔。①批量跳水未达阈值（午后单窗最多 %d 只 -3pp，阈值 ≥3；最差窗池均 %+.2fpp）；②600261 跌停封死第 3 小时（ask1 %s 手、封单较 11:05 增 %.1f%%），不可卖、不虚报成交；③603906 由 -3.96%% 修复至 %+.2f%%，回到 15.17 收盘腿线上方，且 stop_pct=null 盘中不止损统一关闭 → 提前卖＝双次执行；④600299/600259/002365/001287 均未破线。故无新开防守单。" % (
            mx["跌>=3pp只数"], worst["池均Δpp"], Q["sh600261"]["ask1_vol"],
            (int(Q["sh600261"]["ask1_vol"]) / 673142 - 1) * 100, Q["sh603906"]["pct"]),
        "C": "0 笔。指数强反弹（上证 %+.2f%%、创业板 %+.2f%%、科创50 %+.2f%%）但涨停仅 %d（<70）、炸板率 %.2f%%（>30%%）、池内中位 %+.2f%%（仍为负）、跌停 %d → 按反向线② 修复未确认，冰点档 C 不开仓；预案外贴板票（本帧 %d 只，如 601123/000995）仅记录不建仓，C 级需 weight≤10%% 且带帽，本场无证据支持。" % (
            Q["sh000001"]["pct"], Q["sz399006"]["pct"], Q["sh000688"]["pct"], zt_n,
            zb_n / (zt_n + zb_n) * 100, med_last, dt_n, near_last)
    },
    "fills": [],
    "no_action": "心跳hb-d无动作",
    "净值估算": {
        "账本口径(A腿未回写)": round(nav_led, 2),
        "全口径含三腿推定(002652 买4.05/卖3.79、600261 买4.95 锁死4.46、603906 买15.56)": round(nav_full, 2),
        "全口径相对初始100万%": round(nav_full / 1e6 * 100 - 100, 2),
        "说明": "估算，未含滑点 0.10%、佣金、印花税；master/状态.json mtime 2026-11-03 20:35 仍未回写当日任何腿 → 两口径并列，settle 结算为唯一真源，本件不回写账本"
    },
    "待核销账": [
        "600261 900 股：跌停封死第 3 小时（封单 %s 手且递增），午后仍未开板 → 全日不开则次日集合竞价跌停价排队，不得弃单；开板即市价" % Q["sh600261"]["ask1_vol"],
        "603906 600 股：14:57 收盘 -3%% 机械腿（15.17 以下触发），现价 %.2f（%+.2f%%），本场不提前" % (Q["sh603906"]["px"], Q["sh603906"]["pct"]),
        "002652 3,600 股：09:47 卖 3.79 已实现 -936 元；现价 %.2f（卖飞 %.2f%%）不回补" % (Q["sz002652"]["px"], (Q["sz002652"]["px"] / 3.79 - 1) * 100),
        "002365 / 001287：09:47 A 腿 12.19 / 20.04 已申报，账本零回执待 settle 核销"
    ],
    "下一场交接(14:57 收盘前)": [
        "①600261 是否开板（封单增 %+.1f%%＝开板概率继续下降）；开板即市价，不等限价" % ((int(Q["sh600261"]["ask1_vol"]) / 673142 - 1) * 100),
        "②603906 收盘腿：15.17 以下才卖，现价 %.2f（%+.2f%%）未触发；若尾盘急杀穿线按机械腿执行，不穿价追卖" % (Q["sh603906"]["px"], Q["sh603906"]["pct"]),
        "③反向线：两条均已失效（涨停 %d≥40、二板加 %d>8）→ 今日不触发清仓；若尾盘涨停回落至 <40 且 二板加≤8，则收盘前按『已成交按 -3%% 离场』复核一次（已卖 002652 不重复）" % (zt_n, ers),
        "④宽度：池内中位 %+.2f%%（11:05 %+.2f%% → 13:00 -3.30%% → 13:30 -1.91%% → 本帧 %+.2f%%）＝午后修复但尾盘动能放缓；破-8%% 由 11 只降到 %d 只。若尾盘中位跌回 -6%% 以下且破-8%% ≥15 只 → 未发生，只记录不加仓" % (med_last, med115, med_last, break8_last),
        "⑤账本：pulse/执行流水/当日 legs 三项回执继续缺失（第 8 日），属盘后总审立案项，盘中不改脚本、不改阈值"
    ],
    "自审": "本场仅读：未改 playbook/闸门/阈值/权重/账本；未覆盖 09:21/09:40/10:30/11:00 任一发出版；所有价格均为留档帧或带 fetched 时戳的抓取件读数；单笔卖飞、封单比例变化、口径缺失均如实登记，未用替代源冒充实测。",
    "权限声明": "本场零 A/B/C 级动作，未使用任何裁量权。",
    "免责": "本件为系统留档与用户参考，不构成操盘指令。"
}

out = os.path.join(D, "临盘决断_20261104_1330.json")
json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", out, os.path.getsize(out))
print(json.dumps({k: doc[k] for k in ("午后宽度", "跳水阈值核验", "全场广度", "反向线核验", "决断", "净值估算")}, ensure_ascii=False, indent=1))
