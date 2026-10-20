# -*- coding: utf-8 -*-
"""20261020 深场B(hb-f) 哨兵: 对发出版决断件/补正件/尾盘复盘做真实数据自审。FAIL 不算完。"""
import json, os, io, statistics, datetime, re

BASE = r"D:\股票数据\市场数据"
D = os.path.join(BASE, "盘中", "20261020")
J = os.path.join(D, "临盘决断_20261020_1445.json")
FIX = os.path.join(D, "临盘决断_20261020_1445_补正1.json")
MD = os.path.join(BASE, "_学习", "盘中尾盘复盘_20261020.md")
res = []

def chk(name, cond, detail=""):
    res.append((name, bool(cond), detail))

d = json.load(io.open(J, encoding="utf-8"))
fix = json.load(io.open(FIX, encoding="utf-8"))
md = io.open(MD, encoding="utf-8").read()
qs = json.load(io.open(os.path.join(D, "_b1445_quote.json"), encoding="utf-8"))
Q = qs["rows"]

# --- 帧 ---
fr = []
for line in io.open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8", errors="ignore"):
    line = line.strip()
    if line:
        try:
            fr.append(json.loads(line))
        except Exception:
            pass
frame = {f["ts"]: f for f in fr}
last_ts = d["盘中截面序列"]["末帧"]["ts"]
write_ts = datetime.datetime.strptime(d["write_ts"], "%Y-%m-%d %H:%M:%S")

# S1
chk("S1 决断件/补正件/复盘件三件齐备且可解析", all(os.path.exists(p) for p in (J, FIX, MD)),
    f"{os.path.getsize(J)}/{os.path.getsize(FIX)}/{os.path.getsize(MD)} bytes")

# S2 必需块
need = ["交易日校验", "数据新鲜度", "盘中截面序列", "截面判读", "预案核对", "条件决断",
        "在持票逐票表态", "观察票照会", "当日第一手判断", "明日预案要点", "撮合口径",
        "权限分级", "异常与欠账", "证据快照", "写校说明"]
miss = [k for k in need if k not in d]
chk("S2 必需块齐全", not miss, "缺=" + str(miss))

# S3 末帧 ≤ 决断 且 ≤10 分钟
lf = datetime.datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
chk("S3 末帧早于决断时间戳且帧龄≤10分钟", lf <= write_ts and (write_ts - lf).total_seconds() <= 600,
    f"末帧={lf} 决断={write_ts} 差={(write_ts-lf).total_seconds():.0f}s")

# S4 所有行情戳 ≤ 决断
bad = [(k, v["t"]) for k, v in Q.items()
       if datetime.datetime.strptime(v["t"], "%Y%m%d%H%M%S") > write_ts]
chk("S4 全部行情戳 ≤ 决断时间戳(无后视镜)", not bad, str(bad))

# S5 在持票覆盖 + 浮盈重算
st = json.load(io.open(os.path.join(BASE, "_学习/_模拟盘/master/状态.json"), encoding="utf-8"))
book = {p["code"]: p for p in st["持仓"]}
held = {x["code"]: x for x in d["在持票逐票表态"]}
# 600668 今日已清仓, 账本仍记 6100 → 需在文件内出现
chk("S5a 账本在持票全部表态(000601/000823/600668)", set(book) <= set(held),
    f"账本={sorted(book)} 表态={sorted(held)}")
err = []
for c in ("000601", "000823"):
    x = held[c]
    px = Q[("sz" if c[0] == "0" else "sh") + c]["px"]
    exp_mv = round(px * x["shares"], 2)
    # 从文字中反解市值
    m = re.search(r"市值 ([\d,\.]+)", x["浮盈"])
    if not m:
        err.append((c, "浮盈字段无市值"))
        continue
    got = float(m.group(1).replace(",", ""))
    if abs(got - exp_mv) > 0.02:
        err.append((c, "市值", got, exp_mv))
