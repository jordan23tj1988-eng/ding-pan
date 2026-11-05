# -*- coding: utf-8 -*-
"""hb-c 决断文件自审：独立重算 + 前视检查 + 一致性断言"""
import json, os, datetime, collections, re

D = r"D:\股票数据\市场数据\盘中\20261105"
fails, oks = [], []


def ck(name, cond, detail=""):
    (oks if cond else fails).append(f"{name} {detail}".strip())


d = json.load(open(os.path.join(D, "临盘决断_20261105_1100.json"), encoding="utf-8"))
pools = json.load(open(os.path.join(D, "_hb_c_pools_1100.json"), encoding="utf-8"))
quote = json.load(open(os.path.join(D, "_hb_c_quote_1100.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(D, "_hb_c_pos_trends_1100.json"), encoding="utf-8"))
ticks = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]

zt, zb, dt = pools["zt"], pools["zb"], pools["dt"]
ms = d["market_snapshot"]

ck("C-涨停数", ms["涨停"] == len(zt), f'{ms["涨停"]} vs {len(zt)}')
ck("C-炸板数", ms["炸板"] == len(zb), f'{ms["炸板"]} vs {len(zb)}')
ck("C-跌停数", ms["跌停"] == len(dt), f'{ms["跌停"]} vs {len(dt)}')
rate = round(len(zb) / (len(zt) + len(zb)), 4)
ck("C-炸板率", ms["炸板率"] == rate, f'{ms["炸板率"]} vs {rate}')
lb = dict(sorted(collections.Counter(x["lbc"] for x in zt).items()))
ck("C-连板分布", {int(k): v for k, v in ms["连板分布"].items()} == lb, f'{ms["连板分布"]} vs {lb}')
ck("C-二板加", ms["二板加"] == sum(1 for x in zt if x["lbc"] >= 2), f'{ms["二板加"]}')
ck("C-最高板", ms["最高板"] == max(x["lbc"] for x in zt), f'{ms["最高板"]}')

sh = quote["rows"]["sh000001"]["amt_wan"] / 10000
sz = quote["rows"]["sz399001"]["amt_wan"] / 10000
ck("C-半日成交额", abs(ms["半日成交额亿"]["合计"] - (sh + sz)) < 0.15, f'{ms["半日成交额亿"]["合计"]} vs {sh+sz:.1f}')
ck("C-成交额无重复计", ms["半日成交额亿"]["合计"] < 17000, f'{ms["半日成交额亿"]["合计"]}（应≈13290，非 17699）')

# 宽度末点 vs ticks 11:01 帧（文件 snapshot.ts=11:01；不拿 11:05 帧去比 11:01 快照）
def near(t):
    tt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    return min(ticks, key=lambda f: abs(datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") - tt))


f1101 = near("2026-11-05 11:01:00")
lastrows = {r["code"]: r for r in f1101["rows"]}
p = sorted(x["pct"] for x in lastrows.values())
ck("C-宽度末点", abs(ms["池内116只"]["均涨"] - sum(p) / len(p)) < 0.02 and len(p) == 116,
   f'帧{f1101["ts"]} {ms["池内116只"]["均涨"]} vs {sum(p)/len(p):.2f} n={len(p)}')
bt = d["breadth_trend"][-1]
ck("C-宽度趋势末行", abs(bt["mean"] - ms["池内116只"]["均涨"]) < 1e-9, f'{bt}')

# 决断时点内的最新帧读数（只作报告补记，不改 snapshot）
lr = sorted(x["pct"] for x in ticks[-1]["rows"])
print("LATEST_FRAME", ticks[-1]["ts"], "mean", round(sum(lr) / len(lr), 2), "red", sum(1 for v in lr if v > 0),
      "ge9.6", sum(1 for v in lr if v >= 9.6), "le-3", sum(1 for v in lr if v <= -3))

# 持仓：股数与 master 状态一致 + 盈亏重算
state = json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\状态.json", encoding="utf-8"))
shares = {x["code"]: x["shares"] for x in state["持仓"]}
for pos in d["positions"]:
    if pos["shares"] == 0:
        continue
    c = pos["code"]
    ck(f"C-持仓{c}股数", shares.get(c) == pos["shares"], f'{pos["shares"]} vs {shares.get(c)}')
    ck(f"C-持仓{c}价", abs(pos["px"] - tr[c]["last_px"]) < 1e-9, f'{pos["px"]}')
    exp = round((pos["px"] / pos["cost_px"] - 1) * 100, 2)
    ck(f"C-持仓{c}盈亏", abs(pos["pnl_pct"] - exp) <= 0.02, f'{pos["pnl_pct"]} vs {exp}')

mv = sum(x["px"] * x["shares"] for x in d["positions"] if x["shares"])
cash = 929536.38 + 16200.0
ck("C-净值算术", abs(d["nav_estimate"]["本场估算"] - (cash + mv)) < 0.02, f'{d["nav_estimate"]["本场估算"]} vs {cash+mv:.2f}')

# 前视检查：决断时点晚于文件中记录的所有引用数据时点（不用仍在增长的 ticks 实时末帧）
dec = datetime.datetime.strptime(d["决断时点"][:19], "%Y-%m-%d %H:%M:%S")
fdf = d["data_freshness"]
ts_used = [datetime.datetime.strptime(fdf["realtime_ticks_last"], "%Y-%m-%d %H:%M:%S"),
           datetime.datetime.strptime(fdf["quote_fetched"], "%Y-%m-%d %H:%M:%S"),
           datetime.datetime.strptime(fdf["pools_fetched"], "%Y-%m-%d %H:%M:%S"),
           datetime.datetime.strptime(tr["600299"]["last_t"], "%Y-%m-%d %H:%M")]
ck("C-无前视", all(dec >= t for t in ts_used), f'决断 {dec} vs 最大引用时点 {max(ts_used)}')
ck("C-记录帧时点<决断", fdf["realtime_ticks_last"] < d["决断时点"][:19], f'{fdf["realtime_ticks_last"]}')
ck("C-tick断更<10min", d["data_freshness"]["gap_min"] < 10, f'{d["data_freshness"]["gap_min"]} 分')

ck("C-无动作一致性", d["fills"] == [] and "无动作" in d["权限级别"] and d["no_action"] == "心跳hb-c无动作", "")
ck("C-无占位残留", not re.search(r"\{[a-z_]+\}|None|nan", d["reason"]), "")
ck("C-必填字段", all(k in d for k in ("date", "session", "决断时点", "权限级别", "fill_frame", "fills",
                                      "data_freshness", "market_snapshot", "positions", "nav_estimate",
                                      "conditional_watch", "account_integrity", "修订记录")), "")

# 半导体名单归属
semi_zb = [x["n"] for x in zb if x.get("hybk") == "半导体"]
ck("C-半导体炸板名单", all(n in d["reason"] for n in semi_zb), f'{semi_zb}')
ck("C-昭衍新药未入半导体句", "昭衍新药" not in d["reason"].split("半导体链")[1][:80] if "半导体链" in d["reason"] else True, "")

print("=== FAIL", len(fails), "===")
for f in fails:
    print(" FAIL", f)
print("=== PASS", len(oks), "===")
for o in oks:
    print("  ok", o)
print("VERDICT", "PASS" if not fails else "FAIL")
