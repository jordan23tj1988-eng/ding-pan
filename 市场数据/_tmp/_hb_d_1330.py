# -*- coding: utf-8 -*-
"""hb-d 心跳 13:30午后延续段:warboard留证 + 报警追加(只报警禁决策)"""
import json, os, sys, datetime

BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
from _jsonl_append import append_dedup

# --- 1. warboard 关键字段留证 ---
wb_path = os.path.join(BASE, "盘中", "20260817", "warboard.json")  # 引擎错位写目录(8-18 mtime)
wb = {}
if os.path.isfile(wb_path):
    try:
        wb = json.load(open(wb_path, encoding="utf-8"))
    except Exception as e:
        wb = {"read_err": str(e)}
print("WARBOARD_PATH:", wb_path, "mtime:", os.path.getmtime(wb_path))
for k in ("date", "stage", "judgment"):
    if k in wb:
        print(k, "=>", str(wb[k])[:300])
acct = wb.get("account") or wb.get("账户") or {}
print("ACCOUNT:", json.dumps(acct, ensure_ascii=False)[:300])
npos = 0
for kk in ("n_pos", "npos", "持仓数"):
    if kk in acct:
        npos = acct[kk]
print("N_POS:", npos)

# --- 2. 今日目录/文件状态 ---
tdir = os.path.join(BASE, "盘中", "20260818")
files = os.listdir(tdir) if os.path.isdir(tdir) else []
print("TODAY_DIR_FILES:", files)
print("PULSE_EXISTS:", os.path.isfile(os.path.join(tdir, "pulse.json")))
print("FLOW_EXISTS:", os.path.isfile(os.path.join(tdir, "执行流水.jsonl")))
print("WARBOARD_TODAY_EXISTS:", os.path.isfile(os.path.join(tdir, "warboard.json")))
lock_p = os.path.join(BASE, "盘中", "pipeline.lock")
print("LOCK:", os.path.isfile(lock_p), os.path.getmtime(lock_p) if os.path.isfile(lock_p) else None)
pa_p = os.path.join(tdir, "pipeline_alarm.jsonl")
if os.path.isfile(pa_p):
    print("PIPE_ALARM_MTIME:", os.path.getmtime(pa_p))
    print("PIPE_ALARM_TAIL:", open(pa_p, encoding="utf-8").read().strip()[-160:])

# --- 3. 追加 hb-d 报警记录(去重: session=hb-d) ---
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
rec = {
    "ts": now,
    "session": "hb-d",
    "level": "ALARM",
    "type": "data_stale",
    "scope": "intraday_chain",
    "detail": (
        "心跳hb-d(1330午后延续段)链路断更持续(同8-13/8-14/8-17/8-18同源族第6日): "
        "盘中/20260818/ 仍仅pipeline_alarm.jsonl(mtime 10:00:24 all_source_dead, "
        "launcher.log尾=10:00:24连续30分钟全源失败报警退出后无恢复); "
        "pulse.json/执行流水.jsonl/临盘决断 MISSING(全盘搜索pulse.json 0命中); "
        "warboard.json今日仍错位写盘中/20260817/warboard.json(mtime 08-18 10:00:38引擎二次重写, "
        "date=20260817晚复盘 stage=B中性仓位≤2成, account持仓0/现金100%, 优先成交:共进股份[触发·等题材确认]); "
        "断更自09:14:55(lock)起>4小时远超10分钟红线; 腾讯实时NoneType+iFinD errorcode=-1010 全源失败; "
        "交易日校验: sentiment.core.calendar模块缺失不可执行(同8-13~8-18先例), "
        "依pipeline.lock=20260818 09:14:55+周二历法+管道实际启动按正常交易日处理, "
        "留档日历trading_calendar尾=20260817(今日未入bars与断更一致)"
    ),
    "disposition": (
        "只报警禁决策: 无pulse新鲜度(文件不存在, 断更>4小时远超10分钟红线)、无当日行情数据 → "
        "①B级防守无对象(账户0持仓/现金100%无炸板/回撤可守, 题材批量跳水无从核验); "
        "②A级预案trigger(共进股份[等题材确认])需实时tick核验承接+开盘价滑点, 断更禁执行; "
        "③C级预案外进攻禁止(无数据无从核验, 写即编造违反铁律①零编造, 同hb-a/hb-b/hb-c先例); "
        "未写临盘决断_20260818_1330.json(无触发依据); 无A/B/C级动作, 心跳hb-d无动作"
    ),
    "suggest": (
        "人工排查腾讯/iFinD实时取数链(同族报警第6日: 8-13/8-14/8-17/8-18); "
        "恢复后补pulse.json+realtime_ticks.jsonl方可执行13:30承接复核补跑及14:30/14:57心跳; "
        "修复warboard引擎目录硬编码错位(8-18仍写20260817目录, 连续错位族: 8-14写20260813/8-17写20260814/8-18写20260817); "
        "修复sentiment.core.calendar模块或改用留档日历"
    ),
}
ok = append_dedup(os.path.join(BASE, "盘中", "报警_20260818.jsonl"), rec, keys="session")
print("APPEND_RESULT:", "written" if ok else "dup_skipped")
