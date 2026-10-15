# -*- coding: utf-8 -*-
"""深场B(14:45) 发出版writer。只写本场产物: 临盘决断_20261015_1445.json(新建, 禁覆盖) + 报警_20261015.jsonl(append)。
不碰任何生产脚本/账本/净值/次日卖出指令。"""
import json, os, statistics as st
from datetime import datetime

BASE = r"D:\股票数据\市场数据"
D = "20261015"
DAY = os.path.join(BASE, "盘中", D)
TICKS = os.path.join(DAY, "realtime_ticks.jsonl")
CUT = "2026-10-15 14:45:00"
OUT = os.path.join(DAY, "临盘决断_%s_1445.json" % D)
ALARM = os.path.join(DAY, "报警_%s.jsonl" % D)
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

assert not os.path.exists(OUT), "发出版已存在, 禁覆盖: " + OUT

# ---------- 帧读取 ----------
frames = [json.loads(l) for l in open(TICKS, encoding="utf-8") if l.strip()]
legal = [f for f in frames if f["ts"] <= CUT]
excluded = [f["ts"] for f in frames if f["ts"] > CUT]
last = legal[-1]
rows = {x["code"]: x for x in last["rows"]}

def ztp(x):
    lim = 0.20 if x["code"].startswith(("300", "301", "688")) else 0.10
    return round(x["preClose"] * (1 + lim), 2)

def snap(f):
    return {y["code"]: y for y in f["rows"]}

sealed = [c for c, x in rows.items() if x["latest"] >= ztp(x) - 1e-9]
touched = [c for c, x in rows.items() if x["high"] >= ztp(x) - 1e-9]
broken = [c for c in touched if c not in sealed]
dtl = [c for c, x in rows.items() if x["pct"] <= -9.8]
pcts = [x["pct"] for x in rows.values()]

def nm(c):
    return rows[c]["name"]

# 持仓留档(≤14:45) —— 三票均不在实时池, 取 hb-e 14:35 直取留档(唯一 ≤14:45 的持仓行情)
hb = json.load(open(os.path.join(DAY, "_hb_e_quote.json"), encoding="utf-8"))
hd = json.load(open(os.path.join(DAY, "_hb_d_quote.json"), encoding="utf-8"))
for _c, _q in hb.items():          # hb-e 留档键名为 last, 归一为 latest
    if "latest" not in _q and "last" in _q:
        _q["latest"] = _q["last"]

def hold(code, cost, sh, kou):
    q = hb[code]
    r = dict(code=code, name=q["name"], shares=sh, cost_px=cost, kou=kou,
             行情戳=q["time"], latest=q["latest"], preClose=q["preClose"], open=q["open"],
             high=q["high"], low=q["low"], bid1=q["bid1"], ask1=q["ask1"],
             turnover_pct=q["turnover_pct"],
             pct=round((q["latest"] / q["preClose"] - 1) * 100, 2),
             相对成本pct=round((q["latest"] / cost - 1) * 100, 2),
             浮动盈亏_元=round((q["latest"] - cost) * sh, 2),
             市值_元=round(q["latest"] * sh, 2),
             gap_vs_preClose_pct=round((q["open"] / q["preClose"] - 1) * 100, 2),
             行情源="http://qt.gtimg.cn/q=sz000011,sh600693,sh605577 (hb-e 14:35 直取留档, ≤14:45 合法窗口内唯一持仓行情)",
             相对1336留档pct变动_pp=round((q["latest"] / hd["quotes"][code]["preClose"] - 1) * 100 - hd["quotes"][code]["pct"], 2))
    return r

h11 = hold("000011", 10.11, 5900, "第七账账本口径(在持)")
h693 = hold("600693", 12.4124, 4000, "10/14 09:25 A级承接口径(账本未回写)")
h577 = hold("605577", 17.6576, 2200, "10/14 09:25 A级承接口径(账本未回写)")

# ---------- 执行对账(引擎) ----------
ledger_state = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/state.json"), encoding="utf-8"))
ledger_nav = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/净值.json"), encoding="utf-8"))
ledger_sell = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/次日卖出指令.json"), encoding="utf-8"))

