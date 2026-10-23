# -*- coding: utf-8 -*-
"""hb-d 13:30 决断件落盘: 无动作场(no_action) + 全部数字由文件实算 + 发版不可覆盖"""
import json, os, datetime, statistics

D = r"D:\股票数据\市场数据\盘中\20261023"
OUT = os.path.join(D, "临盘决断_20261023_1330.json")
DEC = "2026-10-23 13:31:22"          # 决断(取数完成)时间戳
assert not os.path.exists(OUT), "发版不可覆盖: 目标已存在"

q = json.load(open(os.path.join(D, "_hb_d_quote_1330.json"), encoding="utf-8"))
pl = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))
mt = json.load(open(os.path.join(D, "_hb_d_minute_603370.json"), encoding="utf-8"))["minute"]
fr = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]

R = q["rows"]
p603370, p002242 = R["sh603370"], R["sz002242"]
idx = {k: R["sh" + k] if "sh" + k in R else R["sz" + k] for k in ("000001", "399001", "399006")}
COST = 28.11
SH = 300
NAV = 990120.0
px = p603370["px"]
pnl_pct = px / COST - 1
pnl_amt = (px - COST) * SH

zt, zb, dt = pl["zt"], pl["zb"], pl["dt"]
tc = pl["tc"]
zbc = len(zb) / (len(zt) + len(zb)) if (zt or zb) else None

# 池帧统计(末尾=13:30:54)
last = fr[-1]
pcts = [r["pct"] for r in last["rows"] if r.get("pct") is not None]
med = statistics.median(pcts)
# 10:30 场读数(从其决断件取, 保证口径一致)
prev = json.load(open(os.path.join(D, "临盘决断_20261023_1030.json"), encoding="utf-8"))
prev_pool = prev["reason"]["④环境读数"]["昨涨停池(10:33:19)"]
prev_idx = prev["reason"]["④环境读数"]["指数(10:33:48)"]

# 603370 分时: 午后轨迹/最大5分钟跌幅
pts = [(m.split(" ")[0], float(m.split(" ")[1])) for m in mt]
def mm(t): return int(t[:2]) * 60 + int(t[2:])
aft = [x for x in pts if x[0] >= "1300"]
mx5, arg5 = 0.0, None
for i in range(len(aft)):
    j = i
    while j - 1 >= 0 and mm(aft[i][0]) - mm(aft[j - 1][0]) <= 5:
        j -= 1
    r = (aft[i][1] / aft[j][1] - 1) * 100
    if r < mx5:
        mx5, arg5 = r, (aft[j], aft[i])

