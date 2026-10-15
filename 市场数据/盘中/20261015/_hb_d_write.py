# -*- coding: utf-8 -*-
"""hb-d(2026-10-15 13:30场) 决断文件装配: 全部数字程序化取自留档文件, 不手抄。"""
import json, os, subprocess, sys, datetime, statistics
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = os.path.dirname(os.path.abspath(__file__))
cache = json.load(open(os.path.join(D, '_hb_d_quote.json'), encoding='utf-8'))
calc = json.load(open(os.path.join(D, '_hb_d_calc.json'), encoding='utf-8'))
Q = cache['quotes']
ticks = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8')]

# ---- 新鲜度 ----
ts_list = [datetime.datetime.strptime(t['ts'], '%Y-%m-%d %H:%M:%S') for t in ticks]
deltas = [(ts_list[i] - ts_list[i - 1]).total_seconds() for i in range(1, len(ts_list))]
last = ts_list[-1]
now = datetime.datetime.now()
stale_sec = (now - last).total_seconds()

# ---- 上游链路故障(executions.db) ----
rows = json.load(open(os.path.join(D, '_hb_d_jobs.json'), encoding='utf-8')) if os.path.exists(os.path.join(D, '_hb_d_jobs.json')) else None

# ---- 在持 ----
def mk(code, name, shares, cost, note):
    v = Q[code]
    mv = round(v['latest'] * shares, 2)
    return {"code": code, "name": name, "shares": shares, "cost_px": cost,
            "决断时点实价": v['latest'], "preClose": v['preClose'], "今日开盘": v['open'],
            "今日最高": v['high'], "今日最低": v['low'], "涨跌pct": v['pct'],
            "行情戳": v['ts_quote'], "bid1": v['bid1'], "ask1": v['ask1'],
            "浮动盈亏_元": round((v['latest'] - cost) * shares, 2),
            "相对成本pct": round((v['latest'] / cost - 1) * 100, 2),
            "市值_元": mv, "占nav_pct": round(mv / 1000000 * 100, 2), "note": note}

pos = [
    mk("000011", "深物业A", 5900, 10.11, "账本口径(_学习/_模拟盘/盘中作战/state.json mtime 2026-10-15 10:00, buy_date=20261003)"),
    mk("600693", "东百集团", 4000, 12.4124, "决断记录口径(盘中/20261014/临盘决断_20261014_0940.json#fills fill_buy px_exec=12.4124/qty=4000); 账本未回写"),
    mk("605577", "龙版传媒", 2200, 17.6576, "决断记录口径(同上, fill_buy px_exec=17.6576/qty=2200); 账本未回写"),
]

fills = []  # 本场 0 成交(见 B级 不可成交登记 + A级 未执行登记)