# ---------- playbook ----------
pb = json.load(open(os.path.join(BASE, "盘中/20261014/playbook.json"), encoding="utf-8"))
sells = pb["sells"]
buys = pb["buys"]

def gap(code):
    x = rows.get(code)
    if not x:  # 用 09:25 引擎留档
        return None
    return round((x["open"] / x["preClose"] - 1) * 100, 2)

miss = []
for b in buys:
    c = b["code"]; x = rows.get(c)
    if not x:
        miss.append({"code": c, "name": b["name"], "status": "非池内, 无法核定"})
        continue
    g = round((x["open"] / x["preClose"] - 1) * 100, 2)
    rng = b["trigger"]["open_range"]
    lo, hi = rng.get("min_gap"), rng.get("max_gap")
    inband = (lo is None or g >= lo) and (hi is None or g <= hi)
    yizi = x["open"] >= ztp(x) - 1e-9
    miss.append({"code": c, "name": b["name"], "顺位权重%": b["weight_pct"], "source": b["source"],
                 "开盘": x["open"], "gap%": g, "闸门": "[%s,%s]" % (lo, hi), "落带": inband,
                 "一字": yizi, "锁定帧pct%": x["pct"],
                 "现价/开盘pct%": round((x["latest"] / x["open"] - 1) * 100, 2),
                 "判定": ("落带但本日未成交(preread 09:21 场 provider 故障失败→无执行)" if inband and not yizi
                          else ("弃单(闸门拒)+今封板" if not inband else "弃单(一字/闸门)"))})

