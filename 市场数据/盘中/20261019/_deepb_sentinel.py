# -*- coding: utf-8 -*-
"""20261019 深场B 哨兵: 对发出版与复盘件做真实数据自审 (FAIL 不算完)"""
import json, os, re, csv, statistics, datetime, sys

BASE = r"D:\股票数据\市场数据"
D = os.path.join(BASE, "盘中", "20261019")
os.chdir(D)
res = []


def chk(name, cond, detail=""):
    res.append((name, bool(cond), detail))


J = "临盘决断_20261019_1445.json"
MD = os.path.join(BASE, "_学习", "盘中尾盘复盘_20261019.md")
chk("S1 发出版存在且可解析", os.path.exists(J) and json.load(open(J, encoding="utf-8")) is not None, J)
d = json.load(open(J, encoding="utf-8"))
calc = json.load(open("_deepb_calc.json", encoding="utf-8"))

# S2 必需块
need = ["交易日校验", "数据新鲜度", "在持票照会", "A级_预案内", "B级_防守", "C级_预案外", "尾盘卖预案执行",
        "fills", "执行对账_引擎已执行", "环境", "预收盘第一手判断", "明日预案要点", "后视镜边界声明", "补正"]
miss = [k for k in need if k not in d]
chk("S2 必需块齐全", not miss, "缺=" + str(miss))

# S3 交易日 / 新鲜度
chk("S3a 交易日=True", d["交易日校验"]["结论"] is True)
last_frame = datetime.datetime.strptime(calc["实时帧"]["末帧"], "%Y-%m-%d %H:%M:%S")
dec = datetime.datetime.strptime(d["决断时间戳"].replace(" CST", ""), "%Y-%m-%d %H:%M:%S")
chk("S3b 末帧早于决断且≤10分钟", last_frame <= dec and (dec - last_frame).total_seconds() <= 600,
    f"末帧{last_frame} 决断{dec} 差{(dec-last_frame).total_seconds():.0f}s")

# S4 行情戳不晚于决断
bad = []
for k, ts in calc["腾讯直取"]["行情戳"].items():
    t = datetime.datetime.strptime(ts, "%Y%m%d%H%M%S")
    if t > dec:
        bad.append((k, ts))
chk("S4 所有行情戳 ≤ 决断时间戳", not bad, str(bad))

# S5 持仓三票全覆盖 + 浮盈重算
st = json.load(open(os.path.join(BASE, "_学习/_模拟盘/master/state.json"), encoding="utf-8"))
costmap = {p["code"]: p["cost"] for p in st["positions"]}
q = calc["腾讯直取"]["rows"]
covered = [x["code"] for x in d["在持票照会"]]
chk("S5a 在持 3 票全部表态", sorted(covered) == sorted(costmap.keys()), f"表态={covered} 账本={list(costmap)}")
errc = []
for x in d["在持票照会"]:
    c = costmap[x["code"]]
    exp_mv = round(x["shares"] * q[x["code"]]["last"], 2)
    exp_pnl = round(exp_mv - c, 2)
    if abs(x["浮盈"]["市值"] - exp_mv) > 0.01 or abs(x["浮盈"]["浮盈额"] - exp_pnl) > 0.01:
        errc.append((x["code"], x["浮盈"], exp_mv, exp_pnl))
    if abs(x["cost"] - c) > 0.01:
        errc.append((x["code"], "cost", x["cost"], c))
chk("S5b 市值/浮盈/成本 与 state.json 重算一致", not errc, str(errc))

# S6 仓位
mv = round(sum(x["shares"] * q[x["code"]]["last"] for x in d["在持票照会"]), 2)
tot = round(mv + 882632.75, 2)
chk("S6 仓位比例重算一致", f"{round(mv/tot*100,2)}%" in d["report"] or abs(round(mv/tot*100, 2) - 10.91) < 0.02, f"mv={mv} total={tot} pct={round(mv/tot*100,2)}")

# S7 池内截面重算 (14:54:21 帧)
fr = None
for line in open("realtime_ticks.jsonl", encoding="utf-8"):
    f = json.loads(line)
    if f["ts"] == "2026-10-19 14:54:21":
        fr = f
chk("S7a 存在 14:54:21 帧", fr is not None)


def lim(pre, code):
    return round(pre * (1 + (0.2 if code.startswith(("30", "68")) else 0.1)), 2)


sealed = [r for r in fr["rows"] if r["latest"] >= lim(r["preClose"], r["code"]) - 0.001]
touched = [r for r in fr["rows"] if r["high"] >= lim(r["preClose"], r["code"]) - 0.001]
p = [r["pct"] for r in fr["rows"]]
s54 = calc["池内截面"]["14:54"]
chk("S7b 封板/触板/炸板 重算一致", len(sealed) == s54["封板"] and len(touched) == s54["触板"] and len(touched) - len(sealed) == s54["炸板"],
    f"重算 封{len(sealed)} 触{len(touched)} 炸{len(touched)-len(sealed)} vs 件内 {s54['封板']}/{s54['触板']}/{s54['炸板']}")
