# -*- coding: utf-8 -*-
"""hb-d(13:30) 报警登记: 追加一行到 盘中/20260921/报警_20260921.jsonl (append-only, 不覆盖既有 3 行)。"""
import json, os, datetime as dt

ROOT = r"D:\股票数据\市场数据"
TODAY = "20260921"
D = os.path.join(ROOT, "盘中", TODAY)
AP = os.path.join(D, "报警_%s.jsonl" % TODAY)
DEC = os.path.join(D, "临盘决断_%s_1330.json" % TODAY)
assert os.path.exists(DEC), "decision file 缺失"

before = [l for l in open(AP, encoding="utf-8") if l.strip()]
before_hash = __import__("hashlib").sha256(open(AP, "rb").read()).hexdigest()[:16]

row = {
  "ts": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
  "date": TODAY,
  "session": "hb-d_1330",
  "job_id": "c415a7792216",
  "execution_ref": ("scheduled_instant=2026-09-21T05:30:00+00:00(=13:30 CST) / claimed_at=2026-09-21T13:30:08.731349+08:00 / "
                    "started_at=2026-09-21T13:30:09.654518+08:00 / status=running / pid=19836 (来源 executions.db)"),
  "scheduled_instant": "2026-09-21T05:30:00+00:00 (= 2026-09-21 13:30 CST)",
  "kind": "on_time (lateness≈8.7s < grace → 调度侧标 on_time; 本机盘中链路自 11:46:29 起持续落 tick → 名义时点前已有留档)",
  "lateness": "≈8.7s (名义 13:30 → 认领 13:30:08.73); 本场为今日首个『在窗』实时场次",
  "type": "no_action_no_object + contract_missing_three + daily_chain_down_day7 + stale_observation_pool",
  "level": "ALARM_ONLY",
  "fills": [],
  "持仓表态": "全账户空仓 → 无持仓可表态(盘中作战 cash=1000000.0/positions=[]/n_pos=0; master cash=1009012.5/positions=[]; 次日卖出指令=[])",
  "decision_file": "盘中/20260921/临盘决断_20260921_1330.json",
  "reason": ("未触发『断更>10分钟』红线(决断时点前最后 tick=13:29:47, 断更 13.0s=0.22min), 但三个级别判定对象全空 → 无动作: "
             "A级无对象(playbook max=20260907、warboard 今日缺、六路交易计划 max=20260911 → 无 trigger; 9/18 尾盘复盘 §八 6 条仅观察锚、"
             "无触发区间与价位)、B级无对象(空仓; 池内扫描 2分钟批量跳水=0/单票2分钟急跌=0/高点回撤≥5% 仅 1 只且当日红盘)、"
             "C级禁(总审 20260911 C档 0.82 未解除 + 盘中禁改参数) → 零 fills / 零条件价 / 零 px_exec。"),
  "data_freshness": {
    "pulse.json": "存在=False(全盘 0 命中) → 契约路径未实现, 无对象可核",
    "realtime_ticks": ("新鲜: 决断时点前 104 条(11:46:29–13:29:47, 每 60s, 无 >90s 断档), 断更 0.22min; "
                     "src=腾讯单源, n=40, pool_date=20260911, pool_stale=True"),
    "warboard": "盘中/20260921/warboard.json 不存在; 最新=20260909",
    "执行流水.jsonl": "全盘 0 命中(0 成交流水)",
    "预案真源": "playbook max=20260907(buys=[]) / 六路交易计划 max=20260911 / 总审 max=20260911 档位C 置信0.82",
    "日链": "市场数据日目录 max=20260911(停摆第 7 个交易日) → 温度/涨停家数/炸板/封板质量 全 null",
    "池内实况(13:29:47)": "40 只(9/11 陈旧池, 降级样本): 涨24/跌14, 中位+0.32%, 均值+0.46%; 涨停 1 只(002585 双星新材 +10.04%); "
                     "午后 13:00:42→13:29:47 均值 +0.72%→+0.46%(Δ-0.26pp, 温和走弱无跳水); 跌幅前5=中视传媒-5.71/铭普光磁-3.94/"
                     "光电股份-2.99/中新赛克-2.69/澳弘电子-2.64",
    "引擎判定流水": "_学习/_模拟盘/盘中作战/判断流水.jsonl mtime=11:46:31, 末条=08-21 11:46 → 今日无新判定行"
  },
  "对账": {"引擎已执行": "无(执行流水.jsonl 全盘不存在; 判断流水末条=08-21 11:46)",
          "账本": "全账户空仓(盘中作战 cash=1000000.0/n_pos=0; master cash=1009012.5/n_pos=0; 次日卖出指令=[])",
          "结论": "一致, 无异常; 无成交、无持仓、无卖单 → 无敞口漏记"},
  "机制发现": {
    "①": "契约三缺: pulse.json / 执行流水.jsonl 全盘 0 命中, warboard.json 今日缺 → 契约-实现二选一未决",
    "②": "预案真源断供: playbook max=20260907(空缺第 10 个交易日), 六路交易计划/总审 max=20260911 → A/C 级判定无底座",
    "③": "日链停摆第 7 个交易日(日目录 max=20260911): 早盘简报第 3/5/6 条锚永久不可核",
    "④": "观察池滞后: pool_date=20260911, pool_stale=true(管道 11:46:23 ALARM: 目标日 20260918 涨停池未落档)",
    "⑤": "本日调度集中补发: 今日 44 条执行全由 pid 19836 于 11:46:14–11:46:33 补发(hb-a 迟到126.25min/hb-b 76.2min/hb-c 46.3min; "
          "宿主 process_started_at=11:45:27.96 而本机 LastBootUpTime=08:45:59 → 机器在而宿主未运行)",
    "⑥": "iFinD 不可用: THS_iFinDLogin rc=-2(8602/8899 无监听) → 外围锚/竞价快照降级至末位源 sina",
    "⑦": "引擎判定流水停更(末条 08-21)"
  },
  "后视镜边界声明": ("决断时点=2026-09-21 13:30; 全部决策输入限定为该时点前已留档数据(tick≤13:29:47 共 104 条 / 三账本 / "
                "预案与总审枚举 / 管道与报警留档 / 9-18 尾盘复盘) 或『该数据不存在』这一事实; 写档时点之后的实测仅用于本行自身完整性描述, "
                "不作决策输入。零 fills / 零预判 / 零条件价 / 零 px_exec → 不构成编造(铁律①)。"),
  "收市后待批清单": ["① pulse/执行流水 契约-实现二选一(或解除契约); ② warboard 重建 + 观察池 pool_date 前滚至最新交易日; "
              "③ 日链三任务补跑 9/14–9/18 五日 + 恢复每日; ④ 六路交易计划/总审/playbook 断供恢复; "
              "⑤ iFinD 保活修复(iFinDPy.pth/login rc=-2); ⑥ 调度宿主开机后自启(避免上午名义段集中补发); "
              "⑦ 盘中作战引擎(盘中回应引擎.py)今日未产出判定行, 收市后核查; ⑧ 港股/外围锚源修复"]
}

with open(AP, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")

after = [l for l in open(AP, encoding="utf-8") if l.strip()]
print("前 %d 行 / 后 %d 行 (必须 +1, 且前 %d 行原样保留)" % (len(before), len(after), len(before)))
print("append 前 sha256_16 =", before_hash)
print("前 %d 行哈希是否原样 = %s" % (len(before), before == after[:len(before)]))
print("新行 ts =", row["ts"], "| session =", row["session"], "| level =", row["level"], "| fills =", row["fills"])