result = {
 "date": D, "session": "deepb", "ts": "14:45", "version": "v1",
 "决断时间戳": "2026-10-15 14:45:00 CST", "write_ts": NOW,
 "场次说明": "A股盘中作战·深场B(14:45尾盘场, 13号盘中作战agent)。任务=①尾盘卖预案执行(预案单sells中 leg=close / take_zt 触发→写本文件) ②持仓逐票表态 ③执行对账(引擎已执行什么) ④预收盘第一手判断。权限: A级=预案内自由 / B级=预案外防守(写触发证据) / C级=预案外进攻(本场禁)。铁律: 零后视镜(仅用 ts≤14:45:00 的已留档数据)/断更>10分钟只报警禁决策/发出版不可覆盖/盘中禁改参数/止损类规则只认预案单显式声明。",
 "job身份": {
   "job": "0509b31150e9 · sentiment-intraday-deepb", "cron": "45 14 * * 1-5",
   "enabled": True, "model": "deepseek-flash",
   "execution_id": "6d08e8c45296435f9fdf1e9cffc7a9a5",
   "scheduled_instant": "2026-10-15 14:45:00 CST (06:45:00 UTC)",
   "claimed_at": "2026-10-15T14:45:54.772539+08:00", "started_at": "2026-10-15T14:45:55.158214+08:00",
   "kind": "on_time", "lateness_seconds": 54.5,
   "真源": "profiles/a/cron/jobs.json + executions.db (非自报)"
 },
 "交易日校验": {
   "结论": True, "判定": "2026-10-15 周四 = 交易日(盘中运行中)",
   "等价证据": "①realtime_ticks.jsonl 本日 %d 帧(%s ~ %s, 采样 60~62s 连续缺帧0); ②末帧 pool_date=20261014 / pool_kind=zt_pool / pool_stale=False; ③盘中/pipeline.lock=『20261015 19808 09:14:55』本日上锁; ④launcher.log 本日段(第11651行起) 连续 tick 源=腾讯 n=36 至 14:48:04, 0 错误。"
              % (len(frames), frames[0]["ts"], frames[-1]["ts"]),
   "契约缺口": "任务书指定的 `sentiment.core.calendar` 接口本机不可导入(承本机链路漂移); _学习/_交易日历.json 末5日=20261008/09/12/13/14 未含当日(当日bar收盘后入库) → 两条契约口径均不能直接判当日, 改用上述盘中实时等价证据。"
 },
 "数据新鲜度": {
   "契约源_pulse.json": "盘中/%s/pulse.json **全库0命中(契约路径未实现, 连续多日同型)** → 以 realtime_ticks.jsonl 顶替断更核验并明示口径替换" % D,
   "替代源": "盘中/%s/realtime_ticks.jsonl" % D,
   "读档帧数": len(frames), "合法帧(ts<=14:45:00)": len(legal),
   "首帧": legal[0]["ts"], "末合法帧": last["ts"],
   "断更判定": "末合法帧 %s 距决断时点 14:45:00 约 %d 秒 << 600 秒红线; 相邻间隔 min60s/max62s, >120s空档 0 次 → **新鲜, 允许决策**"
               % (last["ts"], int((datetime.strptime(CUT, "%Y-%m-%d %H:%M:%S") - datetime.strptime(last["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds())),
   "排除帧(ts>14:45:00, 仅列示未作决策输入)": excluded,
   "持仓票行情_新鲜度警告": "三只在持票(000011/600693/605577)**均不在实时池**(36票×%d合法帧 0命中) → 唯一 ≤14:45 的持仓行情 = hb-e 14:35:03~06 腾讯直取留档(距决断约 9分54秒, 逼近 10分钟红线) → 本场按『辅助读数、非主源』使用并 WARN 登记; **不在此刻补拉行情**(拉取时刻>14:45:00, 属零后视镜违规, 宁可标注口径缺口)",
   "池口径": "src=腾讯(单源) / pool_date=20261014 / pool_kind=zt_pool / pool_stale=False / 每帧 n=36 → 口径=『10/14 涨停股(36只) 今日承接』, **非当日全市场口径**"
 },
 "载体缺失登记": [
   "盘中/%s/warboard.json **缺失**(今日未生成; 1014/1013/0930/0928/0923 均有) → 本场以 盘中/20261014/warboard.json(mtime 2026-10-15 14:31, date=20261014, 系素材日文件被回写) + 本场实时帧替代, 缺口登记入账(承 hb-e 20261015_1430 同款登记)" % D,
   "盘中/%s/执行流水.jsonl **缺失**(全库检索无该文件名载体, 契约未实现)" % D,
   "盘中/%s/报警_%s.jsonl 读时**不存在** → 本场新建并追加(见交付对账)" % (D, D),
   "盘中/%s/playbook.json **不存在** → 预案真源取素材日 盘中/20261014/playbook.json(date=20261014, mtime 2026-10-14 21:42, 早于决断时刻)" % D
 ],
 "warboard照会": {
   "源": "盘中/20261014/warboard.json (date=20261014, ts=『2026-10-14 晚间复盘重建』, mtime 2026-10-15 14:31 ≤ 决断时刻 → 合法输入)",
   "judgment": {"档位": "C防守(维持)", "pos_band": "≤2成", "执行清单": "不放开"},
   "checks5项": "now 全为 null, 待明晨09:25竞价场回应",
   "池况(pulse)": {"涨停": 36, "跌停": 11, "炸板": 24, "炸板率": 40.0, "最高连板": 4}
 },
 "在持票照会": {
   "账": "第七账 _学习/_模拟盘/盘中作战/ — state.json(mtime 2026-10-15 14:31): positions=[000011 深物业A 5900@10.11, cost 59649.59, buy_date 20261003], cash=940350.41; 净值.json(date=20261015): nav=999999.41 / pos_val=59649.0 / n_pos=1; 次日卖出指令.json=[]  ← 三件 mtime 14:31 ≤ 14:45:00, 合法输入",
   "双口径": "①账本口径 = 仅 000011; ②决断记录口径 = +600693/605577(10/14 09:25 A级承接, 账本未回写, 承 10/14 四场 + 今日 hb-d/hb-e 登记)",
   "持仓": [h11, h693, h577],
   "合计_决断记录口径": {
     "三票市值_元": round(h11["市值_元"] + h693["市值_元"] + h577["市值_元"], 2),
     "占nav_pct": round((h11["市值_元"] + h693["市值_元"] + h577["市值_元"]) / ledger_nav["nav"] * 100, 2),
     "浮盈合计_元": round(h11["浮动盈亏_元"] + h693["浮动盈亏_元"] + h577["浮动盈亏_元"], 2),
     "行情时点": "2026-10-15 14:35:03~06 (hb-e 直取留档)"
   },
   "逐票表态": [
     {"code": "000011", "name": "深物业A", "口径": "账本在持", "今日表现": "前收10.81 → 低开10.67(-1.30%) → 冲高11.60(日高,+7.31%) → 14:35:06留档10.88(+0.65%); 日低10.48",
      "浮盈": "+4543.00 元 (相对成本 +7.62%)", "明日计划": "playbook『持有』腿: 低开/平开且收盘≥开盘→全仓续持, 次日再评",
      "持有或卖出理由": "playbook.sells[0] 三腿: ①减仓腿=开盘gap≥+3% → 实际 gap **-1.30% 未达**; ②清仓腿=收盘<当日开盘(10.67) → **判定时点未到(收盘15:00)**; 现价10.88>开盘10.67 → 当前落『持有』; ③stop_pct=null。**本场无卖腿触发**",
      "风险备注": "自今日高点11.60回撤 -6.21%; 13:36→14:35 相对前收 -2.22pp(11.12→10.88)"},
     {"code": "600693", "name": "东百集团", "口径": "决断记录口径(账本未回写)", "今日表现": "前收12.19 → **一字跌停 10.97(-10.01%), 开=高=低=10.97, bid1=0.00(无买盘), 换手0.68%**, 14:35:03 仍封死未开板",
      "浮盈": "-5769.60 元 (相对成本 -11.62%)", "明日计划": "若次日开板→开板即处置候选; 若持续封死→记『未成交』转次日卖出指令(引擎口径)",
      "持有或卖出理由": "**无卖出腿**(playbook.sells 仅 000011) → 无显式卖据; 且**物理不可成交**(跌停封死 bid1=0) → 不处置、不写 fill"},
     {"code": "605577", "name": "龙版传媒", "口径": "决断记录口径(账本未回写)", "今日表现": "前收18.95 → **跌停开 17.06(-9.97%,=日低)** → 冲高19.50(日高,+2.90%) → 回落; 14:35:04留档 17.54(-7.44%)",
      "浮盈": "-258.72 元 (相对成本 -0.67%)", "明日计划": "深场B备候选(承 hb-e): 若续弱则次日处置; 但须先有显式卖通道方可落地",
      "持有或卖出理由": "**无卖出腿**(playbook.sells 无该票) + 铁律『止损类规则只认预案单显式声明』 → hb-e 登记的 B级通道A(大幅回撤: 1h-4.00pp/相对成本由+3.47%转-0.67%/自日高-10.05%)**不构成卖据** → 不处置"}
   ]
 },
 "A级_预案内": {
   "许可": True, "成交笔数": 0, "买入金额_元": 0.0,
   "说明": "零 A 级动作(合法空集, 非漏写)。依据: playbook.buys=3只(000601/002343/000823), 全为『明晨(20261015)9:25 gap 一次性判定』条件单, **无盘中/尾盘段二次 trigger 语义**; 至尾盘段均已过判定时点 → 本场无可触发项(见错失登记)。sells 见『尾盘卖预案执行』。",
   "余下时段可触发项": "无。"
 },
 "B级_防守": {
   "触发": False,
   "门槛原文": "①持仓炸板/大幅回撤/题材批量跳水(≥3只2分钟内-3%)→B级防守(写触发证据)",
   "通道A_持仓回撤": "**处置受限, 不成立(可行动层面)**: 605577 大幅回撤事实成立(见下), 但铁律『止损类规则只认预案单显式声明』+ playbook.sells 无该票 → **无卖据**; 000011 相对成本仍 +7.62%(为正)且高于开盘 → 未达回撤门槛; 600693 跌停封死, 状态未变。",
   "通道B_题材批量跳水": "**不成立**: 全窗(09:31:04~%s, 全部≤120s帧对)扫描达阈(≥3只/≤-3pp批)批数 = **0**; 末40分钟最弱单帧 -5.20pp(002029七匹狼·单票)、末5分钟 -1.02pp、末2分钟 -1.19pp, 达阈只数均 0。" % last["ts"],
   "通道C_持仓炸板": "持仓无炸板(三票均非池内; 600693 为跌停非炸板)。池内炸板3只(非持仓, 仅记录): 603258电魂网络(+5.94, 13:35:49封→尾盘由封转炸)、603533掌阅科技(-2.11)、601811新华文轩(+9.46, 摸25.58板未封)。",
   "客观读数": {"605577_14:35留档": h577["latest"], "605577_pct": h577["pct"], "605577_相对成本pct": h577["相对成本pct"], "605577_自今日高回撤pct": round((h577["latest"] / h577["high"] - 1) * 100, 2),
                "000011_14:35留档": h11["latest"], "000011_相对成本pct": h11["相对成本pct"]},
   "处置": "**本场不发起任何成交**。理由: ①无『卖腿/止损』显式声明(playbook.sells 仅 000011 且条件未达); ②现行结构无任何卖通道(见『尾盘卖预案执行』通道前置); ③铁律『盘中禁改参数』+ 零编造 → 不虚构成交、不写 fill。违者可动性, 全部登记为证据并移交次日。"
 },
 "C级_预案外": {
   "许可": False,
   "依据": "盘中/20261014/warboard.json#judgment=『C防守(维持)·pos_band ≤2成』+『执行清单一律不放开』+ 铁律『盘中禁改参数』→ 预案外进攻(含带帽 C 级)禁行。",
   "本场动作": "零 C 级动作、零带帽单; 不把池内异动(尾盘封板5只/个股逆势)折算成新机会。"
 },
 "尾盘卖预案执行": {
   "预案真源": "盘中/20261014/playbook.json (date=20261014, route=master, v2, mtime 2026-10-14 21:42 早于决断时刻)",
   "sells清单": "n=1: {code:000011 深物业A, shares:5900, ref_px:10.11, action:『逢强减仓·走弱清仓(T+1=20261015盘口表态)』, trigger:{减仓:gap≥+3%, 清仓:收盘<开盘, 持有:低开且收盘≥开盘}, intraday:{stop_pct:null}, leg:**null**, take_zt:**null**}",
   "leg_close_take_zt声明": "**无** —— ①全清单 leg 均为 null, **无任何 leg=close**; ②take_zt 均 null, **无止盈腿启用**; ③stop_pct 亦 null(止损类默认关闭, 明示『改用收盘<开盘的形态条件』); ④次日卖出指令.json=[]; ⑤盘中/20261015/playbook.json 不存在(无第二卖出源)。",
   "腿逐一判定": [
     {"腿": "减仓", "条件": "20261015 开盘 gap≥+3%", "实测": "开盘 10.67 vs 前收 10.81 = gap **-1.30%**", "判定": "**未触发**"},
     {"腿": "清仓", "条件": "20261015 收盘 < 当日开盘价 10.67", "实测": "判定时点 14:45 **收盘价不可得**(15:00方定); 末次合法留档 14:35:06=10.88 > 10.67", "判定": "**未到判定时点/截至留档未成立**"},
     {"腿": "持有", "条件": "低开/平开 且 收盘≥开盘", "实测": "低开(-1.30%)成立; 截至14:35留档 10.88>10.67", "判定": "**当前落『持有』**"}
   ],
   "可卖标的": "0 只 —— ①000011 卖腿未触发(且不在观测池, px_exec 不可得); ②600693/605577 无任何卖出腿声明; ③hb-e 备料候选非预案声明、不构成卖据。",
   "结果": "**未执行(合法空集), fills=[]**; 未设任何卖价带、**未调用 fills 接口**, px_exec(决断后下一tick留档价 ± 滑点0.10%)与『跌停封死顺延』条款**均不适用**。",
   "通道前置(承 hb-e, 第7次登记)": "现行结构下**无任何已运行卖通道**: ①盘中回应引擎-每日收盘14:57(jobs.json id=04066045b634) **enabled=false** → 引擎内唯一生成『次日卖出指令』并做持仓断板/跌停检查的场次未运行(真源已复核: enabled=False); ②引擎卖出仅在 0925/1000 消费 次日卖出指令.json(=[]); ③playbook.json 的 sells 字段**无任何模块消费方** ⇒ 本账实质『**只买不卖**』, 一切 B 级防守在结构上不可落地。"
 },
 "fills": [],
 "fills_口径": "本场零成交(合法空集, 非漏写)。三只在持票中 600693 物理不可成交(跌停封死 bid1=0.00); 605577/000011 无任何已触发卖腿; C级禁行。若发生成交: px_exec = 决断后下一tick留档价 ± 滑点0.10%(买不利向上/卖不利向下), 买必带整手 qty, 跌停封死顺延。",
 "no_action": True,
 "执行对账_引擎已执行": {
   "契约件": "盘中/20261015/执行流水.jsonl **缺失**(全库0命中) → 无流水可对账, 改以引擎自留档 + 账本互证。",
   "引擎自留档": "判断流水.jsonl(mtime 2026-10-15 14:31, 总1658行); 本日块=3个: (08-15 09:25/0925, 16条)、(08-15 10:00/1000, 16条)、(08-15 14:30/1430, 16条) —— **ts字段读作『08-15』= 月份退化(应 10-15), 承前场登记**, 以数值交叉核验定日(如『000601 低开-2.05%』『603968 大跌-9.5%』与本日盘中实测逐项一致)。16条**全为档位判定**(档位/闸门/题材/个股/等), **无任何成交字段**。",
   "引擎本日已执行": "**零真实成交**(无 buy、无 sell): state.json positions 仍 1 条(000011)、n_pos=1、cash=940350.41 未变(940350.41 = 1000000 - 59649.59 单笔成本, 无第二笔扣款); 次日卖出指令.json=[] 未变。",
   "运行真源(executions.db)": "本日盘中链: pipeline 09:14 completed / **preread 09:21 failed(Provider unresponsive)** / 竞价引擎09:25 completed / **hb-a 09:40 failed** / 开盘引擎10:00 completed / **hb-b 10:30 failed** / **hb-c 11:00 failed** / hb-d 13:30 completed / hb-e 14:30 completed / 尾盘引擎14:30 completed / deepb 14:45 running(本场)。",
   "结论": "本日引擎侧 3 个 no_agent 场次(09:25/10:00/14:30)全部 completed 但**只记档位判定、不落成交**; 4 个 agent 场次(preread/hb-a/hb-b/hb-c)因 **provider 连续无响应**失败 → **当日无任何计划单被执行**。"
 },
 "错失登记": miss,
 "错失结论": "playbook.buys 3只中, **000601/000823 落带(条件满足)但当日未成交**(preread 09:21 场 provider 故障失败 → 无人执行 9:25 gap 判定与承接); 002343 因 gap +10.0% 越 +5% 上限被闸门拒单(设计内 miss)。落带未执行两票截至锁定帧: 000601 -2.93%(相对开盘 -0.9%)、000823 +4.85%(相对开盘 +2.43%) → **一miss避损、一miss错失**, 非一致方向。",
 "预收盘第一手判断": {
   "口径": "20261014 涨停池 36 只『今日承接』, 锁 %s; **不外推全市场**" % last["ts"],
   "池截面": {"中位": round(st.median(pcts), 2), "均值": round(sum(pcts) / len(pcts), 3),
              "最低": min(pcts), "最高": max(pcts),
              "涨/跌": "%d/%d" % (sum(1 for p in pcts if p > 0), sum(1 for p in pcts if p < 0)),
              "≥+5%": sum(1 for p in pcts if p >= 5), "≥+3%": sum(1 for p in pcts if p >= 3),
              "≤-5%": sum(1 for p in pcts if p <= -5), "≤-3%": sum(1 for p in pcts if p <= -3),
              "封板": len(sealed), "炸板": len(broken), "跌停": len(dtl)},
   "封板名单": [c + nm(c) + "%+.2f" % rows[c]["pct"] for c in sealed],
   "炸板名单": [c + nm(c) + "%+.2f" % rows[c]["pct"] for c in broken],
   "跌停名单": [c + nm(c) + "%+.2f" % rows[c]["pct"] for c in dtl],
   "日内轨迹_中位": {"09:40": -1.98, "10:00": -0.28, "10:30": -1.75, "11:00": -2.44, "11:30": -2.59,
                     "13:00": -2.58, "13:30": -2.71, "14:00": -3.32, "14:15": -3.63, "14:30": -3.88, "14:44": -4.22},
   "情绪定性": "**单边阴跌·尾盘无修复** —— 中位自 10:00 的 -0.28 一路下行至 14:44 的 -4.22(较13:30 -1.51pp); 封板 6→5、跌停 6→8(13:30起)、炸板 2→3; 尾盘未见≥3只同步跳水(0批)亦无修复 → 退潮加深, 与 warboard『C防守(维持)』同向。",
   "主线": "**无单线成簇主线**(最大线仅3只): AI短剧(3只:1封1炸, 002343封+10.00为线内最强/603533炸/603598-5.52) / 出版(3只:0封1炸, 601811+9.46摸板未封/603096-1.91断板/601858-0.46) / 机器人(3只:0封, 中位-9.99全崩) / 储能(3只:0封, 中位-7.56) / 冰雪经济(2只:1封1跌停) / 覆铜板(2只:0封但中位+3.49=全池最强线)。",
   "龙头身位": "**高度3只4板守住2只**: 002343慈文传媒(4板·封+10.00)、002696百洋股份(4板·一字封+10.05) 守住; 603096新经典(4板·**断板** -1.91, 日高+4.9%未触板)。3板 603968醋化股份 **跌停 -10.00**(炸板4次)。⇒ 高度端『封2断1杀1』, 高位分化但天花板(4板)未塌。",
   "龙头票错失对照": "002343(playbook第2顺位·theme)今**一字封+10.0%** → 因 gap +10.0% 越 +5% 闸门被弃单(设计内 miss); 000823(第4顺位·logic)今 +4.85% 落带未执行。"
 },
 "明日预案要点": [
   "环境: 退潮加深(池内封印5/跌停8/中位-4.22, 13:30: 封6/跌停8/中位-2.71) → 明日维持 **C防守(≤2成)**, 不放开执行清单; warboard#judgment.checks 5项 now=null 待明晨09:25竞价场回应。",
   "持仓处置优先级: 600693(开板即处置候选/持续封死转次日) ≥ 605577(续弱则处置候选, 但须先建卖通道) > 000011(playbook『持有』守, 收盘<开盘才清仓)。",
   "**明日开盘前必办**: ①恢复/建卖出通道(14:57场 enabled=false + sells 无消费方); ②000011 持仓可观测性缺口(不在池)处置; ③本日 000601/000823 落带未执行的『非成交』口径结算。",
   "watch 复核(1014): 300299富春股份 今日 -6.98%(弱, 与前场判弱一致) / 001216华瓷股份 +4.00%(逆势) / 601858中国科传 -0.46% — 明日复核净买与封板质量。",
   "provider 故障闭环: 本日 4 场(preread/hb-a/hb-b/hb-c) 因 provider 连续无响应失败, 须核明是模型侧(deepseek-flash)还是本机链路, 并给出补跑/兜底方案(否则 9:25 gap 条件单将反复『落带未执行』)。"
 ],
 "后视镜边界声明": "本文件一切读数取自 ①realtime_ticks.jsonl 帧 ts ≤ %s(末合法帧) 与 ②hb-e 14:35:03~06 腾讯直取留档(≤14:45:00); 决断时点固定为 2026-10-15 14:45:00。realtime_ticks 中 ts>14:45:00 的 %d 帧(见数据新鲜度·排除帧)已排除于决策输入。**本文件不含任何 14:45:00 之后的信息, 也不含收盘口径数据。**" % (last["ts"], len(excluded)),
 "异常与欠账": [
   "①provider 故障(本日新增): preread 09:21 / hb-a 09:40 / hb-b 10:30 / hb-c 11:00 四场 agent 均因『Provider has been unresponsive (no response received) for 5~6 consecutive stale attempts』失败 → 当日计划单 000601/000823 落带未执行(错失口径)。",
   "②账本未回写: 600693/605577 仍为决断记录口径, 第七账仅 000011(第7次登记, 承 10/14)。",
   "③卖通道缺失: 14:57收盘场 enabled=false + playbook.sells 无消费方 ⇒ 只买不卖(第7次登记)。",
   "④载体缺失: 盘中/20261015/ 无 warboard.json、无 执行流水.jsonl、无 pulse.json(契约未实现)。",
   "⑤持仓不可观测: 三只在持票均不在实时池(36票0命中) → 持仓级尾盘风控结构上不可判定(第8次登记)。",
   "⑥判断流水 ts 退化: 本日块读作『08-15』(应 10-15), 需修 ts 源方可机械检索(承前场)。",
   "⑦hb-e 备料描述有误(本场更正): hb-e 20261015_1430 记『playbook buys 4只(000601/002343/000823/603968)』, 经复核 **playbook.buys 实为 3 只(000601/002343/000823), 无 603968**(603968 属 auction 路观察票, 未进顶层 buys) → 以本文件为准(发往他件不覆盖)。"
 ],
 "口径": "五路定序/段落标序/A-C分治 按技能规则; 本场为盘中作战尾盘段, 一切结论基于真实留档数据(零编造); 给判断不给指令; 报告对用户=参考, 非操盘指令。",
 "report": "深场B(14:45尾盘)：池内封印5/炸板3/跌停8、中位-4.22(13:30 -2.71)退潮加深; 尾盘卖预案 **零对象**——playbook.sells 仅 000011 且 leg/take_zt 均 null, 减仓腿 gap -1.30% 未达、清仓腿待收盘, 故 fills=[] 零成交; 持仓逐票: 000011 10.88(+7.62%相对成本)落『持有』, 600693 一字跌停封死不可成交(-11.62%), 605577 17.54(-0.67%, 无卖腿不处置); 对账=引擎本日零成交(账本未变), 4个agent场次因provider故障失败致000601/000823落带未执行; 高度4板守2断1, 无单线成簇主线。"
}

os.makedirs(DAY, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT), "bytes")

# ---------- 报警 append-only ----------
alarms = [
 {"ts": NOW, "date": D, "session": "deepb", "level": "ALARM",
  "code": "provider_outage_4_sessions_missed",
  "msg": "本日 preread09:21/hb-a09:40/hb-b10:30/hb-c11:00 四场agent因Provider连续无响应失败; 当日计划单 000601/000823 落带未执行(错失口径, 一miss避损一miss错失)。执行真源=executions.db。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "ALARM",
  "code": "sell_channel_absent_playbook_sells_unconsumed",
  "msg": "第7次: 盘中回应引擎-每日收盘14:57(id=04066045b634) enabled=false + playbook.sells 无任何消费方 ⇒ 只买不卖, 一切B级防守结构上不可落地。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "ALARM",
  "code": "hold_tickets_unobservable_no_intraday_risk",
  "msg": "第8次: 在持票 000011/600693/605577 均不在实时池(36票×%d合法帧0命中) ⇒ 持仓级尾盘风控不可判定; 唯一≤14:45行情=hb-e 14:35直取留档(距决断9分54秒, 逼近10分钟红线)。" % len(legal)},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "a_level_fills_still_not_written_back",
  "msg": "第7次: 10/14 09:25 两笔A级承接(600693 4000@12.4124 / 605577 2200@17.6576)仍未回写第七账; 执行流水.jsonl 全库不存在。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "contract_files_missing_and_ts_degeneration",
  "msg": "第7次: pulse.json / warboard.json / 执行流水.jsonl 三项契约缺件; 判断流水 ts 本日块读作『08-15』(应10-15)退化; 日历契约 sentiment.core.calendar 不可导入。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "hb_e_payload_miscount_corrected",
  "msg": "本场更正: hb-e 20261015_1430 记『playbook buys 4只(含603968)』, 实为 3 只(000601/002343/000823); 603968 属auction观察票, 未进顶层buys。发往他件不覆盖, 以本场为准。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "tail_sell_plan_no_trigger_zero_fill",
  "msg": "尾盘卖预案零对象: playbook.sells 仅000011, leg=null/take_zt=null; 减仓腿gap-1.30%未达、清仓腿待收盘(14:35留档10.88>开盘10.67) ⇒ fills=[] 合法空集。"}
]
exist = os.path.exists(ALARM)
with open(ALARM, "a", encoding="utf-8", newline="\n") as f:
    for a in alarms:
        f.write(json.dumps(a, ensure_ascii=False) + "\n")
print("ALARM", ("appended" if exist else "created"), ALARM, "n=", len(alarms))
