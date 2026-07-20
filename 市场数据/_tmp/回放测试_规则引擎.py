# -*- coding: utf-8 -*-
"""_tmp/回放测试_规则引擎.py — 一次性回放测试(#029, 阶段②A)
真实tick样本 = 盘中/20260718/watch.jsonl 首行(0718自测真数: 代码/价格/涨幅/涨跌停封板价全真)。
在 盘中/99990101/(日期明标TEST,不碰真实日期目录) 用真实价位铺多tick时间线 + 合成playbook,跑 --replay 断言。
场景: S0 9:25前诱单tick无视 / S1 trigger区间成交 / S2 高开abort / S3 涨停一字禁追 / S4 止损触发
      S5 跌停封死顺延 / S6 炸板即卖 / S7 自由文本unparsed_skip+watch留人判 / S8 abort_if跌破开盘价-3%
      S9 断更报警 / S10 幂等重跑 / S11 滑点与整手 / S12 stop_pct缺ref_px→unparsed_skip(v1.9.1裁定,零编造)
"""
import os, sys, json, glob, subprocess

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

SRC = os.path.join(BASE, "盘中", "20260718", "watch.jsonl")
TD = "99990101"
TDIR = os.path.join(BASE, "盘中", TD)
os.makedirs(TDIR, exist_ok=True)

real = json.loads(open(SRC, encoding="utf-8").readline())["t"]
SRC2 = os.path.join(BASE, "盘中", "20260718", "auction_traj.jsonl")
for _k, _v in json.loads(open(SRC2, encoding="utf-8").readline())["t"].items():
    real.setdefault(_k, _v)   # 两个真实样本文件合并取数(watch优先)
CODES = ["605179", "300105", "002432", "600629", "000566", "603580", "600436", "600332", "300146"]
P = {c: real[c][0] for c in CODES}                                   # 真实latest
PRE = {c: round(real[c][0] / (1 + real[c][1] / 100.0), 2) for c in CODES}  # 真实昨收(反推)

def row(ts, quotes):
    return json.dumps({"ts": ts, "t": {c: [p, round((p / PRE[c] - 1) * 100, 4)] for c, p in quotes.items()}},
                      ensure_ascii=False)

ZT2432, ZT3580, DT0566 = P["002432"], P["603580"], P["000566"]  # 79.20涨停/44.92涨停/5.10跌停(真实封板价)
auction = [
    row("09:24:00", {"605179": round(PRE["605179"] * 1.09, 2)}),   # S0 诱单段: 引擎必须无视(+9%越界也不许弃单)
    row("09:25:10", {"605179": P["605179"], "300105": P["300105"], "002432": ZT2432,
                     "600629": P["600629"], "000566": DT0566, "603580": ZT3580,
                     "600436": P["600436"], "600332": P["600332"]}),
]
watch = [
    row("09:30:05", {"605179": 14.70, "600629": 12.35, "000566": DT0566, "603580": ZT3580,
                     "600436": 147.00, "600332": 21.40}),
    row("09:31:00", {"603580": ZT3580, "000566": DT0566}),
    row("09:40:00", {"603580": 44.50, "000566": DT0566}),   # S6 603580炸板(触发tick)
    row("09:40:30", {"603580": 44.30}),                       # S6 下一tick → fill_sell
    row("10:00:00", {"000566": DT0566}),
    row("10:20:00", {"000566": DT0566}),                      # S9 与上行差20分钟 → data_gap
    row("14:50:00", {"000566": DT0566}),
]
open(os.path.join(TDIR, "auction_traj.jsonl"), "w", encoding="utf-8").write("\n".join(auction) + "\n")
open(os.path.join(TDIR, "watch.jsonl"), "w", encoding="utf-8").write("\n".join(watch) + "\n")

playbook = {"date": TD, "route": "master", "cash_pct": 30, "notes": "TEST合成预案(价位=0718真实样本)",
  "buys": [
    {"code": "605179", "name": "样本605179", "weight_pct": 20, "reason": "S1区间成交",
     "trigger": {"type": "open_range", "min_gap": -3, "max_gap": 5}},
    {"code": "300105", "name": "样本300105", "weight_pct": 10, "reason": "S2高开弃",
     "trigger": {"type": "open_range", "min_gap": -3, "max_gap": 5}},
    {"code": "002432", "name": "样本002432", "weight_pct": 10, "reason": "S3一字禁追",
     "trigger": {"type": "open_range", "min_gap": -3, "max_gap": 12}},
    {"code": "600436", "name": "样本600436", "weight_pct": 10, "reason": "S7自由文本abort_if",
     "trigger": {"type": "open_range", "min_gap": -3, "max_gap": 5},
     "intraday": {"abort_if": "感觉不对就撤"}},
    {"code": "600332", "name": "样本600332", "weight_pct": 10, "reason": "S8跌破开盘价放弃",
     "trigger": {"type": "open_range", "min_gap": -3, "max_gap": 5},
     "intraday": {"abort_if": "跌破开盘价-3%"}},
  ],
  "sells": [
    {"code": "600629", "name": "样本600629", "leg": "open", "intraday": {"stop_pct": -5, "ref_px": PRE["600629"]}},
    {"code": "000566", "name": "样本000566", "leg": "open", "intraday": {"stop_pct": -8, "ref_px": PRE["000566"]}},
    {"code": "603580", "name": "样本603580", "leg": "open", "intraday": {"stop_pct": None, "take_zt": "炸板即卖"}},
    {"code": "600601", "name": "样本600601", "leg": "open", "intraday": {"stop_pct": -6}},  # S12 缺ref_px→skip留人判
  ],
  "watch": [{"code": "300146", "name": "样本300146", "if": "放量过前高", "then": "检查点可升级买入,weight≤10"}]}