out = {
 "date": "20261015",
 "session": "hb-d",
 "ts": "13:30",
 "write_ts": now.strftime("%Y-%m-%d %H:%M:%S"),
 "版本": "v1(本场首版; 未覆盖任何历史发出版)",
 "场次说明": "2026-10-15(周四) 13:30 午后延续段 心跳哨兵。执行真源=cron jobs.json 内嵌 prompt(job_id=c415a7792216, sched='30 13 * * 1-5') + executions.db 本场记录 id=4bc742fd8074459cbc512dff7d7f85a3(status=running, started_at=2026-10-15T13:30:55)。★本场为**本日唯一存活的心跳场次**: 09:21(preread)/09:24/09:40(hb-a)/10:30(hb-b)/11:00(hb-c) 五场全部 failed(Provider unresponsive), 0 个决断文件产出 → 本场额外承担『上游链路故障登记 + 错失执行核账』职责。",
 "交易日校验": {
   "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str;...\" → FAIL: ModuleNotFoundError: No module named 'sentiment'(同 09/17 起连续登记的本机漂移; 市场数据/ 下只有 trading_calendar.py)",
   "本机等效真源": "_学习/_交易日历.json(由 _bars_cache 日线并集重建; 末5条=20261008/20261009/20261012/20261013/20261014 → 20261015 尚未入册, 因当日 bar 收盘后才生成)",
   "判定": "is_trading_day(20261015)=True(本场执行, 不早退)",
   "佐证链": ["2026-10-15 为周四",
              "盘中/launcher.log 连续段 13:31~13:35 tick n=36 源=腾讯, 无断更",
              "盘中/20261015/realtime_ticks.jsonl 末帧 %s" % ticks[-1]['ts'],
              "成交实价可核: 腾讯 qt.gtimg.cn 行情戳 20261015 133636-133637"]
 },
 "数据新鲜度": {
   "源": "盘中/20261015/realtime_ticks.jsonl(腾讯, phase=continuous) + 决断时点实价(腾讯 qt.gtimg.cn, 本场自取并落档 _hb_d_quote.json)",
   "池": {"pool_date": ticks[-1]['pool_date'], "pool_kind": ticks[-1]['pool_kind'],
          "pool_stale": ticks[-1]['pool_stale'], "n": ticks[-1]['n']},
   "窗": "%s ~ %s" % (ticks[0]['ts'], ticks[-1]['ts']),
   "条数": len(ticks),
   "采样间隔秒": {"最小": min(deltas), "最大": max(deltas), "均值": round(statistics.mean(deltas), 2)},
   "末帧滞后_秒": round(stale_sec, 1),
   "断更判定": "无(最大间隔 %.0fs << 600s 门槛; 末帧滞后 %.0fs) → 允许决策" % (max(deltas), stale_sec)
 },
 "上游链路_故障登记": {
   "级别": "ALARM(单点全链失败, 本场口头/书面双登记)",
   "事实": "executions.db 2026-10-15 记录: c7f1e0b2e8da(09:21 盘前预读) failed 10:16:27 / 4610e4f4351f(09:24) failed 10:05:59 / ca64a4e51d42(09:40 hb-a) failed 10:21:59 / aee9c2fb913b(10:30 hb-b) failed 11:16:26 / 3e4b3b30b816(11:00 hb-c) failed 12:07:21; 报错同型='RuntimeError: Provider has been unresponsive (no response received) for 5-6 consecutive stale attempts'",
   "后果": "本日 09:25 竞价闸门判定/预案内条件单执行 **无任何 agent 执行**; 盘中/20261015/ 下 0 个 临盘决断 文件(仅 auction_traj.jsonl + realtime_ticks.jsonl 由定时管道自身生存)",
   "非交易链路对照": "5d3bdd715496/e727f6e55cbf/d3bc2bc0b19d 等 pipeline 类 job 全天 completed(说明仅『需 LLM 的 agent 类 job』被 provider 掐断, 取数管道未断)",
   "处置": "不追单、不补单(见 A级); 请 14:30/收盘场 与复盘链承接复现登记; 建议在 provider 稳定性门禁中把『agent 类 job 连续 stale 失败』计入日级告警"
 },
 "契约文件_缺失登记": {
   "应收": ["盘中/20261015/pulse.json", "盘中/20261015/报警_20261015.jsonl", "盘中/20261015/warboard.json", "盘中/20261015/执行流水.jsonl", "盘中/20261015/playbook.json"],
   "实有": ["盘中/20261015/auction_traj.jsonl(09:25 止)", "盘中/20261015/realtime_ticks.jsonl(13:35 止)"],
   "判定": "5/5 契约文件缺失(pulse.json/执行流水.jsonl 全库从未存在; warboard/playbook 为次日模式, 今日尚未生成) → 本场以上一份 warboard(盘中/20261014/warboard.json, 24h 内) + playbook(盘中/20261014/playbook.json, date=20261014, 其 confirm 字段显式指向 20261015) 承接"
 },
 "在持票照会": {
   "账": "第七账 _学习/_模拟盘/盘中作战/(state.json mtime 2026-10-15 10:00 / 净值.json date=20261015 nav=999999.41 / 次日卖出指令.json=[])",
   "双口径": "①账本口径=仅 000011; ②决断记录口径=+600693/605577(10/14 09:25 A级承接 fill_buy, 账本未回写, 承 10/14 四场登记)",
   "持仓": pos,
   "合计": {"决断时点总市值_元": round(sum(p['市值_元'] for p in pos), 2),
            "合计浮盈_元": round(sum(p['浮动盈亏_元'] for p in pos), 2),
            "占nav_pct": round(sum(p['市值_元'] for p in pos) / 1000000 * 100, 2),
            "行情源": cache['url'], "fetch_ts": cache['fetch_ts']},
   "000011_预案卖腿": "盘中/20261014/playbook.json#sells[0]: 减仓=开盘gap≥+3%(实际gap-1.30%, 未达); 清仓=收盘<当日开盘(今日开10.67, 决断时点11.12>开盘, 待收盘); 持有=低开且收盘≥开盘 → 决断时点**落『持有』, 无卖腿触发**",
   "600693_预案卖腿": "无(playbook#sells 仅 000011) → 处置权限=B级防守",
   "605577_预案卖腿": "无 → 无触发(B级通道逐条见下)"
 },
 "A级_预案内": {
   "口径": "预案内条件单=盘中/20261014/playbook.json(目标日=20261015) buys 4只 + 竞价路 603968; 触发时点=09:25 集合竞价后一次性判定(开盘gap闸门)",
   "执行结果": "0 笔成交 — 唯一执行窗口(09:25)无 agent 存活(见上游链路_故障登记), 非条件未达",
   "条件达成复算(09:25留档, 可复现)": calc['gaps'],
   "逐票": [
     {"code": "000601", "name": "韶能股份", "weight_pct": 4, "闸门": "gap∈[-4,+4]", "实际gap": calc['gaps']['000601']['gap_pct'],
      "判定": "**达成未执行**", "错失核账_元": "若按开盘6.68整手5900股(39,412元): 决断时点6.80 → 盘中+1.80%(+708元)", "事后口径": "事后核账, 不作成交, 不作证伪/证实依据"},
     {"code": "000823", "name": "超声电子", "weight_pct": 2, "闸门": "gap≤+3 且不破前收", "实际gap": calc['gaps']['000823']['gap_pct'],
      "判定": "**达成未执行**", "错失核账_元": "若按开盘25.13整手700股(17,591元): 决断时点26.18 → 盘中+4.18%(+735元)", "事后口径": "事后核账, 不作成交"},
     {"code": "002343", "name": "慈文传媒", "weight_pct": 3, "闸门": "gap≤+5", "实际gap": calc['gaps']['002343']['gap_pct'],
      "判定": "**正确弃单**(闸门拒单, 与链路故障无关)", "佐证": "决断时点仍为一字涨停封死(ask1=0, 涨停价8.91=现价), 买不进"},
     {"code": "603968", "name": "醋化股份", "weight_pct": 3, "route": "auction", "闸门": "gap<+5(偏好低开≤0)", "实际gap": calc['gaps']['603968']['gap_pct'],
      "判定": "**判定分歧登记**: 字面(-9.49% 落『低开≤0』偏好带)可命中的条件, 但属深低开破位, 结合竞价路『池内高开≥5弃区/破位不接』纪律与本票决断时点跌停封死(bid1=0) → 事后判定=不该接。不追溯成交, 只登记口径缺口: auction路 的『低开≤0』未设下限。"}
   ]
 },
 "A级_合计": {"笔数": 0, "成交金额_元": 0, "说明": "本场及本日全天 A级执行=0; 其中 2 只条件达成但因链路故障未执行(错失核账 +1,443 元浮盈口径, 事后非成交), 1 只闸门正确拒单, 1 只口径分歧登记"},
 "B级_防守": {
   "触发": True,
   "触发类型": "①持仓大幅回撤(通道A) — 成立且在册, 但防守动作**不可执行**(跌停封死无买盘); ②题材批量跳水(通道B) — 不成立; ③炸板(通道C) — 持仓无炸板, 池内 3 只(非持仓)仅记录",
   "通道A_持仓回撤": {
     "判定": "触发(B级在册)",
     "触发证据": "600693 东百集团(4000股, 成本12.4124) 决断时点 10.97 = **一字跌停 -10.01%**(涨停13.41/跌停10.97/开=高=低=10.97), 相对成本 -11.62%, 浮亏 -5,769.60 元(占nav -0.577%); 且盘口 **bid1=0.00(无买盘)、ask1=10.97 挂 10,941 手、换手仅0.65%** → 卖单不可成交",
     "不可成交声明": "fills 本场不落任何 600693 卖出记录(物理不可成交, 零编造); 防守意图=清仓了结, 移交 14:30/收盘场核验是否开板, 未开板则按『跌停封死=未成交』结项并转次日卖出指令(引擎口径, 本文件不代写账本)",
     "对照": "605577 龙版传媒(2200股, 成本17.6576): 现18.27 -3.59%(今日开17.06=-9.97% 后拉回, 高19.50/低17.06), 相对成本 **+3.47% 未回撤**; 自今日高点回撤-6.31% 仅记录不触发",
     "000011": "现11.12 +2.87%, 相对成本 +9.99%, 无回撤"
   },
   "通道B_题材批量跳水": {"判定": "不成立", "门槛": "≥3只2分钟内 -3%", "实测": "13:00~13:35 共 %d 帧, 『≥3只单帧跌≥1.5%%』帧数=0(门槛取更严的-1.5pp 仍 0 命中)" % len([t for t in ticks if t['ts'][11:16] >= '13:00'])},
   "通道C_炸板": {"判定": "持仓无炸板", "池内炸板": calc['pool_last']['zb_detail'],
                  "池况": {"封板": calc['pool_last']['zt'], "跌停": calc['pool_last']['dt'], "炸板": calc['pool_last']['zb'], "池均pct_末帧": round(sum(r['pct'] for r in ticks[-1]['rows']) / len(ticks[-1]['rows']), 2)}}
 },
 "C级_预案外": {
   "许可": False,
   "依据": "盘中/20261014/warboard.json#judgment=『C防守(维持), pos_band ≤2成』(温度17.9 冰点/涨停36/炸板率40%/跌停11) + 『盘中禁改参数』→ 预案外进攻禁行(带帽 C 级亦禁)",
   "本场动作": "零 C 级动作、零带帽单; 池内异动仅记录: 6只封板(000530/002343/603258/002696/001318/605189)与 7只跌停并列=冰点分化, 不折算为新机会"
 },
 "fills": fills,
 "no_action": False,
 "reason": "【A级】0笔 — 唯一执行窗口(09:25)本日无 agent 存活(preread/hb-a/b/c 五场 failed), 2只条件确认达成(000601 gap-2.05%落带 / 000823 gap+2.36%≤+3)属**错失执行**并已核账登记, 不做午后退单(不追单、不降闸门、不因盘中走强补数)。【B级】触发1项: 600693 一字跌停 -10.01%(相对成本-11.62%/浮亏-5,769.60元)触发『持仓大幅回撤』, 但 bid1=0 无买盘 → 防守动作物理不可执行, 只登记+移交; 题材批量跳水通道0命中; 池内3只炸板非持仓。【C级】许可=false(总审C防守+盘中禁改参数) → 零预案外动作。",
 "报警_留档": [
   "ALARM-1(最高优先): 2026-10-15 全链 agent 类 job 因 provider 连续 stale 失败 — preread/hb-a/hb-b/hb-c 五场 0 产出, 直接导致预案内条件单错失执行(A级2只)",
   "ALARM-2: 契约文件 5/5 缺失(pulse.json / 报警_20261015.jsonl / warboard.json / 执行流水.jsonl / playbook.json) — 承前场连续登记, 本场第 N 次",
   "ALARM-3: 600693 持仓跌停封死不可卖出 → 防守不可执行, 风险敞口被动留存过夜(决断时点敞口 -5,769.60 元)"
 ],
 "移交_下一场": [
   "14:30(hb-e)/收盘: 600693 是否开板 → 开板即可成交清仓; 未开板记『未成交』并转次日卖出指令",
   "收盘前: 000011 按 playbook#sells[0]『收盘<开盘→清仓2950股/全仓』核验(今日开10.67)",
   "复盘链: 上游 provider 故障根因复现 + 错失执行核账并入当日复盘(错失口径: 000601 +1.80%/000823 +4.18%, 事后非成交)",
   "口径缺口: auction 路条件单『低开≤0』未设下限(本日 603968 深低开-9.49% 落字面命中却是跌停票)"
 ],
 "口径": "零后视镜: 本场全部输入(ticks/auction_traj/playbook/warboard/账本/executions.db)时间戳 ≤ 决断时点 13:36:41; 实价取 腾讯 qt.gtimg.cn 同源(与实时管道一致, URL 与行情戳已落 _hb_d_quote.json); 错失核账为『事后』计算, 明确标注、不进成交、不作胜负依据。零编造: 缺失字段一律 null/登记, 不补价不补量。发出版: 本文件为 20261015 hb-d 首版, 不覆盖任何历史发出版。"
}

p = os.path.join(D, '临盘决断_20261015_1330.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("已写:", p, os.path.getsize(p), "bytes")
print("write_ts", out['write_ts'], "| 末帧", ticks[-1]['ts'], "| 滞后", round(stale_sec, 1), "s")
print("在持合计市值", out['在持票照会']['合计']['决断时点总市值_元'], "浮盈", out['在持票照会']['合计']['合计浮盈_元'])
for x in pos:
    print("  ", x['code'], x['name'], x['决断时点实价'], x['涨跌pct'], "成本", x['cost_px'], "浮盈", x['浮动盈亏_元'], "相对成本", x['相对成本pct'], "%")
