# -*- coding: utf-8 -*-
"""心跳 hb-c (11:00 半日收尾段) 补落档: 盘中/20260918/临盘决断_20260918_1100.json (ALARM_ONLY, 非决策)
+ 报警 jsonl 追加勘误行(目录快照时点变化)
铁律: 发出版不可覆盖 / 只用决断时间戳(11:00)之前已留档数据 / 断更>10分钟=只报警禁决策
口径与同批兄弟场次(hb-a 0940 / hb-b 1030 / hb-d 1330 / deepb 1445)一致: level=ALARM_ONLY, 条件决断=[], fills=[]"""
import json, os, datetime

D = "20260918"
BASE = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + os.sep + "..")
outdir = os.path.join(BASE, "盘中", D)
dec_p = os.path.join(outdir, "临盘决断_%s_1100.json" % D)
alarm_p = os.path.join(outdir, "报警_%s.jsonl" % D)
assert not os.path.exists(dec_p), "发出版已存在, 不可覆盖: " + dec_p

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

说明 = (
    "11:00 半日收尾段心跳 hb-c(名义决断时点 2026-09-18 11:00)。本件=ALARM_ONLY 留档, 非决策。"
    "①本实例 identity: job_id=3e4b3b30b816, execution_id=713067e0f9a74d04ae4d64c29d8905f7, "
    "scheduled_instant=2026-09-18T11:00:00+08:00, dispatched=2026-09-18T17:33:58, actual_start=2026-09-18T17:34:04, "
    "kind=catch_up, lateness=23638.1s(约6.57h) → 名义决断时点已过且已收盘(15:00), 不以 11:00 名义做任何决断。"
    "②数据面硬缺(断更红线硬触发): 决断时点(9/18 11:00)之前本日盘中留档=零 —— 盘中/20260918/ 目录当时不存在, "
    "pulse.json(=warboard 内嵌 fact 快照)/warboard.json/执行流水.jsonl/报警 jsonl 全缺; 实时通道最后留档=盘中/20260917/realtime_ticks.jsonl(mtime 9/17 15:04), "
    "相对决断时点断更约1196分钟 >> 10分钟红线 → 只报警禁决策。佐证: pipeline.lock 冻结=\"20260917 10076 11:52:55\", "
    "launcher.log 末行=\"[15:05:36] 收盘退出\"(9/17) → 9/18 盘中管道(09:25 起)从未启动。"
    "③根因: 调度宿主整段离线 —— executions.db 实证 9/18 最后成功 run=02:30:41, 至 17:33:58 零 run; 17:34 起一次 catch-up "
    "集中补齐 09:40/10:30/11:00/13:30/14:30 五场心跳 + deepb1445 + 竞价快照/THS(17:34–17:47 落档)。非盘中通道故障。"
    "④三级无动作: A级: _学习/交易计划_*.json 全量 max=20260911, playbook 最新=盘中/20260907/playbook.json → 无可触发 leg → 条件决断=[] 合法空; "
    "B级: 盘中作战账本 nav=1000000.0/现金=1000000.0/持仓=[]/n_pos=0/cash_pct=100(起算20260813) → 空仓即防守, 无持仓可守; "
    "C级: 无五路正式荐票 + 观察池(zt_pool max=20260911, 滞后5个交易日) + 盘中禁改参数 → 不预埋不追买不设帽。"
    "⑤本批一致性: 同批 catch-up 兄弟场次(hb-a 0940 / hb-b 1030 / hb-d 1330 / deepb 1445)已分别落档同名 ALARM_ONLY 件, "
    "均为 条件决断=[] / fills=[] / level=ALARM_ONLY → 本件口径与之一致。"
)

