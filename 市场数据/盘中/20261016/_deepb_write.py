# -*- coding: utf-8 -*-
"""深场B(14:45) 发出版writer。只写本场产物: 临盘决断_20261016_1445.json(新建, 禁覆盖) + 报警_20261016.jsonl(append)。
不碰任何生产脚本/账本/净值/次日卖出指令。盘中禁改参数。"""
import json, os, statistics as st, csv
from datetime import datetime

BASE = r"D:\股票数据\市场数据"
D = "20261016"
DAY = os.path.join(BASE, "盘中", D)
TICKS = os.path.join(DAY, "realtime_ticks.jsonl")
CUT = "2026-10-16 14:45:00"
OUT = os.path.join(DAY, "临盘决断_%s_1445.json" % D)
ALARM = os.path.join(DAY, "报警_%s.jsonl" % D)
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

assert not os.path.exists(OUT), "发出版已存在, 禁覆盖: " + OUT

# ---------- 帧读取(只取 ts<=14:45:00) ----------
frames = []
for line in open(TICKS, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("ts"):
        frames.append(d)
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

# ---------- 变化速率/批量跳水 ----------
def p2s(t):
    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
gaps = [(p2s(legal[i+1]["ts"]) - p2s(legal[i]["ts"])).total_seconds() for i in range(len(legal)-1)]
lag = int((p2s(CUT) - p2s(last["ts"])).total_seconds())
noon = [f for f in legal if "11:31:00" <= f["ts"][-8:] <= "12:59:00"]
noon_frozen = False
if noon:
    base_set = {(x["code"], x["pct"]) for x in noon[0]["rows"]}
    noon_frozen = all({(x["code"], x["pct"]) for x in f["rows"]} == base_set for f in noon)

def chg(code, n):
    i = len(legal) - 1 - n
    if i < 0:
        return None
    a, b = snap(legal[i]).get(code), snap(last).get(code)
    if not a or not b:
        return None
    return round(b["pct"] - a["pct"], 2)

rate = {}
for n, lab in [(1, "1分钟"), (5, "5分钟"), (15, "15分钟"), (40, "40分钟")]:
    v = [x for x in (chg(c, n) for c in rows) if x is not None]
    rate[lab] = {"中位": round(st.median(v), 2), "最弱": min(v), "≤-3pp只数": sum(1 for y in v if y <= -3)}

batches = []
for i in range(len(legal)):
    for j in range(i+1, len(legal)):
        if (p2s(legal[j]["ts"]) - p2s(legal[i]["ts"])).total_seconds() > 120:
            break
        a, b = snap(legal[i]), snap(legal[j])
        mem = [c for c in a if c in b and round(b[c]["pct"] - a[c]["pct"], 2) <= -3]
        if len(mem) >= 3:
            batches.append({"起": legal[i]["ts"], "止": legal[j]["ts"], "只数": len(mem),
                            "成员": ["%s%+.2f->%+.2f" % (c, a[c]["pct"], b[c]["pct"]) for c in mem]})

# ---------- 日内轨迹 ----------
traj = {}
for m in ["09:40", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:15", "14:30", "14:44"]:
    target = p2s("2026-10-16 " + m + ":00")
    i = None
    for k, f in enumerate(legal):
        if p2s(f["ts"]) <= target:
            i = k
        else:
            break
    if i is None:
        continue
    S = snap(legal[i])
    ps = sorted(x["pct"] for x in S.values())
    traj[m] = {"中位": round(st.median(ps), 2),
               "封板": sum(1 for c, x in S.items() if x["latest"] >= ztp(x) - 1e-9),
               "炸板": sum(1 for c, x in S.items() if x["high"] >= ztp(x) - 1e-9 and x["latest"] < ztp(x) - 1e-9),
               "跌停": sum(1 for x in S.values() if x["pct"] <= -9.8),
               "涨/跌": "%d/%d" % (sum(1 for p in ps if p > 0), sum(1 for p in ps if p < 0))}

# ---------- 连板列 ----------
lb = {}
try:
    for r in csv.DictReader(open(os.path.join(BASE, "20261015", "zt_pool.csv"), encoding="utf-8-sig")):
        try:
            lb[r["代码"]] = int(float(r["连板数"]))
        except Exception:
            pass
except Exception:
    pass
height = sorted([p for p in rows if lb.get(p, 0) >= 2], key=lambda c: -lb[c])

# ---------- 盘中封/炸状态切换(池内) ----------
def seal_path(code):
    out, prev = [], None
    for f in legal:
        x = snap(f).get(code)
        if not x:
            continue
        z = ztp(x)
        s = "封" if x["latest"] >= z - 1e-9 else ("炸" if x["high"] >= z - 1e-9 else "")
        if s != prev:
            out.append({"ts": f["ts"], "latest": x["latest"], "pct": x["pct"], "态": s})
            prev = s
    return out

# ---------- 账本 ----------
state = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/state.json"), encoding="utf-8"))
navj = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/净值.json"), encoding="utf-8"))
sell_ord = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/次日卖出指令.json"), encoding="utf-8"))
mstate = json.load(open(os.path.join(BASE, "_学习/_模拟盘/master/状态.json"), encoding="utf-8"))

hb = json.load(open(os.path.join(DAY, "_hb_e_quote.json"), encoding="utf-8"))
for _c, _q in hb.items():
    if "latest" not in _q and "last" in _q:
        _q["latest"] = _q["last"]

def q(code):
    return hb.get("sz"+code) or hb.get("sh"+code)

def hold(code, name, acct, cost, sh, src_ts, src):
    x = rows.get(code)
    if x:                                  # 池内 → 用实时帧(最新≤14:45)
        px, pre, op, hi, lo = x["latest"], x["preClose"], x["open"], x["high"], x["low"]
        tsm, fetch = last["ts"], "realtime_ticks.jsonl 帧(池内, 最新合法帧)"
    else:                                  # 池外 → 用 hb-e 14:33 直取留档
        _q = q(code)
        px, pre, op, hi, lo = _q["latest"], _q["preClose"], _q["open"], _q["high"], _q["low"]
        tsm, fetch = _q["time"], "hb-e 14:32:57~14:33:00 腾讯直取留档(池外票) WARN"
    return {
        "code": code, "name": name, "账": acct, "shares": sh, "cost_px": cost,
        "行情戳": tsm, "行情源": fetch,
        "前收": pre, "今日开": op, "今日高": hi, "今日低": lo,
        "gap_pct": round((op / pre - 1) * 100, 2),
        "决断时点实价": px, "涨跌pct": round((px / pre - 1) * 100, 2),
        "相对成本pct": round((px / cost - 1) * 100, 2),
        "自今日高回撤pct": round((px / hi - 1) * 100, 2),
        "浮动盈亏_元": round((px - cost) * sh, 2), "市值_元": round(px * sh, 2)}

pos7 = [
    hold("000011", "深物业A", "第七账(盘中作战独立账本·账本在持)", 10.11, 5900, None, None),
    hold("002860", "星帅尔", "第七账(盘中作战独立账本·引擎本日09:26自机制买入)", 20.08, 2900, None, None),
]
master_hold = [("600668", "尖峰集团", 8.15, 6100, "master(master账·本日09:25 A级承接)"),
               ("605189", "富春染织", 17.97, 1100, "master(master账·本日09:25 A级承接)"),
               ("000601", "韶能股份", 6.68, 6000, "master(master账·状态.json 20261015)"),
               ("603968", "醋化股份", 14.30, 2100, "master(master账·状态.json 20261015)"),
               ("000823", "超声电子", 25.13, 800, "master(master账·状态.json 20261015)")]
pos_m = [hold(c, n, a, cost, sh, None, None) for c, n, cost, sh, a in master_hold]
allpos = pos7 + pos_m
mv7 = round(sum(p["市值_元"] for p in pos7), 2)
mvm = round(sum(p["市值_元"] for p in pos_m), 2)
pl7 = round(sum(p["浮动盈亏_元"] for p in pos7), 2)
plm = round(sum(p["浮动盈亏_元"] for p in pos_m), 2)

# ---------- 表态文本(逐票, 含今日表现/浮盈/明日计划/持有或卖出理由) ----------
pos7[0]["今日表现"] = ("前收 %.2f → 平开 %.2f(gap %+.2f%%) → 全日走高, 摸高 %.2f(=涨停价 %.2f 附近, 触板未封) → 回落; 14:33 留档 %.2f(%+.2f%%); 日低 %.2f"
                  % (pos7[0]["前收"], pos7[0]["今日开"], pos7[0]["gap_pct"], pos7[0]["今日高"], 10.82*1.1, pos7[0]["决断时点实价"], pos7[0]["涨跌pct"], pos7[0]["今日低"]))
pos7[0]["明日计划"] = "playbook.sells leg=close 条件腿: 若 20261016 收盘<今日开盘 %.2f → 清仓腿生效(次一交易日 09:25 执行); 否则继续持有" % pos7[0]["今日开"]
pos7[0]["持有或卖出理由"] = ("**本场无卖腿触发**。逐条: ①减仓腿=开盘 gap≥+3%% → 实测 %+.2f%% **未达**; ②清仓腿=收盘<今日开盘(%.2f) → **判定时点未到**(收盘价须待 14:57/15:00 场), 截至 14:33 留档 %.2f > 开盘 %.2f **未成立**; ③playbook 该条 take_zt=None、无 stop_pct → 无止盈/止损腿 ⇒ **维持持有**。"
                       % (pos7[0]["gap_pct"], pos7[0]["今日开"], pos7[0]["决断时点实价"], pos7[0]["今日开"]))
pos7[0]["风险备注"] = "自今日高 %.2f 回撤 %+.2f%%; 行情戳 14:33 距决断 %s(略越10分钟红线, 见数据新鲜度)" % (pos7[0]["今日高"], pos7[0]["自今日高回撤pct"], "11分57秒")

pos7[1]["今日表现"] = ("前收 %.2f → **高开 %.2f(gap %+.2f%%)** → 摸高 %.2f = 涨停价(触板未封) → 逐级回落至 %.2f(%+.2f%%); 日低 %.2f(=前收, 高开全数回吐)"
                  % (pos7[1]["前收"], pos7[1]["今日开"], pos7[1]["gap_pct"], pos7[1]["今日高"], pos7[1]["决断时点实价"], pos7[1]["涨跌pct"], pos7[1]["今日低"]))
pos7[1]["明日计划"] = "承 hb-e 14:30『深场B备料_1445.尾盘卖预案候选1(优先级最高)』: 建议转为第七账『次日卖出指令.json』口径(T+1 09:25 机械执行) — **须先由盘后复盘定论卖通道**, 本场不擅自写入"
pos7[1]["持有或卖出理由"] = ("**无卖出腿、无成交通道 ⇒ 不处置、不写 fill**(零编造)。但防守证据双通道成立: ①通道A(相对成本≤-4%%) %+.2f%%; ②通道C(持仓炸板) 触涨停价 %.2f 未封。★口径澄清: 判断流水本日 14:30 块对 002860 记『等: 炸开>3%%放弃(失败率53%%/期望-4.89%%)』——该条为**引擎内生判据、非 playbook 显式卖腿**, 按铁律『止损类规则只认预案单显式声明』**不构成卖据**。"
                       % (pos7[1]["相对成本pct"], pos7[1]["今日高"]))

for p in pos_m:
    if p["code"] == "600668":
        p["今日表现"] = ("前收 %.2f → 高开 %.2f(gap %+.2f%%) → **09:32:06 封板 %.2f** → 全天封死 → **14:43:02 首炸(该帧 8.45)** → 末合法帧 14:44:02 报 %.2f(%+.2f%%); 日低=开盘价 %.2f。★本场新增事实(14:30 场时仍记『封板持有』)"
                    % (p["前收"], p["今日开"], p["gap_pct"], 7.99*1.1, p["决断时点实价"], p["涨跌pct"], p["今日开"]))
        p["明日计划"] = "尾盘炸板 → 明日开盘按『断板即走』复核; **须先在 playbook 显式声明卖腿方可落地**(本日 playbook.sells 无 600668)"
        p["持有或卖出理由"] = "**无卖出腿**(playbook.sells 无该票) → 无显式卖据 ⇒ 不处置。但 通道C『持仓炸板』成立(封板→尾盘炸板) → 登记防守证据、移交盘后。相对成本仍为正(%+.2f%%)" % p["相对成本pct"]
        p["封板轨迹"] = seal_path("600668")
    elif p["code"] == "605189":
        p["今日表现"] = "前收 %.2f → 平开 %.2f(gap %+.2f%%) 即全日最高 → 单边下行至 %.2f(%+.2f%%); 日低 %.2f" % (p["前收"], p["今日开"], p["gap_pct"], p["决断时点实价"], p["涨跌pct"], p["今日低"])
        p["明日计划"] = "承 hb-e 备料候选2: 若续弱则次日处置候选; 须先建卖通道"
        p["持有或卖出理由"] = "**无卖出腿** → 不处置。通道A 大幅回撤成立(相对成本 %+.2f%% / 自今日高 %+.2f%%) ⇒ 登记防守证据、移交盘后" % (p["相对成本pct"], p["自今日高回撤pct"])
    elif p["code"] == "603968":
        p["今日表现"] = "前收 %.2f → 低开 %.2f(gap %+.2f%%) → 冲高 %.2f(日高) → 回落至 %.2f(%+.2f%%); 日低 %.2f" % (p["前收"], p["今日开"], p["gap_pct"], p["今日高"], p["决断时点实价"], p["涨跌pct"], p["今日低"])
        p["明日计划"] = "承第一手判断: 处置优先级第3; 须先建卖通道"
        p["持有或卖出理由"] = "**无卖出腿** → 不处置。通道A 成立(相对成本 %+.2f%% / 自今日高 %+.2f%%) ⇒ 登记防守证据、移交盘后" % (p["相对成本pct"], p["自今日高回撤pct"])
    elif p["code"] == "000601":
        p["今日表现"] = "前收 %.2f → 高开 %.2f(gap %+.2f%%) → 冲高 %.2f → 回落 %.2f(%+.2f%%)" % (p["前收"], p["今日开"], p["gap_pct"], p["今日高"], p["决断时点实价"], p["涨跌pct"])
        p["明日计划"] = "观察(未达防守门槛)"
        p["持有或卖出理由"] = "**无卖出腿** → 不处置; 相对成本 %+.2f%% 未达 -4%% 门槛" % p["相对成本pct"]
    else:
        p["今日表现"] = "前收 %.2f → 高开 %.2f(gap %+.2f%%) → 冲高 %.2f → 回落 %.2f(%+.2f%%)" % (p["前收"], p["今日开"], p["gap_pct"], p["今日高"], p["决断时点实价"], p["涨跌pct"])
        p["明日计划"] = "持有(未达防守门槛)"
        p["持有或卖出理由"] = "**无卖出腿** → 不处置; 相对成本 %+.2f%% 为正" % p["相对成本pct"]

# ---------- playbook ----------
pb = json.load(open(os.path.join(BASE, "盘中/20261015/playbook.json"), encoding="utf-8"))
sells = pb["sells"]; buys = pb["buys"]

# ---------- watch confirm 复核 ----------
WATCH = [("300111", "向日葵", "lhb(席位命门)", "20261016 封板质量转为合格(炸板≤3次 且 末封≤14:00)且续封 → 升级重估为条件票候选(权重仍≤2%)"),
         ("603230", "内蒙新华", "lhb(席位命门)", "20261016 续封且 炸板≤2次 且 末封≤14:00 → 升级重估(权重≤2%)"),
         ("002815", "崇达技术", "logic+theme", "20261016 开盘可成交(非一字)且 PCB算力硬件线宽度环比≥0 且出现2板及以上≥1只 → 送总审重估"),
         ("301282", "金禄电子", "logic(产业逻辑)", "20261016 PCB方向仍有≥1只带公告级业绩的涨停 且本票未大幅高开后走弱 → 重估"),
         ("002134", "天津普林", "logic(产业逻辑)", "出具自身产能/订单公告原件 且封板质量改善(炸板≤1次) → 重估"),
         ("605058", "澳弘电子", "limitup(质量库)", "次日机械结算质量分对照"),
         ("600812", "华北制药", "limitup(质量库)", "次日机械结算质量分对照"),
         ("002945", "华林证券", "limitup(质量库)", "次日机械结算质量分对照"),
         ("001318", "阳光乳业", "theme(主线题材)", "次日机械结算题材线宽对照")]
watch_cf = []
for c, n, s, cond in WATCH:
    x = rows.get(c)
    if not x:
        watch_cf.append({"code": c, "name": n, "source": s, "confirm": cond, "本场读数": None, "判定": "非池内, 无法核定"})
        continue
    watch_cf.append({"code": c, "name": n, "source": s, "confirm": cond,
                     "本场读数": {"ts": last["ts"], "latest": x["latest"], "pct": x["pct"], "high": x["high"], "low": x["low"],
                                  "涨停价": ztp(x), "封板": x["latest"] >= ztp(x) - 1e-9, "触板": x["high"] >= ztp(x) - 1e-9},
                     "判定": ("confirm 成立" if (x["latest"] >= ztp(x) - 1e-9) else "confirm 未成立")})

# ---------- 错失登记 ----------
miss = []
for b in buys:
    c = b.get("代码"); x = rows.get(c)
    if not x:
        miss.append({"code": c, "name": b.get("名称"), "status": "非池内, 无法核定"})
        continue
    g = round((x["open"] / x["preClose"] - 1) * 100, 2)
    rng = (b.get("trigger") or {}).get("open_range") or {}
    lo, hi = rng.get("min_gap"), rng.get("max_gap")
    inband = (lo is None or g >= lo) and (hi is None or g <= hi)
    miss.append({"code": c, "name": x["name"], "顺位权重%": b.get("weight_pct"), "source": b.get("source"),
                 "开盘": x["open"], "gap%": g, "闸门": "[%s,%s]" % (lo, hi), "落带": inband,
                 "锁定帧pct%": x["pct"], "现价/开盘pct%": round((x["latest"] / x["open"] - 1) * 100, 2),
                 "stop_pct": ((b.get("intraday") or {}).get("stop_pct")),
                 "判定": ("落带 → 09:25 已成交(见 A级_预案内.本日已结算)" if inband else "破位作废(闸门拒)")})

# ---------- 高板 ----------
high_txt = ["%s %s %d板 现%+.2f%%(%s)" % (c, nm(c), lb[c], rows[c]["pct"],
            "封" if c in sealed else ("炸" if c in touched else "未触板")) for c in height]

LINE_MAP = {"601811": "出版", "603999": "出版", "000530": "机械/冷链", "003029": "信创", "002889": "物流",
            "601811_": "", "002343": "AI短剧/传媒", "002696": "消费", "001318": "食品", "605189": "染料印染",
            "002815": "PCB算力硬件", "301282": "PCB算力硬件", "002134": "PCB算力硬件", "605058": "PCB算力硬件",
            "000626": "其他", "002103": "其他"}
lines = {}
for c in rows:
    ln = LINE_MAP.get(c)
    if ln:
        lines.setdefault(ln, []).append(c)

_r3 = "跌至 %.2f(%+.2f%%)" % (pos_m[0]["决断时点实价"], pos_m[0]["涨跌pct"])
_r4 = "14:43:02 首炸(该帧 8.45) → 末合法帧 %s 报 %.2f(%+.2f%%)" % (last["ts"][-8:], pos_m[0]["决断时点实价"], pos_m[0]["涨跌pct"])

result = {
 "date": D, "session": "deepb", "ts": "14:45", "version": "v5",
 "决断时间戳": "2026-10-16 14:45:00 CST", "write_ts": NOW,
 "修订记录": [
  "v1(sha256_16=56d8c0189f3bcc07, 45972 bytes)→v2: 『交易日校验.等价证据』原引『全档帧区间』(尾端为写档时刻的最后一条帧, 即 >14:45:00 的帧), 修订为引『决断窗内合法帧区间』, 并把超出决断的帧数改为仅登记于『数据新鲜度·排除帧』—— 消除 14:45:00 之后时间戳在非登记字段的渗漏(哨兵 C23)。",
  "v2(sha256_16=1bf3deb11d903527, 46700 bytes)→v3: 『B级_防守.通道C_持仓炸板.对象1_600668.★本场新增事实』原为未套用格式化参数的**字面残留**『跌至 8.44(%+.2f%%)』(出页缺陷), 修订为已求值的『" + _r3 + "』; 另修正 review md 中『通道B/通道C 判定』的双重加粗 **** 渲染。",
  "v3(sha256_16=07c5aa59b6fb8d48, 47342 bytes)→v4: **时点归属精度修订**(零编造纪律下的自我复查)。原文将 600668 的『8.44』归属到 14:43:02 首炸帧, 实为口径混淆 —— 8.44 系 **14:44:02 末合法帧**报价, 而 **14:43:02 首炸帧**报价为 **8.45**(两者均为留档真值, 见『封板轨迹』逐帧)。v4 在『持仓表态 600668.今日表现』与『通道C_持仓炸板.对象1』两处均改写为『" + _r4 + "』。",
  "v4(sha256_16=641ce2ac2f40dba1, 47968 bytes)→v5: **修订记录自身的数值口径修订**。v3/v4 两条修订说明中引用的 600668 末合法帧涨跌被误写为 +5.76%(该值实为 14:43:02 首炸帧的 pct), 与该字段实际取值 +5.63% 不一致 → v5 改为**由 pos_m 计算生成**(『" + _r3 + "』/『" + _r4 + "』), 使修订说明与被修订字段同源、不再漂移。**判定/读数/结论字段逐字不变**。",
  "发出版序列 = v1_superseded + v2_superseded + v3_superseded + v4_superseded (四者留档均未删改) + v5(本件)。每版均有独立 sha256 留痕, 符合『发出版不可覆盖』。"],
 "修订记录_版本": {"v1": "56d8c0189f3bcc07 / 45972 bytes", "v2": "1bf3deb11d903527 / 46700 bytes",
                 "v3": "07c5aa59b6fb8d48 / 47342 bytes", "v4": "641ce2ac2f40dba1 / 47968 bytes", "v5": "本件"},
 "场次说明": "A股盘中作战·深场B(14:45尾盘场, 13号盘中作战agent)。任务=①尾盘卖预案执行(sells中 leg=close / take_zt 触发→写本文件) ②持仓逐票表态 ③执行对账(引擎已执行什么) ④预收盘第一手判断。权限: A级=预案内自由 / B级=预案外防守(写触发证据) / C级=预案外进攻(本场禁)。铁律: 零后视镜(仅用 ts<=14:45:00 已留档数据)/断更>10分钟只报警禁决策/发出版不可覆盖/盘中禁改参数/止损类规则只认预案单显式声明。",
 "job身份": {
   "job": "0509b31150e9 · sentiment-intraday-deepb", "cron": "45 14 * * 1-5",
   "enabled": True, "model": "deepseek-flash", "provider": "deepseek",
   "execution_id": "fd615bd8ac4c4cc8ba7a90be8db72233",
   "scheduled_instant": "2026-10-16 14:45:00 CST (=06:45:00 UTC)",
   "dispatched_at": "2026-10-16T14:45:55.019519+08:00", "claimed_at": "2026-10-16T14:45:55.834879+08:00",
   "kind": "on_time", "lateness_seconds": 55.0,
   "真源": "profiles/a/cron/jobs.json#last_dispatch + executions.db (非自报)"},
 "交易日校验": {
   "结论": True, "判定": "2026-10-16 周五 = 交易日(盘中运行中)",
   "等价证据": "①realtime_ticks.jsonl **决断窗内 %d 帧(%s ~ %s, 全部 ts≤14:45:00)**, 间隔 min60s/max61s, >120s空档 0 次(全档 %d 帧, 其中 ts>14:45:00 的 %d 帧仅登记于『数据新鲜度·排除帧』, 未参与任何判定); ②末合法帧 pool_date=%s / pool_kind=%s / phase=%s / pool_stale=%s; ③腾讯直取 18 标的行情戳 202610161432xx~1433xx(交易时段内, 含上证/深证指数); ④盘中/pipeline.lock=『20261016 12700 09:14:56』本日上锁; ⑤午休窗 %d 帧逐票价全等(冻结, 无脏数据); ⑥executions.db 本日 21 个 job 记录、agent 场次(preread/hb-a~e) 全部 completed、no_agent 引擎场次(09:25/10:00/14:30) 全部 completed, 迟到均 55s、kind=on_time。"
             % (len(legal), legal[0]["ts"], legal[-1]["ts"], len(frames), len(excluded), last.get("pool_date"),
                last.get("pool_kind"), last.get("phase"), last.get("pool_stale"), len(noon)),
   "链路缺口_登记": "任务书指定的 `python -c \"from sentiment.core.calendar import is_trading_day,today_str\"` 在 D:\\股票数据\\市场数据 下 ModuleNotFoundError(无 sentiment 包, 承 10/13~10/15 同项登记) → 以上述①~⑥实盘留档替代, 不伪报结论。"},
 "数据新鲜度": {
   "契约源_pulse.json": "盘中/%s/pulse.json **全库0命中(契约路径未实现, 连续多日同型)** → 以 realtime_ticks.jsonl 顶替断更核验并明示口径替换" % D,
   "替代源": "盘中/%s/realtime_ticks.jsonl" % D,
   "读档帧数": len(frames), "合法帧(ts<=14:45:00)": len(legal),
   "首帧": legal[0]["ts"], "末合法帧": last["ts"],
   "帧距_秒": {"min": min(gaps), "max": max(gaps)}, ">120s空档": sum(1 for g in gaps if g > 120),
   "断更判定": "末合法帧 %s 距决断时点 14:45:00 仅 %d 秒 << 600 秒红线 → **新鲜, 允许决策**" % (last["ts"], lag),
   "排除帧(ts>14:45:00, 仅列示未作决策输入)": excluded,
   "持仓票行情_新鲜度警告": ("7 只在持票中仅 **600668/605189** 在实时池(取自合法帧 %s); 其余 5 只(000011/002860/000601/603968/000823) **不在池内**(36票×%d合法帧 0 命中) → 唯一 ≤14:45 的持仓行情 = hb-e 14:32:57~14:33:00 腾讯直取留档, 距决断 **11分57秒, 略越 10 分钟红线 → 按『辅助读数、非主源』使用并 WARN 登记**; 主判断(000011 leg=close 的收盘值)本就不可得, 不依赖其绝对值; **不在此刻补拉行情**(拉取时刻>14:45:00 属零后视镜违规, 宁可标注口径缺口)。" % (last["ts"], len(legal))),
   "池口径": "src=%s(单源) / pool_date=%s / pool_kind=%s / pool_stale=%s / 每帧 n=%d → 口径=『10/15 涨停股(36只) 今日承接』, **非当日全市场口径**" % (last.get("src"), last.get("pool_date"), last.get("pool_kind"), last.get("pool_stale"), len(rows))},
 "载体缺失登记": [
   "盘中/%s/warboard.json **缺失**(今日未生成) → 全库 %s 无本日件; 现有 盘中/20261014/warboard.json(mtime 2026-10-16 14:31, **内容 date=20261014**、ts=『2026-10-14 晚间复盘重建』, 系素材日文件被回写) → 本场以该件 #judgment + 本场实时帧替代, 缺口登记入账(承 hb-e 同款登记)" % (D, D),
   "盘中/%s/warboard.json 与 盘中/20261015/warboard.json **均不存在**(连续缺件)" % D,
   "盘中/%s/执行流水.jsonl **缺失**(全库检索无该文件名载体, 契约未实现) → 以引擎自留档 + 账本互证替代" % D,
   "盘中/%s/pulse.json **缺失**(契约未实现)" % D,
   "盘中/%s/报警_%s.jsonl 读时**不存在** → 本场新建并追加(见交付对账)" % (D, D),
   "盘中/%s/playbook.json **不存在** → 预案真源取素材日 盘中/20261015/playbook.json(date=20261015, route=master, version=2, mtime 2026-10-15 19:59:08 < 决断时刻, 合法输入)" % D],
 "warboard照会": {
   "源": "盘中/20261014/warboard.json (date=20261014, ts=『2026-10-14 晚间复盘重建』, mtime 2026-10-16 14:31 ≤ 决断时刻 → 合法输入)",
   "judgment": {"stage": "C防守（维持）", "pos_band": "≤2成", "date": "1014晚",
                "line摘要": "温度31.6→17.9(入冰点)、涨停67→36(腰斩)、封板率77.9%→60.0%(破64%退潮线)、跌停8→11、炸板率22.1%→40.0%(翻倍)、成交16759→14144亿(-15.6%); 唯一修复项=≥4板家数0→3",
                "checks5项": "now 全为 null(待明晨09:25竞价场回应)"},
   "本日档位第二源": "总审_20261015.json#总裁决 = 结论『C防守(维持)』/ 档位 C / 置信度 73 / 机械门槛四项 2/4 达(封板率83.72%✓、≥2只4板及以上✓; 温度≥45✗、涨停≥60✗) / 总仓上限≤8%、单笔≤5%、不新开第五条线 → 与本场 C级禁行一致",
   "池况(pulse·1014素材日)": {"涨停": 36, "跌停": 11, "炸板": 24, "炸板率": 40.0, "最高连板": 4}},
 "在持票照会": {
   "口径": "**第七账** = 盘中作战独立账本 _学习/_模拟盘/盘中作战/(state.json mtime 2026-10-16 14:31: positions=[000011 深物业A 5900@10.11 cost 59649.59 buy_date 20261003, 002860 星帅尔 2900@20.08 cost 58232.17 buy_date 20261016], cash=882118.24; 净值.json date=20261016 nav=999999.24 / pos_val=117881.0 / n_pos=2; 次日卖出指令.json=[]) + **master账** = _学习/_模拟盘/master/状态.json(date=20261015, mtime 2026-10-15 20:36:15, 现金830301.19) 叠加本日 09:25 四笔机械成交(临盘决断_20261016_0940.json#fills)。**禁漏票: 在持 7 只全部表态。**",
   "持仓": allpos,
   "合计": {"第七账_市值_元": mv7, "第七账_浮盈亏_元": pl7, "第七账_占nav_pct": round(mv7 / navj["nav"] * 100, 2),
            "master账_市值_元": mvm, "master账_浮盈亏_元": plm,
            "在持7只合计市值_元": round(mv7 + mvm, 2), "在持7只合计浮盈亏_元": round(pl7 + plm, 2),
            "行情时点": "600668/605189 = %s(实时帧); 其余5只 = 2026-10-16 14:32:57~14:33:00(hb-e 直取留档)" % last["ts"]}},
 "A级_预案内": {
   "许可": True, "本场成交笔数": 0, "本场买入金额_元": 0.0,
   "说明": "**零 A 级新增动作(合法空集, 非漏写)**。playbook.buys=3 只(600668/605189/000530) 全为『明晨 09:25 gap 一次性判定』条件单, 且均已于本日 09:25 结算完毕(600668 承接 / 605189 承接 / 000530 破位作废) → **无盘中/尾盘段二次 trigger 语义**; playbook.sells 的 2 条 leg=open 已于 09:25 执行、1 条 leg=close(000011) 条件未成立 → 本场无可触发项。",
   "本日已结算(09:25~09:40, 非本场动作)": [
     "买入 600668 尖峰集团 6100@8.15(gap +2.00% 落带 [-3,+3]) — 源 临盘决断_20261016_0940.json#fills[0]",
     "买入 605189 富春染织 1100@17.97(gap +0.67% 落带 [-3,+5]) — 源 #fills[1]",
     "卖出 600693 东百集团 4000@9.87(跌停价, leg=open) — 源 #fills[2]",
     "卖出 605577 龙版传媒 2200@17.99(leg=open) — 源 #fills[3]",
     "弃单 000530 冰山冷热 09:40 破位作废(实开 gap -4.18% < 下沿 -4.0%)"],
   "余下时段可触发项": "无(本场为尾盘名义段, 之后仅 14:57 收盘场, 但该场 enabled=false, 见通道前置)。"},
 "B级_防守": {
   "触发": True,
   "门槛原文": "①持仓炸板/大幅回撤/题材批量跳水(≥3只2分钟内-3%)→B级防守(写触发证据)",
   "通道A_持仓大幅回撤": {
     "判据(本场口径, 明示)": "相对成本(或成交价) ≤ -4% **或** 自今日高点回撤 ≥ 10% → 判『大幅回撤』(承 20261014 hb-b / 20261013/1015 hb-e 同口径, 本场未改阈值)",
     "成立对象": [p for p in allpos if p["相对成本pct"] <= -4 or p["自今日高回撤pct"] <= -10],
     "未达门槛者": [{"code": p["code"], "name": p["name"], "相对成本pct": p["相对成本pct"]} for p in allpos if not (p["相对成本pct"] <= -4 or p["自今日高回撤pct"] <= -10)]},
   "通道B_题材批量跳水": {
     "判定": "**不成立**", "门槛": "池内 ≥3只 / 2分钟内 / 每只 ≥3pp",
     "实测": "全窗(09:31:06~%s, 全部 ≤120s 帧对)扫描达阈批数 = **%d**(仅 09:31:06→09:32:06 早盘批: %s); 末窗 %s → 尾盘无批量跳水。变化速率: %s"
             % (last["ts"], len(batches),
                (batches[0]["成员"] if batches else []),
                json.dumps(rate, ensure_ascii=False), json.dumps({k: rate[k]["最弱"] for k in rate}, ensure_ascii=False))},
   "通道C_持仓炸板": {
     "判定": "**成立 · 2 只**",
     "对象1_600668 尖峰集团(master账)": {"★本场新增事实": "本日 09:32:06 首触板即封、全天封死, **14:43:02 转炸(该帧 8.45)** → 末合法帧 14:44:02 报 %.2f(%+.2f%%)" % (pos_m[0]["决断时点实价"], pos_m[0]["涨跌pct"]), "封板轨迹": seal_path("600668")},
     "对象2_002860 星帅尔(第七账)": {"证据": "本日 high=20.12 = 涨停价(前收 18.29×1.1); 09:49 留档 +10.01%%(触板), 现价 18.63 << 涨停价 → 触板后未封、自今日高回落 %+.2f%%" % pos7[1]["自今日高回撤pct"]},
     "池内炸板(非持仓, 仅记录)": [c + nm(c) + "%+.2f" % rows[c]["pct"] for c in broken]},
   "处置": "**本场不发起任何成交**。理由: ①无『卖腿/止损』显式声明(playbook.sells 三条: 两条 leg=open 已于 09:25 执行、一条 leg=close 条件未成立; 无任何票带 take_zt/stop_pct); ②现行结构无任何卖通道(见『尾盘卖预案执行.通道前置』); ③铁律『盘中禁改参数』+『零编造』→ 不虚构成交、不写 fill。全部登记为证据并移交盘后/次日。"},
 "C级_预案外": {
   "许可": False,
   "依据": "盘中/20261014/warboard.json#judgment=『C防守(维持)·pos_band ≤2成』+ 总审_20261015.json#总裁决『执行清单不放开、总仓≤8%、不追高、不加仓、不新开第五条线』+ 铁律『盘中禁改参数』→ 预案外进攻(含带帽 C 级)禁行。",
   "本场动作": "0 笔 C 级、0 带帽单; 不把池内异动折算成新机会。",
   "仅记录(非动作)": [
     "000530 冰山冷热 09:40 弃单后 10:21:15 起封板(现 7.62 = 涨停价) → 弃单机会成本(承 hb-d 立案), 供盘后归因",
     "600668 尖峰集团 14:43:02 尾盘炸板(由封板转炸) → 本场新增, 供盘后锚定『尾盘炸板』样本",
     "601811 新华文轩 09:57:11 首封→10:01 炸→10:06 回封→10:07 炸→**14:31 起回封至今**(2板/出版) = 池内尾盘『炸后回封』代表",
     "002815 崇达技术 09:31 一字触板(25.58) 后全日走弱(现 23.46, +0.90%) → 一字不可执行判据再获当日样本",
     "002134 天津普林 / 301282 金禄电子 双双跌停(-9.98%) = 池内 PCB 算力硬件线集中杀跌"]},
 "尾盘卖预案执行": {
   "预案真源": "盘中/20261015/playbook.json (date=20261015, route=%s, version=%s, mtime 2026-10-15 19:59:08 ≤ 决断时刻 → 合法输入)" % (pb.get("route"), pb.get("version")),
   "sells清单": "n=%d: %s" % (len(sells), json.dumps([{"code": s["代码"], "name": s["name"], "leg": s.get("leg"), "take_zt": s.get("take_zt"), "ref_px": s.get("ref_px")} for s in sells], ensure_ascii=False)),
   "leg_close_take_zt声明": "**唯一 leg=close = 000011 深物业A**(存在); take_zt 三条**全为 null → 无止盈腿启用**; sells 三条**无 stop_pct 字段**、buys 三条的 intraday.stop_pct **全为 null → 无任何止损腿**(与铁律『止损类规则只认预案单显式声明』一致: 本日无显式止损声明, 一切止损类判据(如 hb-e 备料候选触发条件、引擎判断流水『炸开>3%%放弃』)均**不构成卖据**); 次日卖出指令.json=%s; 盘中/20261016/playbook.json 不存在(无第二卖出源)" % json.dumps(sell_ord, ensure_ascii=False),
   "腿逐一判定": [
     {"腿": "600693 leg=open", "条件": "20261016 开盘离场(断板/一字封死)", "实测": "本日 09:25 卖出 4000@9.87(跌停价开盘, 全市场唯一跌停开盘) — 源 临盘决断_20261016_0940.json#fills[2]", "判定": "**已于开盘场执行完毕, 本场无残留**"},
     {"腿": "605577 leg=open", "条件": "20261016 开盘离场(断板)", "实测": "本日 09:25 卖出 2200@17.99(相对成本 17.64 = +1.98%) — 源 #fills[3]", "判定": "**已于开盘场执行完毕, 本场无残留**"},
     {"腿": "000011 leg=close(a) 清仓", "条件": "20261016 开盘 gap≤-4% 破位 或 当日收盘<当日开盘", "实测": "①本日开盘 %.2f / 前收 %.2f → gap **%+.2f%% 未达 -4%%**; ②『当日收盘』判定时点 14:45 **不可得**(须 14:57/15:00), 截至 14:33 留档 %.2f > 今日开盘 %.2f → **未成立**" % (pos7[0]["今日开"], pos7[0]["前收"], pos7[0]["gap_pct"], pos7[0]["决断时点实价"], pos7[0]["今日开"]), "判定": "**未触发(条件未达/未到判定时点)**"},
     {"腿": "000011 leg=close(b) 减仓", "条件": "20261016 开盘 gap≥+3% 逢强减仓", "实测": "gap **%+.2f%% 未达 +3%%**" % pos7[0]["gap_pct"], "判定": "**未触发**"},
     {"腿": "000011 leg=close(c) 持有", "条件": "两者均未触发 → 继续持有", "实测": "a)/b) 均未触发", "判定": "**当前落『持有』(维持)**"}],
   "可卖标的": "**0 只** —— ①600693/605577 卖腿已于 09:25 执行完毕; ②000011 的 leg=close 三条件均未触发; ③002860/600668/605189/603968 虽防守证据成立, 但 playbook.sells **无对应显式卖腿** → 不构成卖据; ④hb-e 备料候选非预案声明。",
   "结果": "**未执行(合法空集), fills=[]**; 未设任何卖价带、**未调用 fills 接口**, px_exec(决断后下一tick留档价 ± 滑点0.10%)与『跌停封死顺延』条款**均不适用**(未引用任何 >14:45:00 的帧价)。",
   "通道前置(第8次登记)": "现行结构下**无任何已运行卖通道**: ①盘中回应引擎-每日收盘14:57(jobs.json id=04066045b634) **enabled=false, last_dispatch=null** → 引擎内唯一生成『次日卖出指令』并做持仓断板/跌停检查的场次从未运行(真源已复核); ②引擎卖出仅在 09:25/10:00 消费『次日卖出指令.json』(=[]); ③playbook.json 的 sells 字段**无任何模块消费方** ⇒ master 账实质『只买不卖』, 一切 B 级防守在结构上不可落地。"},
 "fills": [],
 "fills_口径": "本场零成交(合法空集, 非漏写)。理由: ①leg=open 两条已于 09:25 结算; ②leg=close(000011) 三条件均未触发(收盘值判定时点未到); ③其余持仓无任何显式卖腿; ④C 级禁行。若发生成交: px_exec = 决断后下一tick留档价 ± 滑点0.10%(买不利向上/卖不利向下), 买必带整手 qty, 跌停封死顺延。本场未调用该接口。",
 "no_action": True,
 "执行对账_引擎已执行": {
   "契约件": "盘中/20261016/执行流水.jsonl **缺失**(全库0命中) → 无流水可对账, 改以引擎自留档 + 账本互证 + 开盘场fills。",
   "引擎自留档": "判断流水.jsonl(mtime 2026-10-16 14:31, %d bytes); 本日块 = 3 个 × 16 行 = 48 行: (08-16 09:25/0925)、(08-16 10:00/1000)、(08-16 14:30/1430) —— **ts 字段读作『08-16』= 月份退化(应 10-16), 承前场登记**; 48 行**全为档位判定**(档位/闸门/题材/个股/等), **无任何成交字段**。" % os.path.getsize(os.path.join(BASE, "_学习/_模拟盘/盘中作战/判断流水.jsonl")),
   "引擎本日已执行": "**5 笔机械动作 = 开盘场 4 笔 fills + 09:26 第七账自机制买入 1 笔**: ①买入 600668 6100@8.15(master); ②买入 605189 1100@17.97(master); ③卖出 600693 4000@9.87(master, 跌破成本 -20.40%); ④卖出 605577 2200@17.99(master, +1.98%); ⑤**买入 002860 星帅尔 2900@20.08(第七账, 09:26, 依据 判断流水 08-16 09:25 块 档位『✓共振·可成交』三维齐)**; ⑥弃单 000530(09:40 破位作废)。",
   "账本回写核验": "第七账 state.json cash=882118.24 = 1,000,000 − 59649.59(000011) − 58232.17(002860), **与 5 笔动作一致(无卖出回款入账) → 卖出腿是否真实成交仍待引擎回写核验**; 账本.jsonl mtime 2026-10-16 09:26 已记 002860 buy; master 状态.json **date=20261015, mtime 2026-10-15 20:36:15 → 本日 2买2卖 0 回写(第2次登记)**。",
   "★引擎判据与成交不一致(本场新增发现)": "判断流水本日 3 个块对 002860 的『闸门』字段**全部读作『✓低开-6.08%<5%』** —— 与 20261015 三个旧块**逐字相同**(该值系 10/15 实况), 而本日 002860 **实际高开 +9.68%(开 20.06 / 前收 18.29)**。即: **闸门字段未随日刷新(沿用上一交易日缓存值)**, 但其『档位』却按当日实况判为『✓共振·可成交(个股+9.7%)』并据此成交 → 同一行的判据内部不自洽。影响面: 任何依赖『闸门』文本做机械复核的场次会误读。登记待盘后定论(不改参数)。",
   "运行真源(executions.db)": "本日盘中链 21 项记录: pipeline 09:14:55 completed / preread 09:21:55 completed / 竞价引擎 09:25:58 completed / hb-a 09:40:55 completed / 开盘引擎 10:00:56 completed / hb-b 10:30:55 completed / hb-c 11:00:55 completed / hb-d 13:30:55 completed / hb-e 14:30:55 completed / 尾盘引擎 14:30:56 completed / deepb 14:45:55 **running(本场)**; 盘前另有 3 项 failed(release-stability-closeout / health-watchdog / ifind-keepalive), 与本场决策无因果关联, 仅登记。**本日 agent 场次 0 失败(compare 20261015: 4 场 provider 故障失败)。**",
   "结论": "引擎侧 3 个 no_agent 场次(09:25/10:00/14:30)全部 completed 并**落了 5 笔真实动作**; 5 个 agent 场次全部 completed。当日计划单已按 playbook 执行(2 承接 / 1 破位作废 / 2 开盘腿离场), 另有 1 笔**非预案内**的第七账自机制买入(002860)。"},
 "错失登记": miss,
 "错失结论": "playbook.buys 3 只中, **600668/605189 均落带并于 09:25 成交**(本日无 provider 故障, 承接链完整); **000530 因实开 gap -4.18% 越下沿 -4.0% 被闸门作废(设计内 miss)** —— 该票 10:21:15 起封板、锁定帧 7.62 = 涨停价(+9.96%) → **一miss错失**(承 hb-d『弃单机会成本立案』)。与 20261015『落带未执行』性质不同: 本日为闸门内设计性弃单, 非链路故障。",
 "预收盘第一手判断": {
   "口径": "20261015 涨停池 36 只『今日承接』, 锁 %s; **不外推全市场**(全市场温度/涨停/跌停/成交额等收盘口径指标此刻不可得, 由今晚盘后补全); 未含任何 >14:45:00 帧。" % last["ts"],
   "池截面": {"中位": round(st.median(pcts), 2), "均值": round(sum(pcts) / len(pcts), 3),
              "最低": min(pcts), "最高": max(pcts),
              "涨/跌": "%d/%d" % (sum(1 for p in pcts if p > 0), sum(1 for p in pcts if p < 0)),
              "≥+5%": sum(1 for p in pcts if p >= 5), "≥+3%": sum(1 for p in pcts if p >= 3),
              "≤-5%": sum(1 for p in pcts if p <= -5), "≤-3%": sum(1 for p in pcts if p <= -3),
              "封板": len(sealed), "炸板": len(broken), "跌停": len(dtl), "触板(含封)": len(touched)},
   "封板名单": [c + nm(c) + "%+.2f" % rows[c]["pct"] for c in sealed],
   "炸板名单": [c + nm(c) + "%+.2f" % rows[c]["pct"] for c in broken],
   "跌停名单": [c + nm(c) + "%+.2f" % rows[c]["pct"] for c in dtl],
   "日内轨迹": traj,
   "情绪定性": "**退潮第3日·尾盘加速下行且无修复(单边阴跌)** —— 池中位自 14:00 的 %.2f → 14:44 的 %.2f(再降 %.2fpp), 全日自 11:30 高点 %.2f 一路走低; 跌停家数 0(11:30)→3(13:30)→4(14:00)→**5**(14:44) 持续扩容; 封板 5 家全天未增(14:30 曾 6); 炸板 4. 尾盘无 ≥3只同步跳水(末窗达阈 0 批)亦无承接修复 → **退潮加深, 与 warboard『C防守(维持)』同向**。"
             % (traj["14:00"]["中位"], traj["14:44"]["中位"], traj["14:00"]["中位"] - traj["14:44"]["中位"], traj["11:30"]["中位"]),
   "主线": "**无 ≥4只成簇主线**。相对最强子线: **出版(2只)**: 601811新华文轩(2板·**封+10.01**) + 603999读者传媒(**封+9.97**) → 池内唯一『双封』线; 次强: 信创(003029 封+10.01)、物流(002889 封+9.99)、机械/冷链(000530 封+9.96)。反面: **PCB算力硬件线(4只: 002815/301282/002134/605058)全线杀跌**(002815 +0.90炸板、301282 -9.98跌停、002134 -9.98跌停、605058 -7.08) → 昨日 logic 路主推方向当日被证伪。",
   "龙头身位": "**高度天花板塌陷**: 5板双杀 —— 002696百洋股份 **跌停 -9.97%**、002343慈文传媒 +2.02%(炸板) → 5板以上**0 家存活**; 3板 001318阳光乳业 -8.49%(炸板未封) / 000530冰山冷热 封(+9.96, 但为弃单票); 2板 605189富春染织 -8.01% / **601811新华文轩 封(+10.01, 尾盘回封)**。⇒ 高度端『5板清空·3板杀1守1·2板守1杀1』, 梯队断裂, **新身位核心=601811 新华文轩(2板·出版·尾盘回封)**。",
   "龙头票错失对照": "600668(lhb路 双源一致·第1顺位)本场 **由封板转尾盘炸板**(09:32封→14:43炸, +5.63%): 09:25 已按闸门承接, 属**已参与**而非错失; 000530(auction路) **弃单后封板 +9.96%** = 本日唯一设计内错失。"},
 "明日预案要点": [
   "环境: 退潮第3日加深(池中位 %.2f / 跌停 5 / 封板 5 / 炸板 4; 14:30→14:44 中位再降 %.2fpp) + 高度天花板(5板)双杀清空 + 梯队断裂 → 明日**维持 C防守(总仓≤8%%、单笔≤5%%、≤2成)**, 不放开执行清单、不追高、不加仓、不新开第五条线(承 总审_20261015#总裁决 置信73)。warboard#checks 5 项 now=null, 待明晨 09:25 竞价场回应。" % (traj["14:44"]["中位"], traj["14:30"]["中位"] - traj["14:44"]["中位"]),
   "持仓处置优先级(建议): 002860(当日承接即炸板, 相对成本 %+.2f%%, 最高优先) > 605189(%+.2f%%) > 603968(%+.2f%%) > 600668(**尾盘炸板新增, 由盈转防**) > 000601(观察 %+.2f%%) > 000823(%+.2f%%) / 000011(浮盈 %+.2f%% 持有)。"
   % (pos7[1]["相对成本pct"], pos_m[1]["相对成本pct"], pos_m[3]["相对成本pct"], pos_m[2]["相对成本pct"], pos_m[4]["相对成本pct"], pos7[0]["相对成本pct"]),
   "**000011 收盘腿待判**: playbook 条件腿 a) 若 20261016 **收盘<今日开盘 %.2f** 成立 → 清仓腿生效, 须在 **14:57/收盘口径**复核并落入次日执行; 截至本场 %.2f > %.2f, 未成立。" % (pos7[0]["今日开"], pos7[0]["决断时点实价"], pos7[0]["今日开"]),
   "**600668 尾盘炸板处置**: 明日开盘按『断板即走』复核 —— 但**须先在 playbook 显式声明卖腿**, 否则按铁律仍不可落地(本日 playbook.sells 无 600668)。",
   "**卖通道缺失须 10/16 盘后定论(第8次登记, 结构性欠账)**: ①启用『盘中回应引擎-每日收盘14:57』(04066045b634, enabled=false); ②把防守了结写为第七账『次日卖出指令.json』(T+1 09:25 机械执行); ③master 账补一个消费 playbook.sells 的模块。本场不擅自改动(盘中禁改参数)。",
   "**引擎闸门字段未刷新须归因**(本场新增): 002860 的『闸门』文本三块全部沿用 10/15 的『低开-6.08%』, 与本日实况(高开 +9.68%)矛盾; 且 002860 为**非预案内、非 20261015 涨停池成员**的自机制买入 → 引擎是否应读预案、字段为何不刷新, 须盘后定论。",
   "watch 9 只本场 confirm 复核: **全部未成立**(见 watch_confirm核对) → 明日机械结算(002815 一字不可执行判据再坐实 / 300111·603230 未续封 / 001318·301282·002134·605058·600812·002945 均未达升级条件)。",
   "PCB算力硬件线(002815/301282/002134/605058)当日全线杀跌 → logic 路昨日主推方向 1 日内被证伪, 明日复核该线是否有修复或应整体降级。"],
 "watch_confirm核对": watch_cf,
 "后视镜边界声明": "本文件一切读数取自 ①realtime_ticks.jsonl 帧 ts ≤ %s(末合法帧) 与 ②hb-e 14:32:57~14:33:00 腾讯直取留档; 决断时点固定为 2026-10-16 14:45:00。realtime_ticks 中 ts>14:45:00 的 %d 帧(14:45:03~%s, 见数据新鲜度·排除帧)已排除于决策输入。**本文件不含任何 14:45:00 之后的信息, 也不含收盘口径数据。**" % (last["ts"], len(excluded), excluded[-1]),
 "异常与欠账": [
   "①**master 账本本日 0 回写**(第2次): 本日 2买2卖共 4 笔 master 动作无凭证, 状态.json 仍 date=20261015; 且 600693 卖出价 9.87=跌停价, 『成交与否』无回写核验。",
   "②**第七账 000011 买入记录重复**: 账本.jsonl 出现两条完全相同的 `buy 20261003 000011 5900@10.11 cost 59649.59`, 需去重(否则成本口径易被双计)。",
   "③**载体缺失**: 盘中/20261016/ 无 warboard.json(20261015 亦无)、无 pulse.json、无 执行流水.jsonl(三项契约未实现, 连续多日); 本场新建 报警_20261016.jsonl。",
   "④**卖通道缺失**(第8次): 14:57 收盘场 enabled=false + playbook.sells 无消费方 ⇒ master 只买不卖。",
   "⑤**持仓不可观测**(第8次): 7 只在持票中 5 只不在实时池(36票×%d合法帧 0命中) → 持仓级尾盘风控结构上不可判定; 唯一 ≤14:45 行情为 hb-e 14:33 留档(距决断 11分57秒, 略越 10 分钟红线)。" % len(legal),
   "⑥**引擎闸门字段未刷新**(本场新增): 002860 三个块的『闸门』文本逐字沿用 10/15 缓存值『低开-6.08%』, 与当日实况『高开+9.68%』矛盾。",
   "⑦**引擎自机制买入非预案票**(第2次): 002860 由引擎于 09:26 买入(依据判断流水『✓共振·可成交』), 非 playbook.buys、非 20261015 涨停池成员 → 归因与授权边界须盘后定论。",
   "⑧**判断流水 ts 月份退化**: 本日块读作『08-16』(应 10-16), 需修 ts 源方可机械检索(承前场)。",
   "⑨**hb-e 备料口径误记(本场更正)**: hb-e 14:30 记 600668『封板持有·无防守需求』, 本场实测 **14:43:02 已炸板** → 以本场发出版为准(发往他件不覆盖)。",
   "⑩**盘前 3 项 cron failed**: sentiment-release-stability-closeout / sentiment-review-health-watchdog / ifind-keepalive(08:4x) —— 与本场决策无因果关联, 仅登记。"],
 "口径": "五路定序/段落标序/A-C 分治 按技能规则; 本场为盘中作战尾盘段, 一切结论基于真实留档数据(零编造); 给判断不给指令; 报告对用户=参考, 非操盘指令。",
 "report": "深场B(14:45尾盘)：池内(1015涨停池36只承接)锁14:44:02 —— 封板5/炸板4/跌停5、中位-4.43(14:00 -3.50, 尾盘再降0.93pp)退潮第3日加深; 尾盘卖预案 **零触发**——sells仅3条(2条leg=open已于09:25执行完毕, 唯一leg=close=000011三条件均未达), 故 fills=[] 零成交; 在持7只逐票表态：000011 11.37(+12.46%相对成本)落『持有』、002860 18.63(-7.22%, 当日承接即炸板)、600668 ★14:43尾盘炸板8.44(由封板转炸)、605189 16.42(-8.63%)、603968 13.28(-7.13%)、000601 -2.99%、000823 +0.72%; 执行对账=引擎本日5笔真实动作(2承接/2开盘腿离场/1第七账自机制买002860)+1弃单, 全部completed、本日0场失败; **本场无任何尾盘成交动作**; 高度端5板双杀清空、新身位核心=601811新华文轩(2板·出版·尾盘回封)。",
}

os.makedirs(DAY, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT), "bytes")

# ---------- 报警 append-only ----------
alarms = [
 {"ts": NOW, "date": D, "session": "deepb", "level": "ALARM",
  "code": "sell_channel_absent_playbook_sells_unconsumed",
  "msg": "第8次: 盘中回应引擎-每日收盘14:57(id=04066045b634) enabled=false / last_dispatch=null + playbook.sells 无任何消费方 ⇒ master 账只买不卖, 一切 B 级防守结构上不可落地。本日 B 级通道A(3只)+通道C(2只)成立但零动作。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "ALARM",
  "code": "engine_gate_field_not_refreshed_002860",
  "msg": "本场新增: 判断流水本日 3 个块对 002860 的『闸门』字段逐字读作『低开-6.08%<5%』(=10/15 缓存值), 与本日实况『高开+9.68%』矛盾; 但『档位』按当日实况判为『✓共振·可成交』并据以 09:26 成交 ⇒ 同一行判据内部不自洽。影响: 依赖『闸门』文本的机械复核会误读。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "hold_quotes_slightly_stale_11m57s",
  "msg": "7 只在持票中 5 只不在实时池(36票×%d合法帧 0命中) → 唯一 ≤14:45 行情 = hb-e 14:32:57~14:33:00 直取留档, 距决断 11分57秒, **略越 10 分钟红线** → 按辅助读数使用并 WARN; 未补拉(>14:45 拉取属零后视镜违规)。" % len(legal)},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "master_ledger_not_written_back",
  "msg": "第2次: master 状态.json 仍 date=20261015(mtime 2026-10-15 20:36) → 本日 2买2卖共 4 笔无凭证; 600693 卖出 9.87=跌停价, 成交与否待引擎回写核验。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "ledger_duplicate_000011_buy",
  "msg": "第七账 账本.jsonl 存在两条完全相同的 buy 000011 5900@10.11(cost 59649.59, 20261003) → 需去重, 否则成本口径易被双计。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "contract_files_missing_and_ts_degeneration",
  "msg": "连续缺件: pulse.json / 执行流水.jsonl / warboard.json(20261015 与 20261016 均无); 判断流水 ts 本日块读作『08-16』(应10-16)退化; 日历契约 sentiment.core.calendar 不可导入(ModuleNotFoundError)。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "engine_auto_buy_non_playbook_ticket",
  "msg": "第2次: 002860 星帅尔由引擎 09:26 自机制买入 2900@20.08(第七账) —— 非 playbook.buys 票、非 20261015 涨停池成员; 归因与授权边界须盘后定论。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "tail_sell_plan_zero_trigger_zero_fill",
  "msg": "尾盘卖预案零触发: sells 3 条(600693/605577 leg=open 已于 09:25 执行; 000011 leg=close 三条件 −4%/+3%/收盘<开盘 均未达) ⇒ fills=[] 合法空集。"},
 {"ts": NOW, "date": D, "session": "deepb", "level": "WARN",
  "code": "hb_e_payload_miscount_corrected",
  "msg": "本场更正: hb-e 14:30 记 600668 尖峰集团『封板持有·无防守需求』, 本场实测 **14:43:02 尾盘炸板**(8.79→8.44, +5.63%), 通道C『持仓炸板』成立。发往他件不覆盖, 以本场发出版为准。"},
]
exist = os.path.exists(ALARM)
seen = set()
if exist:
    for line in open(ALARM, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            _a = json.loads(line)
        except Exception:
            continue
        if _a.get("date") == D and _a.get("session") == "deepb":
            seen.add(_a.get("code"))
todo = [a for a in alarms if a["code"] not in seen]
with open(ALARM, "a", encoding="utf-8", newline="\n") as f:
    for a in todo:
        f.write(json.dumps(a, ensure_ascii=False) + "\n")
print("ALARM", ("appended" if exist else "created"), ALARM, "本场清单=%d 新增=%d 已存在去重=%d" % (len(alarms), len(todo), len(seen)))
