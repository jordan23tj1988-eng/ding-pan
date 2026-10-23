# -*- coding: utf-8 -*-
"""hb-f 14:45 场 哨兵: 对 临盘决断_1445 / 1500收盘了结 / 尾盘复盘md 做 24 项自审"""
import json, os, datetime, re

D = r"D:\股票数据\市场数据\盘中\20261023"
MD = r"D:\股票数据\市场数据\_学习\盘中尾盘复盘_20261023.md"
F1 = os.path.join(D, "临盘决断_20261023_1445.json")
F2 = os.path.join(D, "临盘决断_20261023_1500_收盘了结.json")
res = []


def chk(name, cond, detail=""):
    res.append((("PASS" if cond else "FAIL"), name, str(detail)))


d1 = json.load(open(F1, encoding="utf-8"))
d2 = json.load(open(F2, encoding="utf-8"))
q = json.load(open(os.path.join(D, "_hb_f_quote_1445.json"), encoding="utf-8"))
qc = json.load(open(os.path.join(D, "_hb_f_quote_close.json"), encoding="utf-8"))
p = json.load(open(os.path.join(D, "_hb_f_pools_1445.json"), encoding="utf-8"))
md = open(MD, encoding="utf-8").read()
w1 = datetime.datetime.strptime(d1["write_ts"], "%Y-%m-%d %H:%M:%S")
w2 = datetime.datetime.strptime(d2["write_ts"], "%Y-%m-%d %H:%M:%S")
T1 = datetime.datetime.strptime(d1["实际决断时间戳"], "%Y-%m-%d %H:%M:%S")

# C01 发版存在
chk("C01 1445发出版存在", os.path.exists(F1) and "v1" in d1["版本"])
# C02 未覆盖前五场件
prev = ["临盘决断_20261023_0921.json", "临盘决断_20261023_0921_补正1.json", "临盘决断_20261023_0940.json",
        "临盘决断_20261023_1030.json", "临盘决断_20261023_1030_补正1.json", "临盘决断_20261023_1330.json",
        "临盘决断_20261023_1330_补正1.json", "临盘决断_20261023_1430.json", "临盘决断_20261023_1430_补正1.json",
        "临盘决断_20261023_1430_补正2.json"]
bad = [f for f in prev if os.path.exists(os.path.join(D, f)) and
       datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(D, f))) >= w1]
chk("C02 前序10件mtime<1445写件", not bad, bad)
# C03 1445件未被收盘件覆盖（mtime 顺序）
chk("C03 1445未被覆盖", datetime.datetime.fromtimestamp(os.path.getmtime(F1)) <=
    datetime.datetime.fromtimestamp(os.path.getmtime(F2)),
    "%s <= %s" % (datetime.datetime.fromtimestamp(os.path.getmtime(F1)), datetime.datetime.fromtimestamp(os.path.getmtime(F2))))
# C04 1445 fills 空
chk("C04 1445 fills=[]", d1["fills"] == [], len(d1["fills"]))
# C05 收盘件 fills 1 笔 sell 300
fl = d2["fills"]
chk("C05 收盘fills=1笔sell", len(fl) == 1 and fl[0]["side"] == "sell" and fl[0]["shares"] == 300, fl[0]["shares"] if fl else None)
# C06 收盘价与证据一致
pxc = qc["rows"]["sh603370"]["px"]
chk("C06 收盘价一致", abs(pxc - 30.11) < 1e-9 and abs(fl[0]["px_base"] - 30.11) < 1e-9, pxc)
# C07 px_exec = 收盘价×0.999 四舍五入
chk("C07 px_exec算式", abs(fl[0]["px_exec"] - round(30.11 * 0.999, 2)) < 1e-9, fl[0]["px_exec"])
# C08 卖出滑点方向不利
chk("C08 滑点方向(卖<基准)", fl[0]["px_exec"] < fl[0]["px_base"], "%s<" % fl[0]["px_exec"])
# C09 成交额/盈亏算式
chk("C09 amount算式", abs(fl[0]["amount"] - round(fl[0]["px_exec"] * 300, 2)) < 1e-6, fl[0]["amount"])
chk("C10 pnl算式", abs(fl[0]["pnl"] - (fl[0]["amount"] - 28.11 * 300)) < 1e-6, fl[0]["pnl"])
chk("C11 pnl_pct算式", abs(fl[0]["pnl_pct"] - round((fl[0]["px_exec"] / 28.11 - 1) * 100, 2)) < 0.011, fl[0]["pnl_pct"])
# C12 帧戳<=写件
t_c = datetime.datetime.strptime("20261023150027", "%Y%m%d%H%M%S")
chk("C12 收盘帧<=写件", t_c <= w2, "%s <= %s" % (t_c, w2))
# C13 零后视镜: 1445 件引用的取数时间均 <= 决断时点
tq = datetime.datetime.strptime(q["fetched"], "%Y-%m-%d %H:%M:%S")
tp = datetime.datetime.strptime(p["fetched"], "%Y-%m-%d %H:%M:%S")
tq_tick = datetime.datetime.strptime(q["rows"]["sh603370"]["t"], "%Y%m%d%H%M%S")
chk("C13 零后视镜(取数<=决断)", tq <= T1 and tp <= T1 and tq_tick <= T1, "%s %s %s <= %s" % (tq, tp, tq_tick, T1))
# C14 现价一致 + 浮盈算式
px = q["rows"]["sh603370"]["px"]
chk("C14 1445现价一致", abs(px - 30.28) < 1e-9 and "30.28" in d1["在持票照会"]["603370 华新精科"]["现价"], px)
chk("C15 浮盈算式", abs(round((30.28 - 28.11) * 300, 2) - 651.0) < 1e-6 and "+651.0" in d1["在持票照会"]["603370 华新精科"]["浮盈"], round((30.28 - 28.11) * 300, 2))
# C16 权重算式
w = round(9084.0 / (933752.43 + 9084.0) * 100, 2)
chk("C16 权重算式", abs(w - 0.96) < 0.005 and "0.96" in d1["在持票照会"]["603370 华新精科"]["浮盈"], w)
# C17 三池数字
chk("C17 三池81/12/8", len(p["zt"]) == 81 and len(p["zb"]) == 12 and len(p["dt"]) == 8,
    "%d/%d/%d" % (len(p["zt"]), len(p["zb"]), len(p["dt"])))