doc = {
    "date": D,
    "session": "hb-c",
    "ts": "11:00",
    "decision_ts_nominal": "2026-09-18 11:00",
    "exec_kind": "catch_up",
    "lateness": "≈6.57h (23638.1s; 名义 2026-09-18 11:00 → 实际 17:34:04, 已收盘)",
    "write_ts": now,
    "level": "ALARM_ONLY",
    "动作级别": "无动作(非漏写); 本件为报警留档",
    "场次说明": 说明,
    "条件决断": [],
    "fills": [],
    "decision": None,
    "data_freshness": {
        "交易日核验": "sentiment.core.calendar 缺失(ModuleNotFoundError, 同8/13起先例)。后验佐证链(仅日历门禁, 非决策输入): 腾讯收盘报价时间戳=20260918161402(沪指3911.87 +0.94%); THS 涨停池 20260918 含77只真实涨停; 2026-09-18=周五(中秋9/25、国庆10/1在其后) → 判定正常交易日",
        "pulse_json": "盘中/20260918/pulse.json 不存在(本系统 pulse=warboard 内嵌 fact)",
        "warboard_json": "最新=盘中/20260909/warboard.json(滞后6个交易日)",
        "执行流水": "全仓不存在 → 引擎本日零成交",
        "realtime_ticks": "最后留档=盘中/20260917/realtime_ticks.jsonl (mtime 9/17 15:04)",
        "pipeline.lock": "20260917 10076 11:52:55 (跨日残留未清)",
        "launcher.log": "末行 [15:05:36] 收盘退出 (9/17)",
        "断更时长": "相对 9/18 11:00 约1196分钟(约20.0h) → 红线硬触发",
    },
    "三级判定": {
        "A_预案内执行": {"对象": "无", "理由": "交易计划 max=20260911 / playbook 最新=20260907 → 无 leg=close/take_zt 票据", "结论": "条件决断=[] 合法空"},
        "B_预案外防守": {"对象": "无", "理由": "账本空仓(n_pos=0, cash=100%); 观察池 zt_pool max=20260911 滞后5交易日", "结论": "无炸板/回撤/题材跳水可判"},
        "C_预案外进攻": {"对象": "无", "理由": "无五路荐票 + 池滞后 + 盘中禁改参数", "结论": "禁止(不预埋/不追买/不设帽)"},
    },
    "报警项": ["盘中链本日(2026-09-18)从未启动: 零 tick 零 pulse 零 warboard 零 执行流水", "调度宿主停机 02:30→17:34 致全工作日 cron miss(5场心跳+deepb+竞价快照 全为 catch_up)"],
    "对账": {"发出版覆盖": "无(新建件, assert 未存在)", "fills": 0, "结论": "本场零成交, 与空仓账本互证"},
    "后视镜边界声明": (
        "本场执行时刻=2026-09-18 17:5x(收盘后); 全部市场信息(腾讯收盘报价 20260918161402 / THS 涨停池 17:47 / 竞价快照 17:36)"
        "均在名义决断时点 11:00 之后产生, 严格排除于决策输入之外; 决策输入仅限『应当留档而实际缺失』这一事实本身, "
        "故本场零 fills 零预判(写预判即编造, 铁律①)。"
    ),
    "report": "心跳hb-c无动作: 9/18 名义11:00场次因宿主02:30–17:34停机、盘中链全天未启动(决断时点前零留档, 断更约1196分钟)→只报警禁决策, 条件决断=[]/fills=[], 空仓无仓可守, 三级均无动作。",
}

with open(dec_p, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)

勘误 = {
    "ts": now,
    "date": D,
    "session": "hb-c_1100",
    "job_id": "3e4b3b30b816",
    "execution_id": "713067e0f9a74d04ae4d64c29d8905f7",
    "kind": "catch_up",
    "level": "ALARM_ONLY",
    "type": "alarm_record_addendum_directory_snapshot_staleness_and_session_doc_supplement",
    "decision_file": "盘中/20260918/临盘决断_20260918_1100.json",
    "fills": [],
    "detail": (
        "【勘误/补充, 追加不覆盖】本场前一条报警行(同 execution_id=713067e0f9a74d04ae4d64c29d8905f7, ts=2026-09-18 17:54:10)记录『盘中/20260918 目录不存在、"
        "pulse/warboard/执行流水/报警全缺』, 该表述为 2026-09-18 17:35–17:40 的目录快照事实, 当时成立; "
        "17:51–18:05 同批 catch-up 兄弟场次(hb-a 0940 ts=17:51:08 / deepb_1445 ts=17:54 / hb-b 1030 ts=18:05:12 / hb-d 1330) "
        "先后落档建目录并写入各自 ALARM_ONLY 件, 目录快照随之改变 → 以『决断时点(11:00)前』为准, 全缺结论不变(增量均为 17:5x 事后留档, "
        "不入决策输入)。补充: hb-c 本场已按同批口径补落 临盘决断_20260918_1100.json(level=ALARM_ONLY, 条件决断=[], fills=[]), "
        "与本行原『decision_file=null』并存解释=先报警后补件, 且补件发生在本行之后、未覆盖任何文件(named assert 未存在)。"
        "本批 5 场 + deepb 1445 全为 ALARM_ONLY / fills=[] → 9/18 全交易日数据面零留档, 无任何成交。"
    ),
    "后视镜边界声明": "本行仅记录留档事实与目录快照时点变化, 无任何市场判断, 不含 11:00 之后的行情作为决策输入。",
}
with open(alarm_p, "a", encoding="utf-8") as f:
    f.write(json.dumps(勘误, ensure_ascii=False) + "\n")

print("WROTE", dec_p, os.path.getsize(dec_p))
print("APPENDED", alarm_p, os.path.getsize(alarm_p))
