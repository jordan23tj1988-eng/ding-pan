# -*- coding: utf-8 -*-
"""hb-d 2026-09-17 13:30 午后延续段: 留档 ALARM_ONLY(零fills/零预判)。
零后视镜: 全部决策输入 = 决断时点(2026-09-17 13:30)之前已留档数据; 写档时点之后的实测仅入台账区并显式声明。
发出版不可覆盖: 目标文件已存在则拒绝写入。"""
import io, json, os, glob, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据\市场数据"
D = "20260917"
INTRA = os.path.join(BASE, "盘中")
DD = os.path.join(INTRA, D)
DEC = datetime.datetime(2026, 9, 17, 13, 30, 0)
WRITE_TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUT = os.path.join(DD, "临盘决断_%s_1330.json" % D)
ALARM = os.path.join(DD, "报警_%s.jsonl" % D)

if os.path.exists(OUT):
    raise SystemExit("REFUSE: 发出版不可覆盖 -> %s 已存在" % OUT)

# ---- 决断时点前留档 (<=13:30) ----
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
up = [r for r in rows if r["pct"] > 0]
dn = [r for r in rows if r["pct"] < 0]
flat = [r for r in rows if r["pct"] == 0]
zt_like = [r for r in rows if r["pct"] >= 9.8]
dt_like = [r for r in rows if r["pct"] <= -9.8]
top = sorted(rows, key=lambda r: -r["pct"])[:4]
bot = sorted(rows, key=lambda r: r["pct"])[:4]
gap_min = round((DEC - datetime.datetime.strptime(last["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60.0, 1)

acc = {}
for nm in ("盘中作战", "master"):
    p = os.path.join(BASE, "_学习", "_模拟盘", nm, "state.json")
    j = json.load(open(p, encoding="utf-8"))
    acc[nm] = {"cash": j.get("cash"), "n_pos": len(j.get("positions") or []), "positions": j.get("positions") or []}
nextsell = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "次日卖出指令.json"), encoding="utf-8"))
zs = json.load(open(os.path.join(BASE, "_学习", "总审_20260911.json"), encoding="utf-8"))["总裁决"]
plan_legs = {}
for f in glob.glob(os.path.join(BASE, "_学习", "交易计划_*.json")):
    key = os.path.basename(f)[len("交易计划_"):-len(".json")]
    parts = key.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 8:
        plan_legs[parts[0]] = max(plan_legs.get(parts[0], ""), parts[1])
pb = sorted(glob.glob(os.path.join(INTRA, "*", "playbook.json")))
daily = sorted(os.path.basename(p) for p in glob.glob(os.path.join(BASE, "2026*")) if os.path.isdir(p))
today_alarms = [json.loads(l) for l in io.open(ALARM, encoding="utf-8", errors="replace") if l.strip()]

rec = {
    "date": D,
    "session": "hb-d",
    "ts": "13:30",
    "decision_ts_nominal": "2026-09-17 13:30 (scheduler in-window; 实际执行 %s)" % WRITE_TS,
    "write_ts": WRITE_TS,
    "level": "ALARM_ONLY",
    "动作级别": "无动作(零 fills / 零预判 / 零条件价)",
    "场次说明": "13:30午后延续段心跳 hb-d 第 4 段(本日). ★单段声明: 本实例=2026-09-17 13:30 名义段(jobs.json c415a7792216 expr '30 13 * * 1-5'), 非 catch_up —— 前序 12:09 落档的 hb-d 记录其名义段=2026-09-16 13:30(catch_up, lateness≈22.4h)并明示『今日 9/17 13:30 段由独立实例承担, 本场不预判』, 即本文件。三者不互相代决断。",
    "条件决断": [],
    "fills": [],
    "data_freshness": {
        "交易日校验": {
            "任务指定": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → ModuleNotFoundError: No module named 'sentiment'(本机实测, 该模块全盘不存在) → 指定校验环节不可用。",
            "可用替代": "市场数据/trading_calendar.py 存在(无 is_trading_day/today_str 接口); _学习/_交易日历.json 共 5397 条, 末条=20260911 → 缓存未含 9/14–9/17, 同样不可判今日。",
            "本场判定依据": "① 盘中/20260917/realtime_ticks.jsonl 决断时点前已落 97 条连续盘中报价(11:53:01–13:29:20, 每 60s) → 当日为交易日(实据, 非推断); ② 2026-09-17=周四, 中秋(9/25)/国庆(10/1)在其后。"
        },
        "realtime_channel": {
            "path": "盘中/20260917/realtime_ticks.jsonl",
            "n_total_now": len(ticks),
            "n_at_or_before_1330": len(pre),
            "first_ts": ticks[0]["ts"],
            "last_at_or_before_1330": last["ts"],
            "gap_min_at_decision": gap_min,
            "src": last.get("src"),
            "n_rows": last.get("n"),
            "结论": "★未触发『断更>10分钟』红线: 决断时点前 %.1f 分钟内有留档 → 允许决策流程; 但源头为腾讯降级源(iFinD 实时不可用), 无 Level1 盘口/无竞价轨迹。" % gap_min
        },
        "pulse": {"path": "盘中/%s/pulse.json" % D, "exists": False,
                  "note": "全盘 glob 0 命中(本系统脉搏=warboard 内嵌 fact 快照字段, 由 warboard_build.py 产出) → 任务步骤2 的 pulse 新鲜度核验: 无对象。"},
        "warboard": {"path": "盘中/%s/warboard.json" % D, "exists": False,
                     "fallback": "最新=盘中/20260909/warboard.json(9/10、9/11、9/15、9/16、9/17 均未产出) → 对今日零指向, 无 fact 快照/无优先成交序。"},
        "执行流水": {"path": "盘中/%s/执行流水.jsonl" % D, "exists": False,
                     "note": "全盘 glob 执行流水*.jsonl 0 命中 → 无成交可对账。"},
        "预案真源": {"playbook_max": os.path.relpath(pb[-1], BASE).replace("\\", "/") if pb else None,
                     "交易计划_max_by_leg": plan_legs,
                     "今日预案文件": [],
                     "note": "playbook 断供第 7 个交易日(9/08 起); 六路交易计划全部停在 20260911 → 今日无 leg=close/take_zt 可触发票据 → A级条件决断合法为空。"},
        "总审": {"path": "_学习/总审_20260911.json", "档位": zs.get("档位"), "置信度": zs.get("置信度"),
                 "结论": zs.get("结论"), "可证伪条件": zs.get("可证伪条件"),
                 "note": "无覆盖 9/14–9/17 的总审 → 防守框架在册未解除。"},
        "账本": acc["盘中作战"],
        "账本_master": {"cash": acc["master"]["cash"], "n_pos": acc["master"]["n_pos"]},
        "次日卖出指令": nextsell,
        "日链": {"市场数据日目录_max": daily[-1] if daily else None, "缺": "20260914–20260917",
                 "note": "日链停摆第 4 个交易日(涨停池/炸板/跌停/龙虎榜 fact 全缺)。"}
    },
    "池内实况_决断时点前最后留档": {
        "tick_ts": last["ts"], "src": last.get("src"), "n": last.get("n"),
        "pool_date": last.get("pool_date"), "pool_stale": last.get("pool_stale"),
        "pool_kind": last.get("pool_kind"),
        "涨跌分布": {"涨": len(up), "跌": len(dn), "平": len(flat), "涨幅>=9.8%": len(zt_like), "跌幅<=-9.8%": len(dt_like)},
        "涨幅前4": ["%s %+.2f%%" % (r["name"], r["pct"]) for r in top],
        "跌幅前4": ["%s %+.2f%%" % (r["name"], r["pct"]) for r in bot],
        "口径警告": "该池=20260911 涨停池(滞后 3 个交易日, 管道自产 pool_stale ALARM), 仅作当日温度旁证, 不构成任何个股判定/决策对象。"
    },
    "三级判定": {
        "A级_预案内": {"对象": "无", "依据": "今日 playbook 缺(最新 20260907)、六路交易计划缺(最新 20260911)、warboard 缺 → 无 trigger 可核, 条件决断=[]。"},
        "B级_预案外防守": {"对象": "无", "依据": "盘中作战 cash=1000000/positions=[]/n_pos=0(mtime %s) + master cash=%.1f/positions=[] + 次日卖出指令=[] → 空仓, 无持仓可逐票表态; 观察池为 9/11 陈旧池 → 炸板/大幅回撤/题材批量跳水三类均无合法判定对象。" % (
            datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "state.json"))).strftime("%Y-%m-%d %H:%M:%S"), acc["master"]["cash"])},
        "C级_预案外进攻": {"对象": "无(禁)", "依据": "总审 20260911 档位 C/置信 0.82『冰点防守…不形成进攻仓位』未解除, 且其可证伪条件(次日温度回升至40以上且连板晋级…)因 9/12 起日链+fact 断供无法验证; 叠加盘中禁改参数 → 预案外进攻一律不做, 仅记录。"}
    },
    "报警项": [
        "①契约三缺: pulse.json 全盘 0 命中(路径未实现) / warboard.json 今日缺(最新 9/09) / 执行流水.jsonl 全盘 0 命中;",
        "②预案真源断供: playbook max=20260907, 六路交易计划 max=20260911;",
        "③数据源降级: 实时通道仅腾讯(src=腾讯, n=40), pipeline.lock=20260917 10076 11:52:55, launcher.log 首行为启动失败留痕(路径含双反斜杠导致 'can't open file')→ 通道可用但为降级链路;",
        "④观察池滞后: pool_date=20260911, pool_stale=true(管道 11:52:56 自产 ALARM『目标日 20260916 涨停池未落档』);",
        "⑤日链停摆: 市场数据日目录 max=20260911, 9/14–9/17 四日全缺(涨停池/炸板/跌停/龙虎榜/fact 全缺);",
        "⑥今日 14:30 文件名占用风险: 盘中/20260917/临盘决断_20260917_1430.json 已由 9/16 名义 hb-e catch_up 于 12:08 写入(其正文自述『不代今日 14:30 决断』) → 今日 14:30 实时段将撞『发出版不可覆盖』, 收市后需二选一(改名留档 or 追加式补档)。"
    ],
    "对账": {"引擎已执行": "无(执行流水.jsonl 全盘不存在)", "账本": "空仓(cash=1000000, positions=[], n_pos=0)", "结论": "一致, 无异常"},
    "后视镜边界声明": "决断时点=2026-09-17 13:30(名义/计划时点), 实际写档=%s。全部决策输入限定为该时点之前已留档的数据(实时 tick<=13:29:20 共 97 条 / 三账本 / 预案与总审枚举 / 管道与报警留档), 或『该数据不存在』这一事实本身。写档时点之后的实测(如写档瞬间 tick 条数)仅用于文件自身完整性描述, 不构成决策输入。本场零 fills、零预判、零触发区间、零条件价 → 不构成编造(铁律①)。" % WRITE_TS,
    "report": None
}
rec["report"] = ("心跳hb-d无动作·仅报警: 2026-09-17 13:30 段(in-window)——实时留档新鲜(决断时点前 %.1f 分钟内有 tick, 11:53:01–13:29:20 共 %d 条/src=腾讯降级源), 未触发断更红线; 但 A级无对象(playbook max 20260907、六路交易计划 max 20260911、warboard 今日缺)、B级无对象(三账本全程空仓: 盘中作战 cash=1000000/positions=[]/n_pos=0, master cash=%.1f/positions=[], 次日卖出指令=[])、C级禁止(总审 20260911 档位C/置信0.82『不形成进攻仓位』未解除) → ALARM_ONLY, 零 fills 零条件价; 另报 观察池滞后(pool_date=20260911, stale=true)/日链停摆第4日(日目录 max=20260911)/pulse与执行流水全盘0命中/今日14:30文件名已被 9/16 catch_up 占用, 收市后待批。") % (
    gap_min, len(pre), acc["master"]["cash"])

with io.open(OUT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)

alarm_line = {
    "ts": WRITE_TS, "date": D, "session": "hb-d_1330", "job_id": "c415a7792216",
    "level": "ALARM_ONLY", "type": "no_action_objects_plus_supply_chain_gaps",
    "nominal_decision_ts": "2026-09-17 13:30", "exec_kind": "in_window",
    "decision_file": "盘中/%s/临盘决断_%s_1330.json" % (D, D),
    "fills": [],
    "detail": rec["report"],
    "依据": "①红线未触发: realtime_ticks 决断时点前最后一档 %s(距决断 %.1f 分钟); ②A/B/C 三级均无合法动作对象(见决断文件『三级判定』); ③观察池 pool_date=20260911 stale=true; ④契约三缺+预案断供+日链停摆。本行为追加留档, 不改动既有 8 行。"
            % (last["ts"], gap_min)
}
with io.open(ALARM, "a", encoding="utf-8") as f:
    f.write(json.dumps(alarm_line, ensure_ascii=False) + "\n")
print("WROTE", OUT)
print("APPENDED", ALARM)
print("gap_min", gap_min, "n_pre", len(pre))