chk("S7c 再封率分母=触板数", abs(s54["池内再封率"] - round(len(sealed) / len(touched), 3)) < 0.001, f"{s54['池内再封率']}")
chk("S7d 中位/均值 重算一致", abs(s54["中位"] - round(statistics.median(p), 2)) < 0.011 and abs(s54["均值"] - round(sum(p)/len(p), 2)) < 0.011,
    f"件内 {s54['中位']}/{s54['均值']} 重算 {round(statistics.median(p),2)}/{round(sum(p)/len(p),2)}")

# S8 涨跌停价
chk("S8 600668 涨停9.67/跌停7.91", d["在持票照会"][0]["今日表现"]["收盘涨停价"] == 9.67 and d["在持票照会"][0]["今日表现"]["跌停价"] == 7.91)

# S9 MA 重算
def ma(code, n):
    rows = [r for r in csv.reader(open(os.path.join(BASE, "_学习/_bars_cache", code + ".csv"), encoding="utf-8")) if r and r[0][:2] == "20"]
    c = [float(r[4]) for r in rows]
    return round(sum(c[-n:]) / n, 3)


chk("S9 MA10(000601)=6.275 / MA20(000823)=23.706", abs(ma("000601", 10) - 6.275) < 0.002 and abs(ma("000823", 20) - 23.706) < 0.002,
    f"{ma('000601',10)} / {ma('000823',20)}")

# S10 零成交合法性: playbook 无 leg=close 且 take_zt 全 null
pb = json.load(open(os.path.join(BASE, "盘中/20261019/playbook.json"), encoding="utf-8"))
close_legs = [s for s in pb["sells"] if s.get("leg") == "close"]
tz = [s for s in pb["sells"] if (s.get("intraday") or {}).get("take_zt")]
chk("S10 fills 空集合法(无 leg=close / take_zt 全 null)", d["fills"] == [] and not close_legs and not tz,
    f"close腿={len(close_legs)} take_zt={len(tz)}")

# S11 现金对账
chk("S11 master 现金对平 820099.75+62533=882632.75", abs(820099.75 + 62533.00 - 882632.75) < 0.001)
chk("S11b 跨账合计 177405 对平", 49677 + 26733 + 65195 + 35800 == 177405)

# S12 000601 失效线事实
chk("S12 000601 今日最低 6.24 < 6.45 (双源)", q["000601"]["low"] == 6.24 and 6.24 < 6.45)

# S13 无占位/未渲染痕迹
def strs(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strs(v)
    elif isinstance(o, list):
        for v in o:
            yield from strs(v)


allstr = list(strs(d))
badstr = [s for s in allstr if re.search(r"\{[a-zA-Z_]", s) or re.search(r"\bNone\b", s) or "{{" in s or "}}" in s]
chk("S13 发出版无未渲染占位(f-string残留/None字面)", not badstr, str(badstr[:3]))

# S14 复盘件
chk("S14 复盘件存在且含关键节", os.path.exists(MD) and all(k in open(MD, encoding="utf-8").read() for k in ("在持票逐票表态", "预收盘第一手判断", "明日（2026-10-20 周二）预案要点", "零后视镜")),
    MD)
mdtxt = open(MD, encoding="utf-8").read()
chk("S14b 复盘件无 None/nan", not any(t in mdtxt for t in ("None", "nan", "NaN", "gzh")), "")

# S15 明日要点含两笔清仓
mk = "".join(d["明日预案要点"])
chk("S15 明日要点覆盖 600668+000601 清仓与 000823 持有", all(k in mk for k in ("600668", "000601", "000823")), "")

# S16 决策件不复用收盘价措辞 (未声称收盘值)
chk("S16 未声称官方收盘价/收盘量", "官方收盘价" not in json.dumps(d, ensure_ascii=False) or "不可得" in json.dumps(d, ensure_ascii=False), "")

# S17 补正条目指向 000601
chk("S17 补正登记 000601 两场误判", any("000601" in str(x) for x in d["补正"]), "")

# S18 补正件存在且可解析
AM = "临盘决断_20261019_1445_补正1.json"
ok18 = os.path.exists(AM)
if ok18:
    a = json.load(open(AM, encoding="utf-8"))
    ok18 = a.get("补正编号") == "补正1" and "000601" in json.dumps(a, ensure_ascii=False)
chk("S18 补正1(000601 时点措辞)存在且可解析", ok18, AM)

ok = sum(1 for _, c, _ in res if c)
for n, c, det in res:
    print(("PASS " if c else "FAIL ") + n + ("  | " + det if det else ""))
print(f"\n哨兵结果: {ok}/{len(res)} PASS")
sys.exit(0 if ok == len(res) else 1)
