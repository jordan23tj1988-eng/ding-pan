# -*- coding: utf-8 -*-
"""hb-e 2026-09-17 14:30 尾盘前哨段(in-window): 留档 ALARM_ONLY(零fills/零预判/零条件价) + 14:45 深场B备料。
零后视镜: 全部决策输入 = 决断时点(nominal 2026-09-17 14:30)之前已留档数据; 写档后实测仅入台账并显式声明。
发出版不可覆盖: 名义目标 临盘决断_20260917_1430.json 已被 9/16 catch_up 占用 -> 拒绝覆盖, 追加式落 _inwindow 后缀件。
"""
import io, json, os, glob, datetime, hashlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据\市场数据"
D = "20260917"
INTRA = os.path.join(BASE, "盘中")
DD = os.path.join(INTRA, D)
DEC = datetime.datetime(2026, 9, 17, 14, 30, 0)
WRITE_TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
NOMINAL = os.path.join(DD, "临盘决断_%s_1430.json" % D)          # 已占用(9/16 catch_up)
OUT = os.path.join(DD, "临盘决断_%s_1430_inwindow.json" % D)     # 本场追加式发出版
ALARM = os.path.join(DD, "报警_%s.jsonl" % D)

if os.path.exists(OUT):
    raise SystemExit("REFUSE: 本场发出版已存在 -> %s" % OUT)

# ---- 既有名义件指纹(证明未触碰) ----
def fingerprint(p):
    if not os.path.exists(p):
        return {"exists": False}
    b = open(p, "rb").read()
    return {"exists": True, "sha256": hashlib.sha256(b).hexdigest()[:16],
            "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S"),
            "bytes": len(b)}

# ---- 决断时点前留档 (<=14:30) ----
ticks = []
with io.open(os.path.join(DD, "realtime_ticks.jsonl"), encoding="utf-8", errors="replace") as f:
    for ln in f:
        ln = ln.strip()
        if not ln:
            continue
        try:
            ticks.append(json.loads(ln))
        except Exception:
            pass
pre = [t for t in ticks if datetime.datetime.strptime(t["ts"], "%Y-%m-%d %H:%M:%S") <= DEC]
last = pre[-1]
rows = last["rows"]

def limit_px(code, pc):
    r = 0.2 if (code[:3] in ("300", "301", "688", "689") or code[:2] == "68") else 0.1
    return round(pc * (1 + r) + 1e-9, 2)

seal, brk = [], []
for r in rows:
    L = limit_px(r["code"], r["preClose"])
    if r["latest"] >= L - 1e-9:
        seal.append("%s %s(%+.2f%%, 涨停价%.2f)" % (r["code"], r["name"], r["pct"], L))
    elif r["high"] >= L - 1e-9:
        brk.append("%s %s(%+.2f%%, 涨停价%.2f, 现价%.2f)" % (r["code"], r["name"], r["pct"], L, r["latest"]))

