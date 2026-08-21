# -*- coding: utf-8 -*-
"""hb-a 09:40 开盘博弈段心跳哨兵·报警留档 (2026-08-20) —— 只记录真实观测事实, 断更禁决策"""
import os, json, time

BASE = r"D:/股票数据/市场数据"
AF = os.path.join(BASE, "盘中", "报警_20260820.jsonl")
ts = time.strftime("%Y-%m-%d %H:%M:%S")

detail = ("心跳hb-a(0940开盘博弈段)链路断更(同8-13/8-14/8-17/8-18同源族第7日): 盘中/20260820/ 目录09:14创建后至今为空"
          "(pulse.json/warboard.json/执行流水.jsonl/临盘决断 全MISSING); launcher.log今日段 09:43:12~09:47:13 iFinD实时"
          "errorcode=-1010 + 腾讯实时NoneType异常, 取数失败streak=13→17(09:47:13), 实时链全断; 断更自09:14:32(pipeline.lock)"
          "起>32分钟远超10分钟红线; warboard.json今日引擎仍错位写盘中/20260819/warboard.json(mtime 08-20 09:25, 内容=0819晚间"
          "复盘重建 stage=C防守空仓/仓位≤2成/account持仓0现金100%, 6张已触发卡[金健米业/罗普斯金/艾艾精工/尚太科技/金能科技/"
          "上纬新材/我爱我家/华锦股份等]均等题材确认, checks.now全null=数据死无承接结论), 连续错位族同8-18写20260817/8-17写"
          "20260814; 交易日校验: sentiment.core.calendar模块缺失不可执行(同8-13~8-18先例), 依pipeline.lock=20260820 09:14:32"
          "+周四历法+管道实际启动按正常交易日处理, 留档日历trading_calendar尾=20260819(今日未入bars与断更一致)")

disposition = ("只报警禁决策: 无pulse新鲜度(文件不存在, 断更>32分钟远超10分钟红线)、无当日行情数据 → "
               "①B级防守无对象(account持仓0无炸板/回撤可守, 关注池题材批量跳水无从核验); "
               "②A级预案trigger(8-19卡金健米业600127等[已触发·等题材确认]含6+只)需实时tick核验承接+开盘价滑点, 断更禁执行; "
               "③C级预案外进攻禁止(无数据无从核验, 写即编造违反铁律①零编造, 同hb-a 8-18先例); "
               "未写临盘决断_20260820_0940.json(无触发依据); 无A/B/C级动作, 心跳hb-a无动作")

suggest = ("人工排查腾讯/iFinD实时取数链(同族报警第7日: 8-13/8-14/8-17/8-18/8-19/8-20); 恢复后补pulse.json+realtime_ticks.jsonl"
           "方可执行09:40开盘博弈段承接复核补跑及后续心跳; 修复warboard引擎目录硬编码错位(8-20仍写20260819目录, 连续错位族: "
           "8-14写20260813/8-17写20260814/8-18写20260817/8-20写20260819); 修复sentiment.core.calendar模块或改用留档日历")

row = {"ts": ts, "session": "hb-a", "level": "ALARM", "type": "data_stale", "scope": "intraday_chain",
       "detail": detail, "disposition": disposition, "suggest": suggest}

with open(AF, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("APPENDED:", ts, "| rows now:", sum(1 for _ in open(AF, encoding="utf-8")))