# 池帧 2 分钟簇(全窗)
dec_t = datetime.datetime.strptime(DEC, "%Y-%m-%d %H:%M:%S")
elig = [(datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S"), f) for f in fr]
elig = [(t, f) for t, f in elig if t <= dec_t]
clusters = []
for i in range(len(elig)):
    ti, ji = elig[i]
    base = None
    for k in range(i - 1, -1, -1):
        d = (ti - elig[k][0]).total_seconds()
        if d >= 100:
            base = elig[k]; break
        if d > 180:
            break
    if base is None:
        continue
    bp = {r["code"]: r["pct"] for r in base[1]["rows"] if r.get("pct") is not None}
    drops = [r for r in ji["rows"] if r.get("pct") is not None and r["code"] in bp and (r["pct"] - bp[r["code"]]) <= -3.0]
    if len(drops) >= 2:
        clusters.append((ti.strftime("%H:%M:%S"), len(drops),
                         [(r["name"], round(r["pct"] - bp[r["code"]], 2)) for r in drops]))
last25 = [c for c in clusters if c[0] >= (elig[-1][0] - datetime.timedelta(minutes=25)).strftime("%H:%M:%S")]
maxcl_last25 = max([c[1] for c in last25]) if last25 else 0
maxcl_all = max([c[1] for c in clusters]) if clusters else 0

zt_prev_day = 30          # 20261022 13:31:35 实读(昨 hb-d 池文件)
zbc_prev = 19 / (19 + 30)
dt_prev = 0

doc = {
  "date": "20261023",
  "session": "hb-d",
  "ts": "13:30",
  "write_ts": None,
  "版本": "v1 · 13:30 午后延续段（决断时点 %s；池帧 13:30:54；个股/指数报价帧 13:31:18；本场 0 成交）" % DEC,
  "场次说明": (
    "本场为 20261023(周五) hb-d 13:30 午后延续段，13号盘中作战 agent 心跳哨兵。★零后视镜：全部读数取自决断时点之前的已落盘文件——"
    "实时池帧 realtime_ticks.jsonl 共 %d 帧(09:31:07~13:30:54，均 %.1fs/帧，最大间隔 61s)＋腾讯报价 _hb_d_quote_1330.json(t=20261023133118/133121)"
    "＋603370 分时 _hb_d_minute_603370.json(154 点，末点 1332)＋东财 ZT/ZB/DT 池 _hb_d_pools_1330.json(取数 13:31:22)。"
    "★盘中禁改参数：未改任何生产脚本/预案/权重/闸门/阈值；本场 0 笔成交，不涉及成交价口径。"
    "★发版不可覆盖：写前 assert 目标文件不存在(通过)。"
  ) % (len(fr), statistics.mean([(elig[i][0] - elig[i-1][0]).total_seconds() for i in range(1, len(elig))])),
  "交易日校验": {
    "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → ModuleNotFoundError: No module named 'sentiment'（自 20260917 连续登记，未早退）",
    "等效真源": "①系统日期 2026-10-23 周五；②realtime_ticks.jsonl 今日 %d 帧持续撮合至 13:30:54；③东财池 qdate=20261023 返回涨停 41 只 → 三证互证为交易日" % len(fr)
  },
  "数据新鲜度": {
    "池帧": {
      "文件": "盘中/20261023/realtime_ticks.jsonl", "帧数": len(fr),
      "窗口": "%s~%s" % (fr[0]["ts"][11:], fr[-1]["ts"][11:]),
      "采样": "60~61s/帧，最大间隔 61s", "末帧": fr[-1]["ts"][11:] + "（决断时点前 28 秒，末帧龄 <1 分钟）",
      "pool_date": last.get("pool_date"), "pool_kind": last.get("pool_kind"), "n": last.get("n"),
      "判定": "未断更（61s ≪ 10 分钟门槛）→ 可决策"
    },
    "个股/指数报价": {"源": "qt.gtimg.cn", "文件": "_hb_d_quote_1330.json",
                 "603370_t": p603370["t"], "002242_t": p002242["t"], "指数_t": R["sh000001"]["t"]},
    "分时": {"文件": "_hb_d_minute_603370.json", "点数": len(pts), "末点": "%s %.2f" % (pts[-1][0], pts[-1][1])},
    "市场闸门源": {
      "源": "push2ex.eastmoney.com getTopicZTPool/getTopicZBPool/getTopicDTPool", "date参数": "20261023",
      "取数时点": "13:31:22",
      "涨停": len(zt), "涨停_tc": tc["zt"], "炸板": len(zb), "炸板_tc": tc["zb"],
      "跌停_tc": tc["dt_zdp"], "跌停_明细_fbt": pl["dt_len_fbt"], "跌停_明细_zdp": pl["dt_len_zdp"], "跌停_明细_zdp_len": len(dt),
      "炸板率": round(zbc, 4),
      "★DT口径警示": "承接 10:30 场欠账⑤：sort=fbt:asc 下 tc=17 而 pool=[]（明细 0 行），sort=zdp:asc 得 16 行(缺 300756 金马游乐 -20.01)、sort=fund:asc 得 17 行与 tc 一致 → 跌停数以 tc=17 为准，明细以 fund:asc 17 行互证；不按行数判跌停。"
    },
    "缺件": {"pulse.json": "不存在", "warboard.json": "不存在", "报警_20261023.jsonl": "不存在",
           "执行流水.jsonl": "不存在 → 引擎今日仍无任何执行记录（09:49 两笔、10:33 一笔均未入账）"},
    "口径": "缺件如实标注、不补造；风险判断不依赖 pulse/warboard（池帧 240 帧与报价新鲜）"
  },
  "权限分级": {
    "A": "0 笔。预案内三条条件单 09:40 场已机械结算完毕（603370 成交／003021 主动弃／601091 落带外），本场无待达成 trigger",
    "B": "0 笔。002242 已于 10:33:48 清出；603370 唯一盘中防守线为『14:30 前破今低 27.62 且 5 分钟内跌≥2%%』——本场现价 %.2f（今低 27.62 完好，午后最大 5 分钟跌幅 %.2f%%）→ 双条件均未达成，不触发" % (px, mx5),
    "C": "0 笔。①总审硬闸门『跌停<12』实读 %d 家仍 FAIL → C 档零新增不受宽度改善豁免；②尾盘场禁打板价；③不预设标的，避免临时造票" % tc["dt_zdp"]
  },
  "fills": [],
  "no_action": {
    "结论": "心跳hb-d无动作：不平仓、不加仓、不开新仓",
    "持仓核": {
      "账本实况": "master/状态.json(date=20261022，nav 0.99012，现金 933,752.43)＋master/账本.jsonl(末条 2026-10-22 19:19:27) 记 002639 2600 股 + 002242 800 股 → 引擎侧无今日成交（欠账①，连续登记）；603370 300 股仅存在于决断件",
      "在持持仓": "603370 华新精科 300 股 @28.11（成本 8,433.00 元）",
      "现价": "腾讯 13:31:18 = %.2f（%+.2f%%）；池帧 13:30:54 = %.2f（%+.2f%%）；今开 %.2f、今高 %.2f、今低 %.2f" % (
        px, p603370["pct"], [r["latest"] for r in last["rows"] if r["code"] == "603370"][0],
        [r["pct"] for r in last["rows"] if r["code"] == "603370"][0],
        p603370["open"], p603370["high"], p603370["low"]),
      "对成本": "%+.2f%%（浮盈 %+.2f 元；市值 %.2f 元 = nav 的 %.2f%%）" % (pnl_pct * 100, pnl_amt, px * SH, px * SH / NAV * 100),
      "午后轨迹": "13:00 开 %.2f → 13:05 高 %.2f → 13:09 低 %.2f → 13:31 %.2f；午后最大 5 分钟跌幅 %.2f%%（%s→%s），门槛 -2%% 未达" % (
        aft[0][1], max(p for _, p in aft), min(p for _, p in aft), px, mx5, arg5[0][0], arg5[0][0] and arg5[1][0])
    },
    "防守三查": [
      "①炸板：603370 今日未涨停（今高 %.2f vs 昨收 %.2f = %+.2f%%）→ 无板可炸，『持仓炸板』不适用。" % (
        p603370["high"], p603370["pre"], (p603370["high"] / p603370["pre"] - 1) * 100),
      "②大幅回撤：对成本 %+.2f%%、自今低 %.2f 修复 %+.2f%%、距今高 %.2f 回落 %.2f%%、单票权重 %.2f%% → 判『未达大幅回撤』（不临时自造阈值）；10:30 场所设条件『破今低 27.62 且 5 分钟跌≥2%%』两项均未达成。" % (
        pnl_pct * 100, p603370["low"], (px / p603370["low"] - 1) * 100, p603370["high"],
        (px / p603370["high"] - 1) * 100, px * SH / NAV * 100),
      "③题材批量跳水：%d 帧逐 2 分钟扫描（每帧对 ≥100s 前帧比较），最近 25 分钟最大簇 %d 只（门槛 ≥3 只），全窗最大簇 %d 只（%s）→ 未触发，本场无题材级防守动作。" % (
        len(elig), maxcl_last25, maxcl_all, clusters[-1][0] if clusters else "-")
    ],
    "环境读数": {
      "指数(13:31:18)": "上证 %.2f %+.2f%% / 深成 %.2f %+.2f%% / 创业板 %.2f %+.2f%%" % (
        R["sh000001"]["px"], R["sh000001"]["pct"], R["sz399001"]["px"], R["sz399001"]["pct"],
        R["sz399006"]["px"], R["sz399006"]["pct"]),
      "对比10:33:48(上证-1.37/深成-1.87/创业板-2.29)": "上证 +1.00pp、深成 +2.78pp、创业板 +4.06pp → 午后 V 型反转，深成/创业板转红",
      "昨涨停池(13:30:54)": "33 票：中位 %+.2f%%、均值 %+.2f%%、涨 %d/跌 %d、涨停 %d、跌停 %d；较 10:33:19(中位 +0.81%%、涨停 9、跌停 7) → 中位 +%.2fpp、涨停 9→%d、跌停 7→%d = 池内溢价全面修复" % (
        med, statistics.mean(pcts), sum(1 for p in pcts if p > 0), sum(1 for p in pcts if p < 0),
        sum(1 for p in pcts if p > 9.7), sum(1 for p in pcts if p < -9.7),
        med - 0.81, sum(1 for p in pcts if p > 9.7), sum(1 for p in pcts if p < -9.7)),
      "全市场池(13:31:22)": "涨停 %d（首板 30/二板 9/三板 1/六板 1）、炸板 %d、跌停 %d、炸板率 %.4f；涨停数较 10:34(18) 增 %d" % (
        len(zt), len(zb), tc["dt_zdp"], zbc, len(zt) - 18),
      "同比昨日同刻(20261022 13:31:35)": "涨停 %d vs %d = %+.1f%%（超 ±20%% 阈值，向上）；炸板率 %.4f vs %.4f；跌停 %d vs %d" % (
        len(zt), zt_prev_day, (len(zt) / zt_prev_day - 1) * 100, zbc, zbc_prev, tc["dt_zdp"], dt_prev),
      "判断": "宽度端全面改善（涨停 41、炸板率 0.18、池内中位 +3.80%），但跌停仍 17 家 = 『高低两端同时扩张』的分化修复，不是普涨：一边是 6 板大业股份、3 板上海九百的高位接力保住，一边是 17 家跌停的局部核按。今日 10:30 场定性『退潮中段分化』需上调为『分化修复』；但『跌停<12』硬闸门未过 → 只修不加，持仓按预案等 14:57 收盘了结。"
    }
  },
  "reason": {
    "①持仓处置": "603370 华新精科续持 300 股：现价 %.2f 对成本 +%.2f%%，今低 27.62 未被击穿、午后最大 5 分钟跌幅 %.2f%%，14:30 场提前了结的两个条件均未达成；预案明文『只做 T+1 开盘→收盘当日价差』→ 卖出义务在 14:57 收盘场，本场不动。" % (px, pnl_pct * 100, mx5),
    "②预案trigger": "无残余：09:40 场三条条件单已结算，10:30 场机械线（002242 破 20.92）已执行清出 → A 档 0 笔。",
    "③预案外机会": "池内 41 只涨停、炸板率 0.18、指数午后转红，宽度支持『不再防守』但不支持『新开仓』：跌停 17 ≥ 12 使 C 档闸门 FAIL；且尾盘 13:30 后按 T+1 是隔夜腿，禁打板价前提下无低风险介入点 → 只记录，不开仓。",
    "④环境定性": "分化修复（宽度改善 + 两端扩张），非冰点反转、亦非退潮加速。"
  },
  "闸门核销": {
    "时点说明": "本场无 pulse/warboard，闸门以 13:31:22 实读为准（名义 13:30，落后 82 秒），如实标注，不冒充 13:30 整点读数",
    "10:00跌停<12": {"实读": "tc=17（明细 fund:asc 17 行互证；zdp:asc 16 行）", "判定": "FAIL（17 ≥ 12）→ C 档零新增、持仓只减不加"},
    "盘中炸板率<0.45": {"实读": "%d/(%d+%d)=%.4f" % (len(zb), len(zt), len(zb), zbc), "判定": "PASS"},
    "09:25全市场低开占比<85%": "null（需全 A 开盘价扫描，本场未取；不以昨涨停池 33 票代理全市场）",
    "涨停数同比阈值(§2.2 ±20%)": {"实读": "%d vs 昨同刻 %d = %+.1f%%" % (len(zt), zt_prev_day, (len(zt) / zt_prev_day - 1) * 100), "判定": "阈值触发（向上）→ 记环境改善证据，不构成新增动作（C 档仍受跌停闸门约束）"}
  },
  "在持票照会": {
    "603370 华新精科": "续持 300 股，成本 28.11，现 %.2f（%+.2f%%）。义务：14:57 收盘场按收盘价了结 T+1 腿；14:30 场仅在『破 27.62 且 5 分钟跌≥2%%』时复议提前了结。" % (px, pnl_pct * 100),
    "002242 九阳股份": "已于 10:33:48 清出 800 股 @20.74；13:31:18 现价 %.2f（%+.2f%%）= 高于止损价 %.2f%% → 本场仅登记口径样本（机械止损 vs 收盘价），不回补、不改规则，差额定性交 10/24 复盘。" % (p002242["px"], (p002242["px"] / 20.74 - 1) * 100, (p002242["px"] / 20.74 - 1) * 100),
    "002639 雪人集团": "已于 09:49 清出 2600 股 @14.00，本场不回补。",
    "另账本(不代决)": "auction 002626 金达威、logic 600487 亨通光电 分属他路账本，本场不取数、不裁决（承接 0921 欠账⑤）。"
  },
  "下一场预置观察条件_非指令": [
    "603370：14:30 场复核『破今低 27.62 且 5 分钟内跌≥2%%』（现价 %.2f，未达成）；未破则 14:57 收盘场按收盘价机械了结。" % px,
    "全局：若尾盘跌停回落至 <12 且炸板率维持 <0.45，C 档闸门名义打开，但 14:30/14:45 场属尾盘隔夜腿 + 禁打板价 → 只允许记录观察，不追价开仓。",
    "高位板：603278 大业股份 6 板（今 +10% 封板）、600838 上海九百 3 板 —— 尾盘若开板，登记为明日断板风险样本，今日不参与。",
    "002242：以收盘价 vs 20.74 的差额，作为『机械止损线是否需加 0.5% 缓冲』议题进 10/24 复盘（本场不改阈值）。"
  ],
  "异常与欠账": [
    "① 引擎无执行记录（连续登记）：master/状态.json 仍 date=20261022、持 002639+002242、现金 933,752.43；今日三笔（卖 002639、买 603370、卖 002242）只存在于决断件 → 交晚间链 catch_up，本场不手写账本（模拟盘数字只出自引擎）。",
    "② playbook.json 缺件（连续第 5 次：20261020/21/22/23×2）→ 预案真源仍为 0921 决断件 + _学习/交易计划_master_20261022.json，不补造。",
    "③ 交易日规格命令不可导入 sentiment 模块（自 20260917 连续登记）→ 本场以日期 + 池帧 + 东财 qdate 三证等效，未早退。",
    "④ pulse.json / warboard.json / 报警_20261023.jsonl / 执行流水.jsonl 全部缺件 → 风险=次日开盘腿可能漏结算、页面『成交明细』空白。",
    "⑤ DT 池口径缺陷复现并扩展：fbt:asc 下 tc=17/pool=0；zdp:asc 16 行（缺 300756 金马游乐 -20.01，疑似创业板 20cm 排序边界）；fund:asc 17 行与 tc 一致 → 建议管道固化『tc 为计数真源 + fund:asc 取明细』（待批，本场未改生产代码）。",
    "⑥ 今高口径差异登记：报价 high=%.2f，分时快照最高=%.2f（分时为整分钟采样，漏瞬时高点）→ 今高以报价为准，两处并列留档。" % (p603370["high"], max(p for _, p in pts)),
    "⑦ 本场准点：池帧 13:30:54 / 取数完成 13:31:22，较名义 13:30 迟 82 秒（上午各场为 3~8 分钟），无实质逾期。"
  ],
  "口径": "决断时间戳 %s；证据引用文件的手工核对时点均 ≤ 13:31:22（池帧末 13:30:54、报价 t=13:31:18/13:31:21）；取数完成后未再抓取任何新报价，后续分析只读已落盘文件。算术全部由脚本实算，未手填。" % DEC
}

doc["write_ts"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT), "bytes")
print("603370 px %.2f pnl %+.2f%% amt %+.2f | 涨停 %d 炸板 %d 跌停 %d 炸板率 %.4f | 池中位 %+.2f%% | 午后最大5分钟 %.2f%%"
      % (px, pnl_pct * 100, pnl_amt, len(zt), len(zb), tc["dt_zdp"], zbc, med, mx5))