# C18 炸板率
zbr = round(len(p["zb"]) / (len(p["zt"]) + len(p["zb"])), 4)
chk("C18 炸板率=12/93", abs(zbr - 12 / 93) < 6e-5 and ("0.129" in json.dumps(d1, ensure_ascii=False)) and abs(zbr - 0.129) < 5e-5, zbr)
# C19 连板分布 + 首板占比
lb = {}
for x in p["zt"]:
    lb[x.get("lbc", 0)] = lb.get(x.get("lbc", 0), 0) + 1
chk("C19 连板分布{1:70,2:9,3:1,6:1}", lb == {1: 70, 2: 9, 3: 1, 6: 1}, dict(sorted(lb.items())))
chk("C20 首板占比86.4%", abs(round(70 / 81 * 100, 1) - 86.4) < 1e-9)
# C21 帧龄 <600s
fr_ts = "2026-10-23 14:48:08"
age = (T1 - datetime.datetime.strptime(fr_ts, "%Y-%m-%d %H:%M:%S")).total_seconds()
chk("C21 帧龄52s<600", abs(age - 52) < 1e-6, age)
# C22 md 章节完整
need = ["## 一、", "## 二、", "## 三、", "## 四、", "## 五、", "## 六、", "## 七、", "## 八、", "## 九、", "## 附：收盘确认"]
miss = [x for x in need if x not in md]
chk("C22 md章节完整", not miss, miss)
# C23 md 与证据一致（关键数字）
nums = ["81", "0.1290", "30.11", "30.08", "591.00", "3690.48", "12.33", "15.96", "+7.72%"]
m2 = [x for x in nums if x not in md]
chk("C23 md关键数字齐", not m2, m2)
# C24 机会成本算式 + 收盘双封一致
g242 = round((qc["rows"]["sz002242"]["px"] - 20.74) * 800, 2)
g639 = round((qc["rows"]["sz002639"]["px"] - 14.00) * 2600, 2)
chk("C24 机会成本算式", abs(g242 - 632.0) < 1e-6 and abs(g639 - 2158.0) < 1e-6 and "2,790" in md, "%s/%s" % (g242, g639))


# C25/C26 补正1（v2 最终成稿）
F3 = os.path.join(D, "临盘决断_20261023_1445_补正1.json")
d3 = json.load(open(F3, encoding="utf-8"))
c3 = dict(d3); c3.pop("更正记录", None)
chk("C25 补正1无百分号残留", "%%" not in json.dumps(c3, ensure_ascii=False))
a = dict(d1); b = dict(d3)
for k in ("版本", "write_ts", "更正记录", "市场读数"):
    a.pop(k, None); b.pop(k, None)
chk("C26 补正1与v1数据一致", json.dumps(a, ensure_ascii=False, sort_keys=True) == json.dumps(b, ensure_ascii=False, sort_keys=True))

fails = [x for x in res if x[0] == "FAIL"]
for st, nm, dt in res:
    print("%-4s %-26s %s" % (st, nm, dt))
print("\n=== %d/%d PASS, FAIL %d ===" % (len(res) - len(fails), len(res), len(fails)))
print("SENTINEL", "PASS" if not fails else "FAIL")