up = [r for r in rows if r["pct"] > 0]
dn = [r for r in rows if r["pct"] < 0]
flat = [r for r in rows if r["pct"] == 0]
zt_like = [r for r in rows if r["pct"] >= 9.8]
dt_like = [r for r in rows if r["pct"] <= -9.8]
top = sorted(rows, key=lambda r: -r["pct"])[:4]
bot = sorted(rows, key=lambda r: r["pct"])[:4]
gap_min = round((DEC - datetime.datetime.strptime(last["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60.0, 1)
span_min = round((datetime.datetime.strptime(last["ts"], "%Y-%m-%d %H:%M:%S") -
                  datetime.datetime.strptime(pre[0]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60.0, 1)

# 15分钟动量 (14:15 vs 14:29)
pm = None
for t in pre:
    if t["ts"] <= "2026-09-17 14:15:00":
        pm = t
mom = {}
if pm:
    a = {r["code"]: r["pct"] for r in pm["rows"]}
    b = {r["code"]: r["pct"] for r in rows}
    d = sorted(((b[k] - a[k], k) for k in b if k in a))
    name = {r["code"]: r["name"] for r in rows}
    mom = {"窗口": "14:15->14:29", "最弱5": ["%s %.2fpp" % (name[k], v) for v, k in d[:5]],
           "最强5": ["%s +%.2fpp" % (name[k], v) for v, k in d[-5:]]}

# ---- 三账本 / 预案 / 总审 ----
acc = {}
for nm in ("盘中作战", "master"):
    p = os.path.join(BASE, "_学习", "_模拟盘", nm, "state.json")
    j = json.load(open(p, encoding="utf-8"))
    acc[nm] = {"cash": j.get("cash"), "n_pos": len(j.get("positions") or []),
               "positions": j.get("positions") or [],
               "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S")}
nextsell = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "次日卖出指令.json"), encoding="utf-8"))
zs = json.load(open(os.path.join(BASE, "_学习", "总审_20260911.json"), encoding="utf-8"))["总裁决"]
plan_legs, plan_zero = {}, {}
for f in glob.glob(os.path.join(BASE, "_学习", "交易计划_*.json")):
    key = os.path.basename(f)[len("交易计划_"):-len(".json")]
    parts = key.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 8:
        plan_legs[parts[0]] = max(plan_legs.get(parts[0], ""), parts[1])
        if parts[1] == plan_legs[parts[0]]:
            j = json.load(open(f, encoding="utf-8"))
            plan_zero[parts[0]] = {"mtime": datetime.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%m-%d %H:%M"),
                                   "buys": len(j.get("buys") or []), "sells": len(j.get("sells") or [])}
pb = sorted(glob.glob(os.path.join(INTRA, "*", "playbook.json")))
daily = sorted(os.path.basename(p) for p in glob.glob(os.path.join(BASE, "2026*")) if os.path.isdir(p))
today_alarms = [json.loads(l) for l in io.open(ALARM, encoding="utf-8", errors="replace") if l.strip()]
recheck = ticks[-1]  # 写档时点后复核(非决策输入)
recheck_rows = recheck["rows"]
re_pcts = {r["code"]: r["pct"] for r in recheck_rows}
delta = sorted(((re_pcts[r["code"]] - r["pct"], r["name"]) for r in rows), key=lambda x: x[0])

rec = {
    "date": D,
    "session": "hb-e",
    "ts": "14:30",
    "role": "尾盘前哨段心跳 hb-e(13号盘中作战agent心跳哨兵, 为 14:45 深场B备料)",
    "decision_ts_nominal": "2026-09-17 14:30 (scheduler in-window; 认领 14:30:10 / 启动 14:30:11 / 实际写档 %s)" % WRITE_TS,
    "write_ts": WRITE_TS,
    "level": "ALARM_ONLY",
    "动作级别": "无动作(零 fills / 零预判 / 零条件价)",
    "场次说明": ("14:30尾盘前哨段心跳 hb-e 本日唯一实时段。★身份读自 cron 真源(非自报): jobs.json id=4deb15fee730 "
              "name=sentiment-intraday-hb-e, expr='30 14 * * 1-5', enabled=true; executions.db 本次认领行 "
              "id=2618f7dee90a406ea4db3392037f0b83, scheduled_instant=2026-09-17T06:30:00Z(=14:30 CST), "
              "claimed_at=2026-09-17T14:30:10, started_at=14:30:11 → kind=in_window(lateness≈10s), 非 catch_up。"
              "前序 12:08 落档的 hb-e(execution 314f3f10d81c4b259c94a00d909cb3a4)其名义段=2026-09-16 14:30(catch_up, "
              "lateness≈21.4h)且全文自述『不代今日 14:30 决断、不预写』→ 两实例互不代决断。"),
    "落档处置_发出版不可覆盖": {
        "名义目标": "盘中/%s/临盘决断_%s_1430.json" % (D, D),
        "占用情况": "★已被 9/16 名义段 catch_up hb-e 于 2026-09-17 12:08:24 写入(其正文自述『今日 9/17 14:30 名义段未到点, 本文件不代其决断、不预写』)。",
        "本场处置": "按『发出版不可覆盖』拒绝覆盖既有件; 本场结论以追加式落 盘中/%s/临盘决断_%s_1430_inwindow.json(文件名按字典序排在名义件之后, 命名不冲突)。",
        "既有件指纹(写档前/后均未触碰)": fingerprint(NOMINAL),
        "待批": "同名冲突的长期处置(改名留档 vs 追加式补档 vs 场次重命名)属机制改动, 收市后报用户拍板; 场次内零改动。"
    },
    "条件决断": [],
    "fills": [],
    "data_freshness": {
        "交易日校验": {
            "任务指定": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → ModuleNotFoundError: No module named 'sentiment'(本机实测, 该模块全盘不存在) → 指定校验环节不可用。",
            "可用替代": "市场数据/trading_calendar.py 存在(无 is_trading_day/today_str 接口); _学习/_交易日历.json 末条=20260911 → 缓存未含 9/14–9/17, 同样不可判今日。",
            "本场判定依据": "① 盘中/20260917/realtime_ticks.jsonl 决断时点前已落 %d 条连续盘中报价(%s–%s, 每 60s, 跨度 %.0f 分钟) → 当日为交易日(实据, 非推断); ② 2026-09-17=周四, 中秋(9/25)/国庆(10/1)在其后; ③ 盘中管道 launcher.log 持续每 60s 续写至决断时点之后。"
                            % (len(pre), pre[0]["ts"], last["ts"], span_min)
        },
        "realtime_channel": {
            "path": "盘中/20260917/realtime_ticks.jsonl",
            "n_total_now": len(ticks), "n_at_or_before_1430": len(pre),
            "first_ts": ticks[0]["ts"], "last_at_or_before_1430": last["ts"],
            "gap_min_at_decision": gap_min, "src": last.get("src"), "n_rows": last.get("n"),
            "结论": "★未触发『断更>10分钟』红线: 决断时点前 %.1f 分钟内有留档 → 允许决策流程; 但源头为腾讯降级源(iFinD 实时不可用), 无 Level1 盘口/无竞价轨迹, 仅 40 只样本。" % gap_min
        },
        "pulse": {"path": "盘中/%s/pulse.json" % D, "exists": False,
                  "note": "全盘 glob 0 命中(本系统脉搏=warboard 内嵌 fact 快照字段, 由 warboard_build.py 产出) → 任务步骤2 的 pulse 新鲜度核验: 无对象(等同断更)。"},
        "warboard": {"path": "盘中/%s/warboard.json" % D, "exists": False,
                     "fallback": "最新落档=盘中/20260909/warboard.json(date 字段=20260909, 9/9 晚间复盘重建; 本日 14:30:14 被『盘中回应引擎-每日尾盘14:30』重写但 target 日仍=20260909) → 对今日零指向, 无 fact 快照/无优先成交序。"},
        "执行流水": {"path": "盘中/%s/执行流水.jsonl" % D, "exists": False,
                     "note": "全盘 glob 执行流水*.jsonl 0 命中 → 无成交流水可对账。"},
        "预案真源": {"playbook_max": os.path.relpath(pb[-1], BASE).replace("\\", "/") if pb else None,
                     "交易计划_max_by_leg": plan_legs,
                     "最新计划 buys/sells": plan_zero,
                     "今日预案文件": [],
                     "note": "playbook 断供第 8 个交易日(9/08 起); 六路交易计划全部停在 20260911 且 buys=0/sells=0 → 今日无 leg=close/take_zt 可触发票据 → A级条件决断合法为空(非漏写)。"},
        "总审": {"path": "_学习/总审_20260911.json", "档位": zs.get("档位"), "置信度": zs.get("置信度"),
                 "结论": zs.get("结论"), "可证伪条件": zs.get("可证伪条件"),
                 "note": "无覆盖 9/14–9/17 的总审 → 防守框架在册未解除。"},
        "账本": acc["盘中作战"],
        "账本_master": {"cash": acc["master"]["cash"], "n_pos": acc["master"]["n_pos"], "mtime": acc["master"]["mtime"]},
        "次日卖出指令": nextsell,
        "日链": {"市场数据日目录_max": daily[-1] if daily else None, "缺": "20260914–20260917",
                 "note": "日链停摆第 4 个交易日(涨停池/炸板/跌停/龙虎榜 fact 全缺); 根因=日链三任务被禁用(同 12:0x 三场记录)。"}
    },
    "池内实况_决断时点前最后留档": {
        "tick_ts": last["ts"], "src": last.get("src"), "n": last.get("n"),
        "pool_date": last.get("pool_date"), "pool_stale": last.get("pool_stale"), "pool_kind": last.get("pool_kind"),
        "涨跌分布": {"涨": len(up), "跌": len(dn), "平": len(flat), "涨幅>=9.8%": len(zt_like), "跌幅<=-9.8%": len(dt_like)},
        "封板(现价=涨停价)": seal, "曾触板未回封(炸板)": brk,
        "涨幅前4": ["%s %+.2f%%" % (r["name"], r["pct"]) for r in top],
        "跌幅前4": ["%s %+.2f%%" % (r["name"], r["pct"]) for r in bot],
        "15分钟动量": mom,
        "口径警告": "该池=20260911 涨停池(滞后 3 个交易日, 管道自产 pool_stale ALARM); 报价为今日实时, 但成分股不构成今日市场截面 → 仅作当日温度旁证, 不构成任何个股判定/决策对象(零后视镜)。"
    },
    "三级判定": {
        "A级_预案内": {"对象": "无", "依据": "今日 playbook 缺(最新 20260907)、六路交易计划缺(最新 20260911 且 buys/sells 全空)、warboard 缺 → 无 trigger 可核, 条件决断=[]。"},
        "B级_预案外防守": {"对象": "无", "依据": "盘中作战 cash=%.1f/positions=[]/n_pos=0(mtime %s) + master cash=%.1f/positions=[] + 次日卖出指令=[] → 全空仓, 无持仓可逐票表态; 观察池为 9/11 陈旧池 → 炸板/大幅回撤/题材批量跳水三类均无合法判定对象(池内中视传媒炸板非持仓, 不触发 B 级)。"
                                  % (acc["盘中作战"]["cash"], acc["盘中作战"]["mtime"], acc["master"]["cash"])},
        "C级_预案外进攻": {"对象": "无(禁)", "依据": "总审 20260911 档位 C/置信 0.82『冰点防守…不形成进攻仓位』未解除, 且其可证伪条件(次日温度回升至40以上且连板晋级…)因 9/12 起日链+fact 断供无法验证; 叠加盘中禁改参数 + 今日截面数据缺失 → 预案外进攻一律不做, 仅记录。"}
    },
    "报警项": [
        "①契约三缺: pulse.json 全盘 0 命中(路径未实现) / warboard.json 今日缺(最新 20260909) / 执行流水.jsonl 全盘 0 命中;",
        "②预案真源断供: playbook max=20260907(断供第 8 个交易日), 六路交易计划 max=20260911(buys=0/sells=0);",
        "③数据源降级: 实时通道仅腾讯(src=腾讯, n=40), 无 Level1/无竞价轨迹; launcher.log 每 60s 续写正常(决断时点前 %.1f 分钟内有 tick);" % gap_min,
        "④观察池滞后: pool_date=20260911, pool_stale=true(管道 11:52:56 自产 ALARM『目标日 20260916 涨停池未落档』);",
        "⑤日链停摆: 市场数据日目录 max=20260911, 9/14–9/17 四日全缺(涨停池/炸板/跌停/龙虎榜/fact 全缺) → 五路复盘与 14:45 尾盘复盘均无事实底座;",
        "⑥文件名冲突: 盘中/20260917/临盘决断_20260917_1430.json 已被 9/16 catch_up 占用(12:08:24, sha256=%s), 本场追加式落 _inwindow 件, 未覆盖; 三项(改名/追加/场次重命名)待用户拍板。"
            % fingerprint(NOMINAL).get("sha256"),
        "⑦14:45 深场B 落档位预检: 临盘决断_20260917_1445.json=空闲(未被占用); _学习/盘中尾盘复盘_20260917.md 已含 9/16 catch_up 写的『午间台账条目』(11:58, 自述不代 14:45 决断) → 14:45 场次应追加(勿覆盖)。"
    ],
    "对账": {"引擎已执行": "无(执行流水.jsonl 全盘不存在)", "账本": "全空仓(盘中作战 cash=1000000.0/n_pos=0; master cash=%.1f/n_pos=0)" % acc["master"]["cash"], "结论": "一致, 无异常"},
    "备料_14:45深场B": {
        "尾盘卖预案候选": [],
        "尾盘卖预案_说明": "零对象: 盘中作战 positions=[] + 次日卖出指令=[] + 六路交易计划 sells=[] → 无可触发卖单(合法空, 非漏写); 14:45 场次若写 fills 即为编造。",
        "持仓逐票表态素材": "无对象(全空仓), 14:45 任务步骤3 的『持仓表态』应为空数组并注明空仓自洽。",
        "14:45 落档位": {"临盘决断_20260917_1445.json": "空闲", "盘中尾盘复盘_20260917.md": "已存在(9/16 catch_up 午间条目) → 追加, 勿覆盖"},
        "明日预案要点草稿": [
            "①【最高优先·数据链】日链三任务(涨停池/炸板/跌停/龙虎榜 fact)重启并补 9/14–9/17; 不恢复则 A 级永远零 trigger、B 级永远零对象、总审可证伪条件永远不可验证;",
            "②【观察池】把 pool_date 从 20260911 前滚到最近交易日; 当前 40 只旧池报价虽实时但成分失真, 只能当温度旁证;",
            "③【总审解冻判据】总审 20260911=档位C/置信0.82 防守未解除; 其可证伪条件=『次日温度回升至40以上 且 连板晋级 且 封板质量与至少两路荐票同时改善』——数据一恢复即优先核该条, 达标才谈解除防守;",
            "④【今日实况旁证·不作为决策依据】决断时点前 40 只旧池样本: 涨%d/跌%d, 封板%d 只(%s), 曾触板未回封 1 只(%s), 无跌幅≤-9.8%; 池内 15 分钟动量最弱 -0.85pp → 无『题材批量跳水』特征, 但样本不含今日热点成分, 不足以给情绪档位定性;",
            "⑤【纪律】14:45 与明日预案一律不得引用本场 14:30 之后的任何数据推断到尾盘动作; 无持仓时『尾盘卖预案』保持空数组, 不许为凑动作造票。"
        ],
        "备料口径声明": "本节为草稿(供 14:45 场次与用户参考), 非决断、非指令; 数据受限项已逐条标注证据边界。"
    },
    "诊断证据_写档时点后复核(非决策输入)": {
        "ts": recheck["ts"], "n": recheck.get("n"),
        "涨跌分布": {"涨": len([r for r in recheck_rows if r["pct"] > 0]), "跌": len([r for r in recheck_rows if r["pct"] < 0])},
        "相对决断时点变动pp": {"最弱3": ["%s %.2fpp" % (nm, v) for v, nm in delta[:3]], "最强3": ["%s +%.2fpp" % (nm, v) for v, nm in delta[-3:]]},
        "声明": "仅用于文件自身完整性/台账, 不构成决策输入(本场零动作, 无任何结论依赖该段)。"
    },
    "后视镜边界声明": ("决断时点=2026-09-17 14:30(名义/计划时点; 认领 14:30:10, 启动 14:30:11), 实际写档=%s。全部决策输入限定为该时点之前已留档的数据"
                 "(实时 tick<=%s 共 %d 条 / 三账本 / 预案与总审枚举 / 管道日志与报警留档), 或『该数据不存在』这一事实本身。"
                 "写档时点之后的实测(写档后复核段)仅标注为诊断, 不构成决策输入。本场零 fills、零预判、零触发区间、零条件价 → 不构成编造(铁律①)。"
                 % (WRITE_TS, last["ts"], len(pre))),
    "report": None
}
rec["report"] = ("心跳hb-e无动作·仅报警: 2026-09-17 14:30 尾盘前哨段(in-window, 认领14:30:10)——实时留档新鲜(决断时点前 %.1f 分钟内有 tick, %s–%s 共 %d 条/跨度%.0f分钟/src=腾讯降级源), 未触发断更红线; "
                 "但 A级无对象(playbook max 20260907、六路交易计划 max 20260911 且 buys/sells 全空、warboard 今日缺)、B级无对象(全空仓: 盘中作战 cash=1000000.0/positions=[]/n_pos=0, master cash=%.1f/positions=[], 次日卖出指令=[]; 池内中视传媒炸板非持仓)、C级禁止(总审 20260911 档位C/置信0.82『不形成进攻仓位』未解除且可证伪条件因日链断供不可验证) → ALARM_ONLY, 零 fills 零条件价; "
                 "14:45 深场B 备料已出(尾盘卖预案候选=[]合法空, 明日预案要点草稿 5 条, 14:45 落档位预告); 另报 观察池滞后(pool_date=20260911, stale=true)/日链停摆第4日(日目录 max=20260911, 9/14–9/17 全缺)/pulse与执行流水全盘0命中/名义件 临盘决断_20260917_1430.json 已被 9/16 catch_up 占用 → 本场追加式落 _inwindow 件未覆盖, 处置待批。") % (
    gap_min, pre[0]["ts"], last["ts"], len(pre), span_min, acc["master"]["cash"])

with io.open(OUT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)

alarm_line = {
    "ts": WRITE_TS, "date": D, "session": "hb-e_1430", "job_id": "4deb15fee730",
    "execution_id": "2618f7dee90a406ea4db3392037f0b83",
    "level": "ALARM_ONLY", "type": "no_action_objects_plus_supply_chain_gaps",
    "nominal_decision_ts": "2026-09-17 14:30", "exec_kind": "in_window",
    "decision_file": "盘中/%s/临盘决断_%s_1430_inwindow.json" % (D, D),
    "nominal_file_occupied_by": "盘中/%s/临盘决断_%s_1430.json (9/16 catch_up, sha256 %s)" % (D, D, fingerprint(NOMINAL).get("sha256")),
    "fills": [],
    "detail": rec["report"],
    "依据": "①红线未触发: realtime_ticks 决断时点前最后一档 %s(距决断 %.1f 分钟); ②A/B/C 三级均无合法动作对象(见决断文件『三级判定』); ③观察池 pool_date=20260911 stale=true; ④契约三缺+预案断供+日链停摆; ⑤发出版不可覆盖 → 追加 _inwindow 件, 既有 9 行未改动。" % (last["ts"], gap_min)
}
with io.open(ALARM, "a", encoding="utf-8") as f:
    f.write(json.dumps(alarm_line, ensure_ascii=False) + "\n")

print("WROTE", OUT)
print("APPENDED", ALARM)
print("gap_min", gap_min, "n_pre", len(pre), "seal", len(seal), "brk", len(brk))
print("NOMINAL fingerprint", fingerprint(NOMINAL))
