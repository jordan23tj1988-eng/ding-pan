# -*- coding: utf-8 -*-
"""hb-c 11:00 心跳哨兵·报警留档 (2026-08-18) —— 只记录真实观测事实"""
import os, json, time

BASE = r"D:/股票数据/市场数据"
AF = os.path.join(BASE, "盘中", "报警_20260818.jsonl")
ts = time.strftime("%Y-%m-%d %H:%M:%S")

detail = ("心跳hb-c(1100半日收尾段)链路断更持续(同8-13/8-14/8-17/8-18同源族第6日): 盘中/20260818/ 仍仅pipeline_alarm.jsonl"
          "(mtime 10:00:24 all_source_dead, launcher.log尾=10:00:24连续30分钟全源失败报警退出后无恢复); "
          "pulse.json/执行流水.jsonl/临盘决断 MISSING(全盘搜索pulse.json 0命中, realtime_ticks仅8-13旧档); "
          "warboard.json今日仍错位写盘中/20260817/warboard.json(mtime 08-18 10:00:38引擎二次重写, date=20260817晚复盘 "
          "stage=B中性仓位≤2成, account持仓0/现金100%, responses仅09:25场摘要且checks.now全null=数据死无承接结论, "
          "优先成交:共进股份[触发·等题材确认]); 断更自09:14:55(lock)起>110分钟远超10分钟红线; "
          "腾讯实时NoneType+iFinD errorcode=-1010 全源失败; "
          "交易日校验: sentiment.core.calendar模块缺失不可执行(同8-13~8-17先例), 依pipeline.lock=20260818 09:14:55+周二历法+管道实际启动按正常交易日处理, "
          "留档日历trading_calendar尾=20260817(今日未入bars与断更一致)")

disposition = ("只报警禁决策: 无pulse新鲜度(文件不存在, 断更>110分钟远超10分钟红线)、无当日行情数据 → "
               "①B级防守无对象(账户0持仓无炸板/回撤可守, 题材批量跳水无从核验); "
               "②A级预案trigger(共进股份等6只[等题材确认])需实时tick核验承接+开盘价滑点, 断更禁执行; "
               "③C级预案外进攻禁止(无数据无从核验, 写即编造违反铁律①零编造, 同hb-a/hb-b先例); "
               "未写临盘决断_20260818_1100.json(无触发依据); 无A/B/C级动作, 心跳hb-c无动作")

suggest = ("人工排查腾讯/iFinD实时取数链(同族报警第6日: 8-13/8-14/8-17/8-18); 恢复后补pulse.json+realtime_ticks.jsonl方可执行"
           "11:00半日收尾段承接复核补跑及14:30/14:57心跳; 修复warboard引擎目录硬编码错位(8-18仍写20260817目录, 连续错位族: "
           "8-14写20260813/8-17写20260814/8-18写20260817); 修复sentiment.core.calendar模块或改用留档日历")

row = {"ts": ts, "session": "hb-c", "level": "ALARM", "type": "data_stale", "scope": "intraday_chain",
       "detail": detail, "disposition": disposition, "suggest": suggest}

with open(AF, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("APPENDED:", ts, "| rows now:", sum(1 for _ in open(AF, encoding="utf-8")))