chk("S5b 在持票市值与报价×股数重算一致", not err, str(err))

# 成本重算
err2 = []
cost_exp = {"000601": 40100.04, "000823": round(20114.05 / 2, 2)}
for c, v in cost_exp.items():
    m = re.search(r"浮[盈亏] ([+-][\d,\.]+)", held[c]["浮盈"])
    mv = float(re.search(r"市值 ([\d,\.]+)", held[c]["浮盈"]).group(1).replace(",", ""))
    if m:
        pnl = float(m.group(1).replace(",", ""))
        if abs((mv - pnl) - v) > 0.05:
            err2.append((c, mv, pnl, v))
chk("S5c 成本反解一致(mv-pnl==cost; 000823 半仓成本)", not err2, str(err2))

# S6 仓位/NAV
mv_total = sum(round(Q[("sz" if c[0] == "0" else "sh") + c]["px"] * held[c]["shares"], 2) for c in ("000601", "000823"))
cash_txt = d["仓位上账(估算, 待结算回填)"]["现金"]
cash = float(re.search(r"([\d,]+\.\d+) = master", cash_txt).group(1).replace(",", ""))
nav = float(re.search(r"NAV\": \"([\d,\.]+)", json.dumps(d, ensure_ascii=False)).group(1).replace(",", ""))
chk("S6a NAV = 现金+市值 重算一致", abs(nav - (cash + mv_total)) < 0.02, f"nav={nav} cash+mv={cash+mv_total}")
pos = round(mv_total / nav * 100, 2)
m = re.search(r"仓位\": \"([\d\.]+)%", json.dumps(d, ensure_ascii=False))
chk("S6b 仓位比例一致", m and abs(float(m.group(1)) - pos) < 0.02, f"file={m.group(1) if m else None} calc={pos}")
chk("S6c 现金基数可溯源(master 882,632.75 + 今日毛成交 58,294)",
    "882,632.75" in cash_txt and ("58,294" in cash_txt or "58294" in cash_txt), cash_txt[:60])

# S7 池内截面重算(末帧)
f = frame[last_ts]
def lim(pre, code):
    return round(pre * (1 + (0.2 if code.startswith(("30", "68")) else 0.1)), 2)
seal = [r for r in f["rows"] if r["latest"] >= lim(r["preClose"], r["code"]) - 0.005]
zb = [r for r in f["rows"] if r["high"] >= lim(r["preClose"], r["code"]) - 0.005 and r not in seal]
med = round(statistics.median([r["pct"] for r in f["rows"]]), 2)
up = sum(1 for r in f["rows"] if r["pct"] > 0)
dn = sum(1 for r in f["rows"] if r["pct"] < 0)
sl = d["盘中截面序列"]["末帧"]
chk("S7 末帧截面(封板/炸板/涨跌/中位)重算一致",
    (sl["seal"], sl["zb"], sl["up"], sl["dn"], sl["median"]) == (len(seal), len(zb), up, dn, med),
    f"file={(sl['seal'],sl['zb'],sl['up'],sl['dn'],sl['median'])} calc={(len(seal),len(zb),up,dn,med)}")

# S8 预案腿核销
pb = json.load(io.open(os.path.join(BASE, "盘中", "20261019", "playbook.json"), encoding="utf-8"))
pb_codes = {s["代码"] for s in pb["sells"]}
file_codes = {s["code"] for s in d["预案核对"]["sells"]}
chk("S8a 预案 3 条卖腿全部逐条核销", pb_codes == file_codes, f"预案={pb_codes} 文件={file_codes}")
chk("S8b leg=close / take_zt 计数为 0 且与预案一致",
    d["预案核对"]["leg_close计数"] == 0 and d["预案核对"]["take_zt_count"] == 0
    and all(s["腿"] == "open" for s in pb["sells"]), str([s["腿"] for s in pb["sells"]]))

