# -*- coding: utf-8 -*-
"""hb-e 心跳 14:30尾盘前哨 2026-08-24: 只报警禁决策(数据全天断更, 同族第9日延续)"""
import json, os, sys, datetime

BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
from _jsonl_append import append_dedup

TDAY = "20260824"
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

decision = {
    "date": TDAY,
    "session": "hb-e_1430",
    "ts": "14:30",
    "write_ts": now,
    "条件决断": [],
    "data_freshness": {
        "pulse": {"path": f"盘中/{TDAY}/pulse.json", "exists": False,
                  "note": "今日全天未生成(盘中/20260824/ 目录为空; 全盘搜索pulse.json 0命中; 同族断更第9日延续: 8-13/8-14/8-17/8-18/8-19/8-20/8-21/今日)"},
        "warboard": {"path": f"盘中/{TDAY}/warboard.json", "exists": False,
                     "note": "今日无当日warboard; 最近留档=盘中/20260821/warboard.json(08-21 21:00) date=20260821 account起算20260813 nav1.0 pos0% cash100% n_pos=0, 非今日预案不作决断输入, 仅作持仓背景参考"},
        "playbook": {"path": f"盘中/{TDAY}/playbook.json", "exists": False,
                     "note": "今日无playbook(全盘搜索8/21后无新playbook.json); 最近=盘中/20260821/playbook.json(08-20 19:42晚间预案, 昨日预案禁跨日引用不作今日输入)"},
        "执行流水": {"path": f"盘中/{TDAY}/执行流水.jsonl", "exists": False},
        "报警": {"path": f"盘中/报警_{TDAY}.jsonl",
                "note": "今日不存在(盘中/ 无报警_20260824.jsonl; 今日hb-a/hb-d无留痕, 本心跳为今日首条报警)"},
        "launcher": {"path": "盘中/launcher.log",
                     "note": "今日盘中时段实时取数管道未运行: 早段09:58-10:00全源失败streak=30于10:00:19'连续30分钟全源失败,报警退出'(iFinD errorcode=-1010, 腾讯实时NoneType); 18:34:32收盘段重启(观察池=20260820\\\\zt_pool.csv 79只)→18:34:36 iFinD login rc=0→连续段启动→收盘退出; 19:09:09晚间段(观察池=20260821\\\\zt_pool.csv 54只)→19:09:17 iFinD login rc=0→连续段启动→收盘退出(盘中时段零留档)"},
        "pipeline_lock": "20260824 19:09:02(晚间launcher写入, 非盘中时间戳)",
        "stale_min": "全天(执行时刻19:1x已过收盘, 盘中时段零留档, 远超10分钟红线)",
        "verdict": "只报警禁决策: 数据断更>10分钟, 无pulse/无当日warboard/无playbook/无实时tick → 一切判断无据, 写任何预判即编造(铁律①)"
    },
    "decision": {
        "level": "ALARM_ONLY",
        "fills": [],
        "reason": ("数据全天断更(同族第9日延续: 8-13~8-21+今日; 今日盘中实时管道未运行, 早段10:00:19全源失败报警退出后无恢复, "
                   "18:34/19:09两次晚间段均'连续段启动→收盘退出'; 本心跳执行时刻19:1x已过收盘) → "
                   "①B级防守无对象(最新留档8-21 warboard: account持仓0/现金100%/n_pos=0, 无炸板/回撤可守, 题材批量跳水无从核验) "
                   "②A级trigger无预案可依(今日无playbook, 8/21预案神奇制药600613为昨日预案禁跨日引用; sells无留档) "
                   "③C级预案外进攻禁止(无数据无从核验, 写即编造违反铁律①零编造) "
                   "④14:45深场B备料(尾盘卖预案候选/明日预案要点草稿)无当日行情无从做起, 写即编造; "
                   "依铁律只报警禁决策, 不写任何触发证据与预判"),
        "note": ("今日首条报警(盘中/报警_20260824.jsonl 不存在, 今日hb-a/hb-d未留痕); "
                 "取数链恢复并补pulse.json+当日warboard后, 下一心跳场(14:57)方可恢复实质决策; "
                 "交易日校验: sentiment.core.calendar模块仍缺失(同8-13~8-21先例), 依周一历法+今日盘中管道早段尝试运行(09:58-10:00全源失败)+晚间launcher活跃(pipeline.lock=20260824 19:09:02, 观察池=20260821 zt_pool)按正常交易日处理")
    }
}

