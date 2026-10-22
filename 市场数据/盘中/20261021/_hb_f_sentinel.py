# -*- coding: utf-8 -*-
"""hb-f 自审哨兵: 复算 + 一致性 + 口径缺陷扫描"""
import json, os, re, statistics, csv

D = r"D:\股票数据\市场数据\盘中\20261021"
MD = r"D:\股票数据\市场数据\_学习\盘中尾盘复盘_20261021.md"
fail, warn = [], []

j = json.load(open(os.path.join(D, "临盘决断_20261021_1445.json"), encoding="utf-8"))
fix = json.load(open(os.path.join(D, "临盘决断_20261021_1445_补正1.json"), encoding="utf-8"))
q = json.load(open(os.path.join(D, "_hb_f_quote_exec.json"), encoding="utf-8"))["rows"]
raw_txt = open(os.path.join(D, "临盘决断_20261021_1445.json"), encoding="utf-8").read()

# C1 格式缺陷
if "%%" in raw_txt:
    fail.append("C1 存在 %% 格式缺陷")
if re.search(r"NaN|Infinity", raw_txt):
    fail.append("C1 存在 NaN/Infinity")

# C2 fills 复算
for f in j["条件决断"]["fills"]:
    px, ex, qty = f["px"], f["px_exec"], f["qty"]
    if round(px * 0.999, 2) != ex:
        fail.append(f"C2 {f['code']} px_exec 不等于 px×0.999 → {round(px*0.999,2)} vs {ex}")
    if qty % 100 != 0:
        fail.append(f"C2 {f['code']} 股数非100整数倍")
    cost = {"000601": 6.68 * 6000, "000823": 25.13 * 800}[f["code"]]
    pnl = round((ex - {"000601": 6.68, "000823": 25.13}[f["code"]]) * qty, 2)
    if abs(pnl - f["pnl_gross"]) > 0.01:
        fail.append(f"C2 {f['code']} pnl {pnl} vs 声明 {f['pnl_gross']}")
    ret = round((ex / {"000601": 6.68, "000823": 25.13}[f["code"]] - 1) * 100, 2)
    if abs(ret - f["ret_pct"]) > 0.01:
        fail.append(f"C2 {f['code']} ret {ret} vs 声明 {f['ret_pct']}")
    if abs(pnl / cost * 100 - f["ret_pct"]) > 0.02:
        fail.append(f"C2 {f['code']} ret 与 pnl/cost 不一致")

# C3 与源帧一致
if j["条件决断"]["fills"][0]["px"] != q["sz000601"]["px"]:
    fail.append("C3 000601 决断帧价与 quote 文件不符")
if j["条件决断"]["fills"][1]["px"] != q["sz000823"]["px"]:
    fail.append("C3 000823 决断帧价与 quote 文件不符")

# C4 NAV 复算
nav_txt = j["仓位上账(估算, 待结算回填)"]["NAV"]
nav_calc = round((932054.28 + 6.35 * 6000 + 23.92 * 800) / 1e6, 6)
if f"{nav_calc}" not in nav_txt:
    fail.append(f"C4 NAV 复算 {nav_calc} 未出现在声明文本: {nav_txt[:60]}")
cash_calc = round(932054.28 + 6.35 * 6000 + 23.92 * 800, 2)
print("复算 NAV", nav_calc, "现金", cash_calc, "→ 涨幅", round((nav_calc - 1) * 100, 2), "%")

# C5 截面数字与源一致
ser = json.load(open(os.path.join(D, "_hb_f_series.json"), encoding="utf-8"))["series"]
for k, lab in (("LAST", "LAST"), ("14:15", "14:15"), ("14:33", "14:33")):
    s = ser[k]
    row = j["盘中截面序列"][lab]
    for fld in ("up", "dn", "median", "seal", "zb"):
        if row[fld] != s[fld]:
            fail.append(f"C5 截面 {lab}.{fld} 不一致 {row[fld]} vs {s[fld]}")

# C6 尾盘回吐数值
drop = round(ser["14:15"]["median"] - ser["LAST"]["median"], 2)
if abs(drop - 1.62) > 0.02:
    warn.append(f"C6 尾盘回吐复算 {drop} ≠ 文本 -1.62pp")

# C7 预案数与账本
pb = json.load(open(os.path.join(D, "playbook.json"), encoding="utf-8"))
legs = [s["leg"] for s in pb["sells"]]
if legs.count("close") != j["预案核对"]["leg_close计数"]:
    fail.append("C7 leg=close 计数与 playbook 不符")
if legs.count("take_zt") != j["预案核对"]["take_zt_count"]:
    fail.append("C7 take_zt 计数与 playbook 不符")
led = [json.loads(l) for l in open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\账本.jsonl", encoding="utf-8") if l.strip()]
n21 = len([r for r in led if r.get("d") == "20261021"])
if n21 != 0:
    fail.append(f"C7 账本今日已有 {n21} 条 → 幂等判定需重算")

# C8 md 与 json 数字一致
md = open(MD, encoding="utf-8").read()
for tok in ("6.35", "23.92", "-1,980", "-968", "+3.74%", "31.6%", "3704.82", "2684.67", "23.05", "15.8%"):
    if tok not in md:
        fail.append(f"C8 md 缺关键数字 {tok}")
if "-968.0（-4.82%）" in md or "-968.0（-4.82%）" in raw_txt:
    fail.append("C8 仍有 -4.82% 残留（000823 浮盈行）")
print("  C8 提示: 补正件/复盘第八节中 `-4.82%` 为笔误引用(反引号内), 属合法引用, 不计 FAIL")

# C9 发出版存在性与产物齐全
for fn in ("临盘决断_20261021_1445.json", "临盘决断_20261021_1445_补正1.json",
           "_hb_f_quote_exec.json", "_hb_f_quote_postcheck.json", "_hb_f_series.json"):
    p = os.path.join(D, fn)
    if not os.path.exists(p):
        fail.append(f"C9 缺产物 {fn}")
    else:
        print(f"  {fn:44s} {os.path.getsize(p):>7d} B  mtime={__import__('datetime').datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M:%S')}")

# C10 报警件条数
n_alarm = sum(1 for l in open(os.path.join(D, "报警_20261021.jsonl"), encoding="utf-8") if l.strip())
if n_alarm != 5:
    warn.append(f"C10 报警条数 {n_alarm}（预期 5）")

print("\n=== WARN ===")
for w in warn:
    print(" W:", w)
print("=== FAIL ===")
for f in fail:
    print(" F:", f)
print("\n判定:", "PASS" if not fail else "FAIL")
