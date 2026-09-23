# -*- coding: utf-8 -*-
"""deepb 1445 catch_up ALARM 写入 (2026-09-15 补跑, 名义 slot=2026-09-14 14:45)"""
import json, os, datetime

BASE = r"D:\股票数据\市场数据"
D_EXEC = "20260915"
alarm_p = os.path.join(BASE, "盘中", D_EXEC, "报警_%s.jsonl" % D_EXEC)
assert os.path.isdir(os.path.dirname(alarm_p)), "报警目录不存在: " + os.path.dirname(alarm_p)

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

detail = (
    "尾盘场深场B(名义决断时间戳=2026-09-14 14:45 周一〈正常交易日〉; 本次实际执行=2026-09-15 盘后; "
    "派发=catch_up, dispatched_at=2026-09-15 18:52:12, lateness=101232s≈28.1h, 见 cron executions last_dispatch)。"
    "①时窗合法性: 分钟级盘中场次的零后视镜前提是「执行时刻≈决断时刻」, 本场执行晚于名义时刻约28小时, "
    "决断输入只能取 <=2026-09-14 14:45 已留档数据; 而该日全盘零盘中留档(见②) -> 只报警禁决策, "
    "不写预判/触发区间/条件价(铁律①)。本场未写 临盘决断_20260915_1445.json(黑障下写条件价即编造); "
    "与 hb-c(18:58 落档)同口径。"
    "②数据新鲜度红线(本场独立复验): "
    "a) 盘中/20260914 目录不存在; 盘中/20260915 目录为本轮补跑 19:01 新建(仅含 报警_20260915.jsonl); "
    "b) pulse.json 全盘 find 0命中(该路径未实现, 脉搏为 warboard 内嵌 fact 字段); "
    "c) warboard.json 最新内容落档=盘中/20260909/warboard.json(date=20260909, ts=「2026-09-09 晚间复盘重建」), "
    "但 mtime=2026-09-15 18:52(本轮补跑时段) -> 该历史发出版被回写, 是否逐字节等同原落档未能自证, 列待核; "
    "9/14、9/15 无任何 warboard; "
    "d) 执行流水.jsonl 全盘 0命中(未实现) -> 「引擎已执行了什么」无独立对账源, 只能以双账本为准(见③); "
    "e) 实时留档管道: 本机无 盘中实时管道.py 进程; 盘中/pipeline.lock 冻结=「20260911 09:14:49」; "
    "盘中/launcher.log 尾部=[10:00:11] 连续30分钟全源失败,报警退出(mtime=2026-09-11 10:00, 尾部可见 iFinD 实时 errorcode=-1010 streak=1..30) "
    "-> 自 2026-09-11 09:31 至今约4.4天零实时留档, 远超10分钟阈值 -> 只报警禁决策。"
    "③尾盘卖预案执行=无动作, fills=[]: 六路交易计划 _学习/交易计划_theme_*.json 最新=20260911 且 buys=[]/sells=[] "
    "-> 无 leg=close / take_zt 声明; 双账本空仓(_学习/_模拟盘/盘中作战账本.json 本日18:52回写: 持仓=[]/n_pos=0/nav=1000000.0/cash_pct=100; "
    "master/state.json(9/14 16:08): cash=1009012.5/positions=[]) -> 无票可卖, 空仓自洽(非漏执行)。"
    "④A级对象=0: playbook.json 最新=20260907(断供); 市场数据日目录最新=20260911 "
    "-> 连板梯队/炸板/大幅回撤/题材批量跳水 无判定对象。"
    "⑤持仓表态=[]: 无持仓票, 逐票「今日表现/浮盈/明日计划/持有或卖出理由」对象数=0(空仓即防守, 非漏写)。"
    "⑥C级=禁止: 最新总审=总审_20260911(档位C 冰点防守, 置信度0.82, 证据=温度12.7/最高连板4/涨停40/炸板18/跌停21; "
    "可证伪条件=次日温度回升≥40且连板晋级+封板质量+≥两路荐票同时改善)未解除 + 盘中禁改参数 + 零有效票池。"
    "⑦前瞻(9/16 09:14 场次前置是否可用)=否: 管道进程/lock/数据源仍处 9/11 冻结态; 本机监听端口枚举 8899(盯盘台)/8602(iFinD)/8420(记忆) 全无。"
    "⑧环境侧客观事实(非决策输入): 计划任务 StockDailyChain 状态=「已禁用」(上次运行 2026/9/11 16:30, 上次结果=1); "
    "以下 cron 处 paused: sentiment-daily-review / weixin-review-push / sentiment-offline-replay / warboard-rebuild-watchdog / "
    "sentiment-release-stability-closeout / stuck-session-watch -> 9/15 盘后复盘无自动触发源(是否恢复待用户拍板)。"
    "⑨收市后独立复核(仅台账, 严禁作盘中决策输入, 铁律②): 腾讯日K sh000001 = 9/11收3888.110、9/14收3885.330、9/15收3864.280 "
    "(实时报价戳 20260915161402, -21.05/-0.54%) -> 9/14、9/15 均为正常交易日; 佐证=竞价快照存档/20260915_meta.json(18:54:06 ifind_rt 5505条, "
    "自标「污染:>09:30盘中累计,只留档不训练」), 9/14 无快照。"
    "⑩本场结论: 无动作, fills=[]; 记录本轮「catch_up 补跑时窗合法性判定」机制发现(与 hb-c 一致), 建议统一入审计。"
)

rec = {
    "ts": ts,
    "session": "deepb_1445",
    "level": "ALARM",
    "type": "realtime_channel_dead_data_blackout",
    "scope": "intraday_chain",
    "detail": detail,
    "decision_file": None,
    "fills": [],
}

n_before = sum(1 for _ in open(alarm_p, encoding="utf-8")) if os.path.exists(alarm_p) else 0
with open(alarm_p, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
n_after = sum(1 for _ in open(alarm_p, encoding="utf-8"))
print("ALARM appended:", alarm_p)
print("lines before/after =", n_before, "/", n_after)
print("ts =", ts)