json.dump(playbook, open(os.path.join(TDIR, "playbook.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for fn in ("执行流水.jsonl", "alerts.jsonl", "rule_engine.log"):   # 清上次测试产物(仅TEST目录)
    p = os.path.join(TDIR, fn)
    if os.path.isfile(p): os.remove(p)

ENG = os.path.join(BASE, "盘中规则引擎.py")
r1 = subprocess.run([sys.executable, ENG, TD, "--replay"], capture_output=True, text=True, cwd=BASE)
if r1.returncode != 0:
    print("引擎退出码", r1.returncode, r1.stderr[-800:]); sys.exit(2)

FLOWP = os.path.join(TDIR, "执行流水.jsonl"); ALERTP = os.path.join(TDIR, "alerts.jsonl")
flow = [json.loads(l) for l in open(FLOWP, encoding="utf-8")]
alerts = [json.loads(l) for l in open(ALERTP, encoding="utf-8")] if os.path.isfile(ALERTP) else []
n1 = len(flow)
r2 = subprocess.run([sys.executable, ENG, TD, "--replay"], capture_output=True, text=True, cwd=BASE)  # S10 幂等
flow2 = [json.loads(l) for l in open(FLOWP, encoding="utf-8")]

def ev(code, action, rule_part=""):
    return [r for r in flow if r["code"] == code and r["action"] == action and rule_part in (r["rule"] or "")]

R = []
def chk(name, cond, detail=""):
    R.append((name, bool(cond), detail))

f1 = ev("605179", "fill_buy")
chk("S0 9:25前诱单tick被无视", not [r for r in flow if r["ts"] == "09:24:00"])
chk("S1 竞价确认confirm@09:25:10", ev("605179", "confirm") and ev("605179", "confirm")[0]["ts"] == "09:25:10")
chk("S1 下一tick价成交14.70@09:30:05", f1 and f1[0]["px"] == 14.70 and f1[0]["ts"] == "09:30:05",
    str(f1[:1]))
chk("S1 禁用触发tick自身价", not [r for r in f1 if r["ts"] == "09:25:10"])
chk("S2 高开gap越界abort且无成交", ev("300105", "abort", "trigger") and not ev("300105", "fill_buy"))
chk("S3 涨停一字禁追abort且无成交", ev("002432", "abort", "zt_no_chase") and not ev("002432", "fill_buy"))
f4 = ev("600629", "fill_sell", "stop_pct")
chk("S4 止损触发confirm(rule=stop_pct:-5)", ev("600629", "confirm", "stop_pct:-5"))
chk("S4 止损下一tick成交12.35", f4 and f4[0]["px"] == 12.35 and f4[0]["ts"] == "09:30:05")
chk("S5 跌停封死defer顺延且全日无成交", ev("000566", "defer", "stop_pct") and not ev("000566", "fill_sell"))
f6 = ev("603580", "fill_sell", "take_zt")
chk("S6 炸板即卖confirm@09:40:00", ev("603580", "confirm", "take_zt") and ev("603580", "confirm", "take_zt")[0]["ts"] == "09:40:00")
chk("S6 炸板下一tick成交44.30", f6 and f6[0]["px"] == 44.30 and f6[0]["ts"] == "09:40:30")
chk("S6 持仓炸板报警", any(a["type"] == "pos_zt_break" and a["code"] == "603580" for a in alerts))
chk("S7 自由文本abort_if→unparsed_skip", [r for r in flow if r["code"] == "600436" and r["action"] == "skip" and r["rule"] == "unparsed_skip"])
chk("S7 该票结构化部分照常成交147.00", ev("600436", "fill_buy") and ev("600436", "fill_buy")[0]["px"] == 147.00)
chk("S7 watch观察项skip留人判", [r for r in flow if r["code"] == "300146" and r["action"] == "skip" and r["rule"] == "watch"])
chk("S8 abort_if跌破开盘价-3%放弃且无成交", ev("600332", "abort", "abort_if:跌破开盘价") and not ev("600332", "fill_buy"))
chk("S9 断更>3分钟data_gap报警", any(a["type"] == "data_gap" for a in alerts))
chk("S10 幂等: 重跑流水不增行", len(flow2) == n1, "%d→%d" % (n1, len(flow2)))
chk("S11 滑点0.10%落px_exec", f1 and f1[0].get("px_exec") == round(14.70 * 1.001, 4))
chk("S11 整手取整13500股(20%/100万)", f1 and f1[0].get("qty") == 13500, str(f1[0].get("qty") if f1 else None))
s12 = [r for r in flow if r["code"] == "600601" and r["action"] == "skip" and r["rule"] == "unparsed_skip"
       and "缺ref_px" in (r.get("note") or "")]
chk("S12 stop_pct缺ref_px→unparsed_skip留人判且无卖出动作", s12 and not ev("600601", "confirm") and not ev("600601", "fill_sell"))

ok = 0
print("\n===== 回放测试清单 =====")
for name, passed, det in R:
    print("%s  %s %s" % ("PASS" if passed else "FAIL", name, ("| " + det) if (det and not passed) else ""))
    ok += passed
print("===== %d/%d PASS =====" % (ok, len(R)))
print("\n流水样例:")
for r in flow[:20]:
    if r["action"] in ("confirm", "fill_buy", "fill_sell", "defer", "abort"):
        print(" ", json.dumps(r, ensure_ascii=False))
sys.exit(0 if ok == len(R) else 1)
