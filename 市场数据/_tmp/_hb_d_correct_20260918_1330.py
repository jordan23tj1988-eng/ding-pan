# -*- coding: utf-8 -*-
"""hb-d 2026-09-18 13:30 场次: 事实校正(根因措辞) + 追加更正行。
理由: 首稿写档后复核发现两处措辞需按实测校正(非改判断, 结论仍为 ALARM_ONLY/零动作):
  ① 宿主 pid 16124 的 process_started_at 原始值=178964183837, 单位=1/100秒 -> 实为 2026-09-17 18:43:58(首稿误按 claim 时刻写成 17:33:58);
  ② 系统 LastBootUpTime=2026-09-18 08:24:53 表明本机当日并非"整机停机", 而是 Hermes 调度宿主自 02:30:40 起至 17:33:58 零 dispatch/零日志(agent.log+errors.log 本日 15 点前 0 行) -> 措辞应由"整机停机"改为"调度宿主停摆"。
纪律: 结论与零动作不变更; 已落 报警 行不覆盖, 以追加『更正』行留痕。
"""
import json, os, hashlib, time

BASE = r"D:\股票数据\市场数据"
D = "20260918"
DD = os.path.join(BASE, "盘中", D)
OUT = os.path.join(DD, "临盘决断_%s_1330.json" % D)
ALARM = os.path.join(DD, "报警_%s.jsonl" % D)

rec = json.load(open(OUT, encoding="utf-8"))
before = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]

NEW_ROOT = ("【根因·定位校正】调度宿主 pid=16124(process_started_at=2026-09-17 18:43:58, 原始值 178964183837/100秒) "
            "本日 02:30:40 之后至 17:33:58 之间零 dispatch、零日志(agent.log 与 errors.log 本日 15 点前 0 行, 全部 1084+100 行集中在 17 时) "
            "-> 盘中时段(09:14–15:00)Hermes 调度器未运行, 盘中管道从未启动(launcher.log 停于 9/17 15:05:36『收盘退出』, pipeline.lock=9/17 11:52); "
            "系统 LastBootUpTime=2026-09-18 08:24:53 与『宿主进程 9/17 18:43:58 起驻留』并存 -> 与『休眠/睡眠-恢复导致调度停摆』一致, 而非冷启动/整机当日未开机; "
            "精确电源区间待查(候选: 8:25–17:33 处于睡眠 S3)。")

# ① 场次说明 / report 中的“本机整个交易日停机”措辞校正
rec["场次说明"] = rec["场次说明"].replace(
    "本场执行时点已在收盘(15:00)之后",
    "本场执行时点已在收盘(15:00)之后")
rec["report"] = rec["report"].replace(
    "本机整个交易日停机(executions.db 本日 23 条执行全部于 17:33:59–17:34:05 由 pid 16124 补发)",
    "Hermes 调度宿主整个交易时段停摆(executions.db 本日 23 条执行全部于 17:33:59–17:34:05 由 pid 16124 补发; 宿主自 02:30:40 起零 dispatch 零日志)")
# ② 报警项 ② 措辞校正
rec["报警项"][1] = ("②【根因·调度宿主停摆】" + NEW_ROOT.split("【根因·定位校正】")[1] +
                    " 证据: executions.db 本日 23 条执行全部于 17:33:59–17:34:05 被 pid 16124 以 catch_up 补发, 含 09:14 盘中管道 b8e2f1f39fd3 与其 30 分钟看门狗 d3bc2bc0b19d; 校正说明见文件尾『校正记录』;")
# ③ 旁证 executions.db 措辞校正
pc = rec["data_freshness"]["写档时点旁证(非决策输入)"]
pc["executions.db"] = ("本日 23 条执行记录中, 全部盘中 instant(09:14/09:21/09:24/09:40/10:00…/13:30/14:30/14:45) 的 claimed_at 集中在 17:33:59–17:34:05; "
                       "宿主 pid=16124 process_started_at=178964183837(1/100秒)=2026-09-17 18:43:58; 本日 00:00:42–02:30:40 有 6 条正常执行, 02:30:40 之后至 17:33:58 归零 "
                       "-> 调度宿主当日 02:30:40 后停摆, 盘中时段未运行(非仅本场迟到)。")
pc["日志旁证"] = "logs/agent.log 与 logs/errors.log 本日(2026-09-18)15 点前 0 行, 全部行集中在 17 时 -> 宿主盘中无运行痕迹(现场逐行统计)。"
rec["校正记录"] = {
    "时间": time.strftime("%Y-%m-%d %H:%M:%S"),
    "首稿sha256_16": before,
    "校正项": [
        "① 首稿称『本机整个交易日停机』+『pid 16124 process_started_at≈17:33:58』→ 已校正为『Hermes 调度宿主停摆』+『process_started_at=2026-09-17 18:43:58(1/100秒单位)』(依据: 原始值 178964183837 换算 + 系统 LastBootUpTime=2026-09-18 08:24:53 与进程存活并存);",
        "② 新增日志旁证与电源状态候选说明, 结论(ALARM_ONLY/零 fills/零条件价)与三级判定不变。"
    ],
    "纪律": "本次校正仅修正事实措辞, 未新增任何决策内容; 报警档以追加行留痕, 未覆盖既有 5 行中的任何一行。"
}
json.dump(rec, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
after = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]

corr = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "date": D, "session": "hb-d",
    "job_id": "c415a7792216", "execution_id": "eb15496cf5dc4e7e9b68c06a82a1caa3",
    "kind": "catch_up_correction", "level": "ALARM_ONLY", "type": "fact_correction_root_cause_wording",
    "对前一条(ts=2026-09-18 17:54:10)的更正": "该条 detail/依据 内『本机整个交易日停机(pid 16124 process_started_at≈17:33:58)』措辞不准 —— 实为 Hermes 调度宿主停摆(宿主进程 2026-09-17 18:43:58 起驻留, 本日 02:30:40 后零 dispatch 零日志; 本机 LastBootUpTime=2026-09-18 08:24:53 存在, 非整机当日未开机)。",
    "结论不变": "ALARM_ONLY / 零 fills / 零预判 / 零条件价; A级无对象、B级无对象(全账户空仓)、C级禁(总审 20260911 C档0.82未解除)。",
    "decision_file": "盘中/%s/临盘决断_%s_1330.json" % (D, D),
    "sha256_16_before": before, "sha256_16_after": after,
}
with open(ALARM, "a", encoding="utf-8") as f:
    f.write(json.dumps(corr, ensure_ascii=False) + "\n")

print("corrected", OUT, before, "->", after)
print("alarm lines:", sum(1 for _ in open(ALARM, encoding="utf-8")))
json.load(open(OUT, encoding="utf-8"))
print("JSON OK")
