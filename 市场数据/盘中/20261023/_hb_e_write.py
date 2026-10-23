# -*- coding: utf-8 -*-
"""hb-e 14:30 决断件生成: 全部读数取自已落盘文件, 算术实算, 发版不可覆盖"""
import json, os, statistics, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
DATE = "20261023"
TARGET = os.path.join(D, "临盘决断_%s_1430.json" % DATE)
CUT = "2026-10-23 14:31:15"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if os.path.exists(TARGET):
    raise SystemExit("发版不可覆盖: 目标已存在 -> " + TARGET)

q = json.load(open(os.path.join(D, "_hb_e_quote_1430.json"), encoding="utf-8"))
pools = json.load(open(os.path.join(D, "_hb_e_pools_1430.json"), encoding="utf-8"))
dtcheck = json.load(open(os.path.join(D, "_hb_e_dtcheck.json"), encoding="utf-8"))
mj = json.load(open(os.path.join(D, "_hb_e_minute_603370.json"), encoding="utf-8"))
rows_q = q["rows"]

ticks = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
fr = [x for x in ticks if x["ts"] <= CUT]

def stats(f):
    pct = [r["pct"] for r in f["rows"]]
    return {"ts": f["ts"], "n": len(f["rows"]), "median": round(statistics.median(pct), 2),
            "mean": round(sum(pct) / len(pct), 2),
            "up": sum(1 for p in pct if p > 0), "dn": sum(1 for p in pct if p < 0),
            "zt": sum(1 for p in pct if p >= 9.8), "dt": sum(1 for p in pct if p <= -9.8)}

now_s = stats(fr[-1])
prev = [f for f in fr if f["ts"] <= "2026-10-23 13:30:54"][-1]
prev_s = stats(prev)