dpath = os.path.join(BASE, "盘中", TDAY, f"临盘决断_{TDAY}_1430.json")
if os.path.isfile(dpath):
    print("DECISION_SKIP_EXISTS:", dpath)
else:
    with open(dpath, "w", encoding="utf-8") as f:
        json.dump(decision, f, ensure_ascii=False, indent=2)
    print("DECISION_WRITTEN:", dpath)

# ---- 报警jsonl追加(去重 session=hb-e; 今日文件不存在则新建) ----
rec = {
    "ts": now,
    "session": "hb-e",
    "level": "ALARM",
    "type": "data_stale",
    "scope": "intraday_chain",
    "detail": (
        "心跳hb-e(1430尾盘前哨)链路全天断更(同族第9日延续: 8-13/8-14/8-17/8-18/8-19/8-20/8-21/今日): "
        "盘中/20260824/ 目录为空(无playbook.json/pulse.json/warboard.json/执行流水.jsonl 全MISSING); "
        "realtime_ticks.jsonl最新仅20260813; "
        "本心跳执行时刻=08-24 19:1x(已过收盘, 盘中时段零留档), 14:30决断时间戳之前无任何当日行情数据可引; "
        "launcher.log今日: 早段09:58-10:00全源失败streak=30于10:00:19'连续30分钟全源失败,报警退出'(iFinD errorcode=-1010, 腾讯实时NoneType)后无恢复; "
        "18:34:32收盘段重启(观察池=20260820\\\\zt_pool.csv 79只)→18:34:36 iFinD login rc=0→连续段启动→收盘退出; "
        "19:09:09晚间段(观察池=20260821\\\\zt_pool.csv 54只)→19:09:17 iFinD login rc=0→连续段启动→收盘退出; "
        "pipeline.lock=20260824 19:09:02(晚间launcher写入, 非盘中时间戳); "
        "盘中/报警_20260824.jsonl 今日不存在(今日hb-a/hb-d未留痕, 本心跳为今日首条报警); "
        "交易日校验: sentiment.core.calendar模块仍缺失(同8-13~8-21先例), 依周一历法+盘中管道早段尝试运行+晚间launcher活跃按正常交易日处理"
    ),
    "disposition": (
        "只报警禁决策: 无pulse新鲜度(文件不存在, 全天断更远超10分钟红线)、无当日实时行情 → "
        "①B级防守无对象(最新留档8-21 warboard: account持仓0/现金100%/n_pos=0, 无炸板/回撤可守, 题材批量跳水无从核验); "
        "②A级trigger无预案可依(今日无playbook, 8/21预案神奇制药600613为昨日预案禁跨日引用; sells无留档); "
        "③C级预案外进攻禁止(无数据无从核验, 写即编造违反铁律①零编造); "
        "④14:45深场B备料无当日行情无从做起; "
        "已写临盘决断_20260824_1430.json(ALARM_ONLY留证, 无fills); 无A/B/C级动作, 心跳hb-e无动作"
    ),
    "suggest": (
        "人工排查: 取数链同族故障第9日(8-13起): iFinD实时errorcode=-1010持续+腾讯实时NoneType→早段streak=30报警退出后盘中无恢复, "
        "需确认launcher盘中常驻/定时机制为何9日未跑通盘中实时段; "
        "恢复后补pulse.json+realtime_ticks.jsonl方可执行14:30/14:57心跳实质决策与14:45深场B备料; "
        "修复sentiment.core.calendar模块缺失(连续9日)或改用留档日历trading_calendar.py"
    ),
}
ok = append_dedup(os.path.join(BASE, "盘中", f"报警_{TDAY}.jsonl"), rec, keys="session")
print("APPEND_RESULT:", "written" if ok else "dup_skipped")