# S9 零成交自洽
chk("S9 fills=[] 且无 px_exec 伪造",
    d["条件决断"]["fills"] == [] and d["条件决断"]["买入"] == [] and d["条件决断"]["卖出"] == []
    and "无 px_exec" in d["撮合口径"]["本场"],
    d["撮合口径"]["本场"])
# 000601 距线算术
e = Q["sz000601"]
dist = round((e["px"] - 6.24) / 6.24 * 100, 2)
chk("S9b 000601 距止损线算术一致(+0.80%)", abs(dist - 0.80) < 0.02, f"px={e['px']} dist={dist}%")
chk("S9c 止损条件只引预案明文", "playbook.json#notes④" in json.dumps(d["条件决断"], ensure_ascii=False), "")

# S10 复盘件与决断件同源
chk("S10a 复盘件含末帧数值且与决断件一致",
    f"| **{last_ts[11:16]}（末帧）** |" in md and f"**{sl['median']}**" in md, last_ts)
chk("S10b 复盘件声明『待盘后补』且不冒充收盘口径",
    "待盘后补" in md and "不用 15:00 后数据回填" in md, "")
chk("S10c 复盘件未出现『收盘涨停家数=』类收盘口径数值",
    not re.search(r"收盘涨停\s*=?\s*\d+\s*家", md), "")

# S11 补正件『原文』可回溯
src = json.dumps(d, ensure_ascii=False).replace("%%", "%")  # 归一化已知 %% 格式缺陷(见补正2)
bad2 = []
for it in fix["条目"]:
    parts = [p.strip().replace("%%", "%") for p in it["原文"].split("…") if p.strip()]
    miss2 = [p for p in parts if p not in src]
    if miss2:
        bad2.append((it["字段"], miss2[0][:40]))
chk("S11 补正件每条『原文』均可在原决断件中回溯", not bad2, str(bad2))

# S12 欠账如实登记
debt = json.dumps(d["异常与欠账"], ensure_ascii=False)
chk("S12 三缺/账实不符/口径冲突 均已登记",
    all(k in debt for k in ("pulse.json", "warboard.json", "执行流水", "800 股", "6.45")), "")

# S13 覆盖检测: 同目录不得有第二个 1445 决断件
dup = [x for x in os.listdir(D) if x.startswith("临盘决断_20261020_1445") and x.endswith(".json")]
chk("S13 1445 决断件唯一(无覆盖)", sorted(dup) == ["临盘决断_20261020_1445.json", "临盘决断_20261020_1445_补正1.json", "临盘决断_20261020_1445_补正2.json"], str(dup))

# S14 '%%' 格式缺陷是否被补正2 全量登记
fix2 = json.load(io.open(os.path.join(D, "临盘决断_20261020_1445_补正2.json"), encoding="utf-8"))
paths = []
def _walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            _walk(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _walk(v, path + "[%d]" % i)
    elif isinstance(o, str) and "%%" in o:
        paths.append(path)
_walk(d)
chk("S14 决断件 '%%' 格式缺陷被补正2 全量登记(条数+路径一致)",
    sorted(paths) == sorted(it["路径"] for it in fix2["条目"]) and len(paths) > 0,
    f"实际={len(paths)} 登记={len(fix2['条目'])} 未登记={sorted(set(paths)-set(it['路径'] for it in fix2['条目']))}")

fails = [r for r in res if not r[1]]
for n, ok, det in res:
    print(("PASS " if ok else "FAIL ") + n + (("  | " + det) if (det and not ok) else ""))
print("\nTOTAL %d  PASS %d  FAIL %d" % (len(res), len(res) - len(fails), len(fails)))
io.open(os.path.join(D, "_hb_f_sentinel.out"), "w", encoding="utf-8").write(
    "\n".join(("PASS " if ok else "FAIL ") + n + (("  | " + det) if det else "") for n, ok, det in res)
    + "\n\nTOTAL %d PASS %d FAIL %d\n" % (len(res), len(res) - len(fails), len(fails)))
raise SystemExit(1 if fails else 0)