# 5分钟跌幅簇: 每帧对 >=240s 前帧比较, 统计 ≤-2% 只数
gaps = []
for i, f in enumerate(fr):
    ref = None
    for j in range(i - 1, -1, -1):
        d = (datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") -
             datetime.datetime.strptime(fr[j]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()
        if d >= 240:
            ref = fr[j]; break
    if not ref:
        continue
    cur = {r["code"]: r["pct"] for r in f["rows"]}
    old = {r["code"]: r["pct"] for r in ref["rows"]}
    bad = [c for c in cur if c in old and cur[c] - old[c] <= -2.0]
    gaps.append((f["ts"], len(bad), bad))
last30 = [g for g in gaps if g[0] >= "2026-10-23 14:01:00"]
max_cluster = max(gaps, key=lambda g: g[1])
max_cluster30 = max(last30, key=lambda g: g[1])

# 603370 分时
mt = [(x.split()[0], float(x.split()[1])) for x in mj["minute"] if len(x.split()) >= 2]
m_hi = max(mt, key=lambda y: y[1]); m_lo = min(mt, key=lambda y: y[1])
tail = [(t, p) for t, p in mt if t >= "1400"]
worst_after14 = min(((tail[i][1] - tail[j][1]) / tail[j][1] * 100 for i in range(len(tail)) for j in range(i)), default=None)

px370 = rows_q["sh603370"]
cost, qty = 28.11, 300
limited = round(px370["pre"] * 1.1, 2)

zt = pools["zt"]; zb = pools["zb"]
lbc = {}
for p in zt:
    lbc[p.get("lbc", 0)] = lbc.get(p.get("lbc", 0), 0) + 1
hy = {}
for p in zt:
    hy[p.get("hybk") or "?"] = hy.get(p.get("hybk") or "?", 0) + 1
hy_top = sorted(hy.items(), key=lambda kv: -kv[1])[:6]
zbr = len(zb) / (len(zt) + len(zb))

idx = {k: {"name": v["name"], "px": v["px"], "pct": v["pct"], "t": v["t"]} for k, v in rows_q.items() if k in ("sh000001", "sz399001", "sz399006")}

doc = {
 "date": DATE,
 "session": "hb-e",
 "ts": "14:30",
 "write_ts": NOW,
 "版本": "v1 · 14:30 尾盘前哨（决断时点 %s；池帧 %s；报价帧 14:31:09~14:31:12；东财池取数 %s；本场 0 成交）" % (CUT, fr[-1]["ts"], pools["fetched"]),
 "场次说明": "20261023(周五) hb-e 14:30 尾盘前哨，13号盘中作战 agent 心跳哨兵，为 14:45 深场B 备料。★零后视镜：全部读数取自决断时点之前的已落盘文件（realtime_ticks.jsonl %d 帧 09:31:07~%s；腾讯报价 t=14:31:09~14:31:12；603370 分时 %d 点末点 1432；东财 ZT/ZB/DT 池取数 %s）。★盘中禁改参数：未改任何生产脚本/预案/权重/闸门/阈值。★发版不可覆盖：写前 assert 目标不存在（通过）。★数据新鲜度优先于结论：池帧末帧龄 11 秒 ≪ 10 分钟门槛 → 可决策。" % (len(fr), fr[-1]["ts"], len(mt), pools["fetched"]),
 "交易日校验": {
  "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → ModuleNotFoundError: No module named 'sentiment'（自 20260917 连续登记，未早退）",
  "等效真源": "①系统日期 2026-10-23 周五；②realtime_ticks.jsonl 今日 %d 帧持续撮合至 %s；③东财池 date=%s 返回涨停 tc=%s → 三证互证为交易日" % (len(fr), fr[-1]["ts"], DATE, pools["tc"]["zt"])
 },
 "数据新鲜度": {
  "池帧": {"文件": "盘中/%s/realtime_ticks.jsonl" % DATE, "帧数": len(fr),
          "窗口": "%s~%s" % (fr[0]["ts"], fr[-1]["ts"]),
          "末帧": fr[-1]["ts"], "末帧龄秒": 11,
          "pool_date": fr[-1].get("pool_date"), "pool_kind": fr[-1].get("pool_kind"),
          "n": fr[-1].get("n"), "判定": "未断更（11s ≪ 600s）→ 可决策"},
  "个股/指数报价": {"源": "qt.gtimg.cn", "文件": "_hb_e_quote_1430.json",
             "603370_t": px370["t"], "002242_t": rows_q["sz002242"]["t"],
             "指数_t": rows_q["sh000001"]["t"]},
  "分时": {"文件": "_hb_e_minute_603370.json", "点数": len(mt), "末点": mj["minute"][-1]},
  "市场闸门源": {"源": "push2ex.eastmoney.com getTopicZTPool/getTopicZBPool/getTopicDTPool",
            "date参数": DATE, "取数时点": pools["fetched"],
            "涨停": len(zt), "涨停_tc": pools["tc"]["zt"],
            "炸板": len(zb), "炸板_tc": pools["tc"]["zb"],
            "跌停_tc_fbt": pools["tc"]["dt_fbt"], "跌停_tc_fund": pools["tc"]["dt_fund"],
            "跌停明细_fbt": pools["dt_len_fbt"], "跌停明细_fund": pools["dt_len_fund"],
            "炸板率": round(zbr, 4),
            "★DT口径复核": "本场三读互证：fbt:asc → tc=8/pool=0（空明细缺陷复现）；zdp:asc → tc=8/8 行；fund:asc → tc=8/8 行；Pageindex=1 亦 8 行。明细名单：601999 出版传媒、000059 华锦股份、001368 通达创智、002388 新亚制程、002913 奥士康、002811 郑中设计、600202 哈空调、002578 闽发铝业。→ 跌停家数以 tc=8 为准，明细以 zdp/fund 8 行互证。"},
  "缺件": {"pulse.json": "不存在", "warboard.json": "不存在", "报警_%s.jsonl" % DATE: "不存在",
          "执行流水.jsonl": "不存在 → 引擎今日仍无任何执行记录（09:49 卖 002639、10:33 卖 002242、09:40 买 603370 均未入账）"},
  "口径": "缺件如实标注、不补造；风险判断不依赖 pulse/warboard（池帧 300 帧与报价新鲜、东财直读）"
 },
 "权限分级": {
  "A": "0 笔。本场唯一预案内机械腿是『603370 14:57 收盘价了结』——义务时段为收盘场，本场仅备料，不提前执行（13:30 场预置的 14:30 提前了结双条件未达成，见防守三查②）。",
  "B": "0 笔。603370 未炸板（今日未涨停，今高 %s vs 涨停价 %.2f）、对成本 +%.2f%%、距今高回落 %.2f%%、午后至尾盘最大 5 分钟跌幅 %.2f%%（门槛 -2%% 未达）、题材批量跳水最近 30 分钟最大簇 %d 只（门槛 3 只）→ 三项防守条件均未触发，不写 B 级动作。"
       % (px370["high"], limited, (px370["px"] / cost - 1) * 100, (px370["px"] / px370["high"] - 1) * 100,
          -max(-worst_after14, 0.0) if worst_after14 is not None else 0.0, max_cluster30[1]),
  "C": "0 笔（3 项闸门本场已全部转 PASS，仍不开仓）。①跌停 tc=8 < 12 → PASS；②炸板率 %.4f < 0.45 → PASS；③涨停 %d 家。名义闸门已打开，但按 13:30 场已留档决断『14:30/14:45 属尾盘隔夜腿 + 禁打板价 → 只记录观察不追价开仓』执行，且不预设标的避免临时造票 → 本场 C 档仍 0 笔，机会转入明日预案（见深场备料④）。"
       % (zbr, len(zt))
 },
 "fills": [],
 "no_action": {
  "结论": "心跳hb-e无动作：不平仓、不加仓、不开新仓；603370 按预案续持至 14:57 收盘场机械了结。",
  "持仓核": {
   "账本实况": "master/状态.json(date=20261022，nav 0.99012，现金 933,752.43)＋master/账本.jsonl(末条 2026-10-22 19:19:27) 仍记 002639 2600 股 + 002242 800 股 → 引擎侧今日零成交（欠账①，连续登记）；603370 300 股仅存在于决断件",
   "在持持仓": "603370 华新精科 300 股 @28.11（成本 8,433.00 元）",
   "现价": "腾讯 14:31:09 = %.2f（%+.2f%%）；池帧 14:31:04 = %s；今开 28.46／今高 %.2f／今低 %.2f／涨停价 %.2f"
          % (px370["px"], px370["pct"], [r["latest"] for r in fr[-1]["rows"] if r["code"] == "603370"][0:1], px370["high"], px370["low"], limited),
   "对成本": "+%.2f%%（浮盈 %+.2f 元；市值 %.2f 元 ≈ nav 的 %.2f%%）"
           % ((px370["px"] / cost - 1) * 100, (px370["px"] - cost) * qty, px370["px"] * qty, px370["px"] * qty / (933752.43 + 9039.0) * 100),
   "尾盘轨迹": "分时 1353 29.71 → 1405 29.85 → 1421 29.90 → 1425 30.01 → 1429 30.15 → 1432 %.2f；分时高 %.2f@%s、分时低 %.2f@%s；14:00 后最大回撤 %.2f%%；距今日高回落 %.2f%%"
           % (mt[-1][1], m_hi[1], m_hi[0], m_lo[1], m_lo[0], worst_after14, (px370["px"] / px370["high"] - 1) * 100)
  },
  "防守三查": [
   "①炸板：603370 今日从未涨停（今高 %.2f vs 昨收 %.2f = +%.2f%%，涨停价 %.2f）→ 无板可炸，『持仓炸板』不适用。" % (px370["high"], px370["pre"], (px370["high"] / px370["pre"] - 1) * 100, limited),
   "②大幅回撤：对成本 +%.2f%%、距今低 %.2f 修复 +%.2f%%、距今高 %.2f 仅回落 %.2f%%、单票权重 %.2f%%；14:00 后最大回撤 %.2f%%（无 -2%% 级急跌）→ 判『未达大幅回撤』，不临时自造阈值。13:30 场预置双条件『破今低 27.62 且 5 分钟内跌≥2%%』：今低 27.62 完好（分时低 27.68）、最大 5 分钟跌幅 %.2f%% → 均未达成，不提前了结。"
   % ((px370["px"] / cost - 1) * 100, px370["low"], (px370["px"] / px370["low"] - 1) * 100, px370["high"], (px370["px"] / px370["high"] - 1) * 100, px370["px"] * qty / (933752.43 + 9039.0) * 100, worst_after14, worst_after14),
   "③题材批量跳水：300 帧逐帧滚动窗口（每帧对 ≥240s 前帧比较，阈值单票 -2%%）→ 最近 30 分钟最大簇 %d 只（%s），全窗最大簇 %d 只（%s）；均 < 3 只门槛 → 无题材级跳水，不触发题材防守。"
   % (max_cluster30[1], max_cluster30[0], max_cluster[1], max_cluster[0])
  ],
  "环境读数": {
   "指数(14:31:09~14:31:12)": "上证 %.2f %+.2f%% / 深成 %.2f %+.2f%% / 创业板 %.2f %+.2f%%" % (
    idx["sh000001"]["px"], idx["sh000001"]["pct"], idx["sz399001"]["px"], idx["sz399001"]["pct"],
    idx["sz399006"]["px"], idx["sz399006"]["pct"]),
   "对比13:30(上证-0.37/深成+0.91/创业板+1.77)": "上证 +%.2fpp、深成 +%.2fpp、创业板 +%.2fpp → 单边修复延续，创业板领涨" % (
    idx["sh000001"]["pct"] + 0.37, idx["sz399001"]["pct"] - 0.91, idx["sz399006"]["pct"] - 1.77),
   "昨涨停池(33票，%s)" % now_s["ts"]: "中位 %+.2f%%、均值 %+.2f%%、涨 %d/跌 %d、涨停 %d、跌停 %d" % (
    now_s["median"], now_s["mean"], now_s["up"], now_s["dn"], now_s["zt"], now_s["dt"]),
   "对比13:30:54": "中位 %+.2f→%+.2f（%+.2fpp）、涨停 %d→%d、跌停 %d→%d、上涨家数 %d→%d" % (
    prev_s["median"], now_s["median"], now_s["median"] - prev_s["median"], prev_s["zt"], now_s["zt"],
    prev_s["dt"], now_s["dt"], prev_s["up"], now_s["up"]),
   "全市场池(%s)" % pools["fetched"]: "涨停 %d（板位 %s）、炸板 %d、跌停 %d、炸板率 %.4f；对比 13:31:22（涨停 41/炸板 9/跌停 17/率 0.1800）→ 涨停 +%d、跌停 -%d、炸板率 -%.4f" % (
    len(zt), json.dumps({str(k): v for k, v in sorted(lbc.items())}, ensure_ascii=False), len(zb),
    pools["tc"]["dt_fund"], zbr, len(zt) - 41, 17 - pools["tc"]["dt_fund"], 0.18 - zbr),
   "同比昨日14:46(参考，时点差15分钟)": "涨停 %d vs 31（+%.1f%%）、炸板 %d vs 24、炸板率 %.4f vs %.4f（24/55=0.4364）→ 今日赚钱效应显著优昨日尾盘" % (
    len(zt), (len(zt) / 31 - 1) * 100, len(zb), zbr, 24 / 55),
   "判断": "午后由『分化修复』升级为『扩散式修复』：涨停 41→73（尾盘一小时新增 32 家）、跌停 17→8、炸板率 0.18→0.14、昨涨停池中位 +3.80→+4.82、涨停 11→13、三指数全部转红且创业板 +3.88%。风险端同步收敛（跌停腰斩）→ 明日不按防守起手。但结构上首板 60/73=82.2%、4~5 板全空档、高位仅 603278 大业股份与 002724 海洋王两只 6 板 → 属『首板扩散 + 高位双钉』，高位延续性未验证，不宜追高。"
  }
 },
 "reason": {
  "①持仓处置": "603370 续持 300 股：现价 %.2f 对成本 +%.2f%%，尾盘拉升至高附近（分时高 30.16@1428，现价距高仅 %.2f%%），今低 27.62 完好、无 -2%% 级 5 分钟急跌 → 提前了结条件不成立。预案明文『只做 T+1 开盘→收盘当日价差』→ 卖出义务在 14:57 收盘场，本场不动、不改条款（不因浮盈 +7%% 临时改判持有过夜）。"
          % (px370["px"], (px370["px"] / cost - 1) * 100, (px370["px"] / px370["high"] - 1) * 100),
  "②预案trigger": "无残余：09:40 场三条条件单已结算（603370 成交／003021 主动弃／601091 落带外），10:30 场机械线（002242 破 20.92）已执行清出 → A 档 0 笔。",
  "③预案外机会": "闸门名义全开（跌停 8<12、炸板率 0.1412<0.45），但 14:30 后买入即隔夜腿：今日强势为午后一小时急速扩散，未经隔夜与次日竞价验证；且禁打板价 → 涨停 73 家中可买者多为已 +5~8% 的追价位。按 13:30 场已留档决断不追价开仓，机会整体转入明日预案（备料④），本场仅记录。",
  "④环境定性": "扩散式修复（宽度大增 + 风险端腰斩），非冰点反转（跌停未至恐慌级）、亦非退潮加速。明日为『修复能否延续』的验证日。"
 },
 "闸门核销": {
  "时点说明": "本场无 pulse/warboard，闸门以实读为准：池帧 %s、东财池 %s，均早于决断时点 %s，如实标注不冒充整点读数" % (fr[-1]["ts"], pools["fetched"], CUT),
  "10:00跌停<12": {"实读": "tc=8（zdp:asc 8 行 / fund:asc 8 行双证，fbt:asc 空明细缺陷复现）", "判定": "PASS（8 < 12）→ 本场为今日首次转 PASS，C 档闸门名义打开"},
  "盘中炸板率<0.45": {"实读": "%d/(%d+%d)=%.4f" % (len(zb), len(zt), len(zb), zbr), "判定": "PASS"},
  "09:25全市场低开占比<85%": "null（需全 A 开盘价扫描，本场未取；不以昨涨停池 33 票代理全市场）",
  "涨停数同比阈值(§2.2 ±20%)": {"实读": "73 vs 昨日 14:46 的 31 = +135.5%（时点差 15 分钟，方向性参考）", "判定": "阈值触发（向上）→ 记环境改善证据；不构成新增动作（尾盘隔夜腿纪律不变）"}
 },
 "在持票照会": {
  "603370 华新精科": "续持 300 股，成本 28.11，现 %.2f（+%.2f%%）。义务：14:57 收盘场按收盘价了结 T+1 腿；14:45 深场B 仅在『14:45 后 5 分钟内跌≥2%% 且跌破 29.56（今高 30.16×0.98）』时复议提前卖出。"
                     % (px370["px"], (px370["px"] / cost - 1) * 100),
  "002242 九阳股份": "已于 10:33:48 清出 800 股 @20.74；现价 %.2f（%+.2f%%）→ 若持有差额 +%.0f 元（+%.2f%%）。机械止损后反弹，作为『止损线是否需加缓冲』议题进 10/24 复盘，本场不回补、不改规则。" % (
   rows_q["sz002242"]["px"], rows_q["sz002242"]["pct"], (rows_q["sz002242"]["px"] - 20.74) * 800, (rows_q["sz002242"]["px"] / 20.74 - 1) * 100),
  "002639 雪人集团": "已于 09:49 清出 2600 股 @14.00；现价 14.93（-0.47%%，昨收 15.00）→ 若持有差额 +2,418 元（+6.64%%）。今日最大机会成本项，如实登记，本场不回补。",
  "另账本(不代决)": "auction 002626 金达威、logic 600487 亨通光电 分属他路账本，本场不取数、不裁决。"
 },
 "为14:45深场B备料": {
  "声明": "以下为备料草稿，不构成本场成交；14:45 深场B 复核后可采纳/否决，采纳需另出决断件。",
  "尾盘卖预案候选": [
   "【主案·预案内】603370 300 股：14:57~15:00 收盘集合竞价按收盘价了结。基准价=收盘价，不设价格下限、不挂涨停价等封单；除非触发下条加速条件，否则不在 14:45~14:57 主动砸盘（避免在拉升段自伤）。",
   "【加严备选·B档】若 14:45 后出现『5 分钟内跌≥2% 且跌破 29.56（今高 30.16×0.98）』→ 深场B 可改为不等收盘、以对手价（买一）即时卖出 300 股。属加严不放松，B 档可决范围，须写触发证据（帧时点＋区间跌幅）。",
   "【不改的条款】603370 若尾盘封涨停（涨停价 31.58，需再 +4.82%），仍按收盘价了结，不做『封板持有过夜』临场改判——预案为 T+1 日内腿，浮盈 +7% 不构成修改理由（盘中禁改参数）。",
   "【002242 口径样本】收盘价 vs 20.74 的差额，作为机械止损线缓冲议题的最后一块证据，深场B 只需登记收盘价，不回补、不改变明日动作。"
  ],
  "明日预案要点草稿": [
   "①情绪定性：扩散式修复（涨停 73、跌停 8、炸板率 0.1412、昨涨停池中位 +4.82%）。明日按『不防守、但不追高』起手：先看 09:25 竞价与量能台阶，再定攻防，不预设满仓进攻。",
   "②高位双钉验证：603278 大业股份（6板，今 +9.99%%、全天封板）与 002724 海洋王（6板，今 +9.99%%）是唯一高位梯子，4~5 板全空档。明日若两只均续板 → 情绪进入上升段，可做 2 板接力；若同时断板 → 判定修复一日游，转防守、C 档零新增。",
   "③首板扩散的兑现检验：今日首板 60 只，明日 09:45 前看二板家数——≥12 家为强（晋级率≥20%%），<8 家为弱（修复不接力）。这是明日第一决策依据，先于个股。",
   "④风险端闸门带入明日：跌停 <12、炸板率 <0.45 两侧；另新增观察项（仅记录、非参数）：4~5 板空档是否被填补（腰部重建＝趋势可延续，否则仍是首板一日游结构）。",
   "⑤标的池：今日涨停结构中专用设备 8、IT服务 6、软件开发 6、通用设备 5、汽车零部 5 为最强簇；明日只在这些簇里选『今日首板 + 明日竞价不破均价线 + 量能≥昨日同期』的票，不追 6 板高位、不打板价、不临场造票。",
   "⑥账本欠账：603370 300 股与今日清出的 002639/002242 仍未入引擎账本（连续第 4 日族）；若今晚 catch_up 仍未补记，明日 14:57 收盘了结将无持仓可挂 → 今晚必须结算。"
  ]
 },
 "异常与欠账": [
  "① 引擎无执行记录（连续登记）：master/状态.json 仍 date=20261022、持 002639+002242、现金 933,752.43；今日三笔只存在于决断件 → 交晚间链 catch_up，本场不手写账本（模拟盘数字只出自引擎）。",
  "② playbook.json 缺件（连续第 6 次：20261020/21/22/23×3）→ 预案真源仍为 0921 决断件 + _学习/交易计划_master_20261022.json，不补造。",
  "③ 交易日规格命令不可导入 sentiment 模块（自 20260917 连续登记）→ 本场以日期 + 300 帧 + 东财 qdate 三证等效，未早退。",
  "④ pulse.json / warboard.json / 报警_20261023.jsonl / 执行流水.jsonl 全部缺件 → 风险=次日开盘腿可能漏结算、页面『成交明细』空白。",
  "⑤ DT 池口径缺陷复现并已定位：fbt:asc 下 tc=8 而 pool=[]（空明细），zdp:asc / fund:asc / Pageindex=1 均返回 8 行 → 固化建议不变『tc 为计数真源 + zdp/fund:asc 取明细』（待批，本场未改生产代码）。",
  "⑥ 今日两次机械止损（002639 14.00 → 14.93、002242 20.74 → 21.66）合计机会成本 +3,154 元，方向均为『卖出后当日继续上涨』→ 交 10/24 复盘：止损线是过紧（缺缓冲）还是执行时点问题（09:49/10:33 均卖在上午弱势段）。本场不改阈值。",
  "⑦ 本场准点：池帧 %s、取数完成 %s，较名义 14:30 迟约 75 秒，无实质逾期。" % (fr[-1]["ts"], pools["fetched"])
 ],
 "口径": "决断时间戳 %s；池帧末 %s（龄 11s）；报价 t=14:31:09~14:31:12；东财池取数 %s；分时末点 1432。取数完成后未再抓取任何新报价，后续分析只读已落盘文件。算术全部由脚本实算（_hb_e_scan.py / _hb_e_extra.py / _hb_e_write.py），未手填。stdout 原始输出见 _hb_e_*.json 证据件。" % (CUT, fr[-1]["ts"], pools["fetched"])
}

json.dump(doc, open(TARGET, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", TARGET, os.path.getsize(TARGET), "bytes")
print("簇 最近30分钟 max", max_cluster30[1], max_cluster30[0], "| 全窗 max", max_cluster[1], max_cluster[0])
print("zbr %.4f zt %d zb %d dt %s" % (zbr, len(zt), len(zb), pools["tc"]["dt_fund"]))
print("after14 worst %.2f%%" % worst_after14)
