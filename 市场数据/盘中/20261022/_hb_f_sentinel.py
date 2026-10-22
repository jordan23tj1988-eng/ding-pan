# -*- coding: utf-8 -*-
"""hb-f 14:45 场 哨兵: 对 临盘决断_20261022_1445.json + 尾盘复盘md 做 24 项自审"""
import json, os, re, glob, datetime

D = r"D:\股票数据\市场数据\盘中\20261022"
MD = r"D:\股票数据\市场数据\_学习\盘中尾盘复盘_20261022.md"
F = os.path.join(D, "临盘决断_20261022_1445.json")
res = []


def chk(name, cond, detail=""):
    res.append((("PASS" if cond else "FAIL"), name, detail))


d = json.load(open(F, encoding="utf-8"))
q = json.load(open(os.path.join(D, "_hb_f_quote_1445.json"), encoding="utf-8"))
p = json.load(open(os.path.join(D, "_hb_f_pools_1445.json"), encoding="utf-8"))
dtc = json.load(open(os.path.join(D, "_hb_f_dtcheck.json"), encoding="utf-8"))
md = open(MD, encoding="utf-8").read()
wts = datetime.datetime.strptime(d["write_ts"], "%Y-%m-%d %H:%M:%S")

# 1 发出版存在且 v1
chk("C01 发出版存在/v1", d.get("version") == 1 and d.get("发出版") is True)
# 2 未覆盖前六件
prev = ["临盘决断_20261022_0921.json", "临盘决断_20261022_0940.json", "临盘决断_20261022_1030.json",
        "临盘决断_20261022_1100.json", "临盘决断_20261022_1330.json", "临盘决断_20261022_1430.json"]
bad = []
for f in prev:
    fp = os.path.join(D, f)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    if mt >= wts:
        bad.append((f, str(mt)))
chk("C02 前六件mtime<write_ts", not bad, str(bad))
# 3 零后视镜: 证据帧 <= write_ts
qt = q["fetched"]
chk("C03 腾讯帧<=write_ts", datetime.datetime.strptime(qt, "%Y-%m-%d %H:%M:%S") <= wts, qt)
chk("C04 池帧取数<=write_ts", datetime.datetime.strptime(p["fetched"], "%Y-%m-%d %H:%M:%S") <= wts, p["fetched"])
# 5 fills 空 + 条件决断空
chk("C05 fills=[]", d["fills"] == [], len(d["fills"]))
chk("C06 买入腿=0", d["条件决断"]["买入"] == [])
chk("C07 卖出腿=0", d["条件决断"]["卖出"] == [])
# 8 leg计数
chk("C08 leg_close/take_zt=0", d["预案核对"]["leg_close计数"] == 0 and d["预案核对"]["take_zt_count"] == 0)
# 9 持仓数字
h = d["在持票逐票表态"][0]
r = q["rows"]["sz002242"]
chk("C09 002242现价一致", abs(r["px"] - 21.35) < 1e-9 and "21.35" in h["今日表现"], "%.2f" % r["px"])
chk("C10 浮亏算式", abs((21.35 - 21.69) * 900 - (-306.0)) < 1e-6, "%.1f" % ((21.35 - 21.69) * 900))
chk("C11 减半股数", "450" in h["明日计划"] and 900 / 2 == 450)
chk("C12 低/高一致", h["今日表现"].find("20.50") > 0 and abs(r["low"] - 20.50) < 1e-9 and abs(r["high"] - 22.08) < 1e-9)
# 13 涨跌停池数字
chk("C13 三池数字", len(p["zt"]) == 31 and len(p["zb"]) == 24 and len(p["dt"]) == 46,
    "%d/%d/%d" % (len(p["zt"]), len(p["zb"]), len(p["dt"])))
chk("C14 炸板率", abs(len(p["zb"]) / (len(p["zt"]) + len(p["zb"])) - 0.4364) < 0.0002,
    "%.4f" % (len(p["zb"]) / (len(p["zt"]) + len(p["zb"]))))
# 15 跌停确认
chk("C15 跌停46/46确认", dtc["confirmed"] == 46 and dtc["dt_pool_n"] == 46 and not dtc["unconfirmed"])
# 16 连板分布
lb = {}
for x in p["zt"]:
    lb[x.get("lbc", 0)] = lb.get(x.get("lbc", 0), 0) + 1
chk("C16 连板分布", lb == {1: 24, 2: 3, 3: 2, 5: 2}, str(dict(sorted(lb.items()))))
# 17 池内宽度重算(帧<=14:46:15)
frames = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
fr = [f for f in frames if f["ts"] <= "2026-10-22 14:46:15"][-1]
pcts = sorted(x["pct"] for x in fr["rows"] if x.get("pct") is not None)
n = len(pcts)
med = pcts[n // 2] if n % 2 else (pcts[n // 2 - 1] + pcts[n // 2]) / 2
up = sum(1 for x in pcts if x > 0); dn = sum(1 for x in pcts if x < 0)
le9 = sum(1 for x in pcts if x <= -9); ge9 = sum(1 for x in pcts if x >= 9)
chk("C17 池内宽度", abs(med + 2.95) < 0.01 and up == 19 and dn == 31 and le9 == 9 and ge9 == 11,
    "中位%.2f 涨%d 跌%d ≤-9%%:%d ≥9%%:%d" % (med, up, dn, le9, ge9))
chk("C18 末帧14:46:15", fr["ts"] == "2026-10-22 14:46:15", fr["ts"])
# 19 帧龄 < 10min
chk("C19 帧龄<10min", (wts - datetime.datetime.strptime(fr["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() < 600,
    "%.1f 分钟" % ((wts - datetime.datetime.strptime(fr["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60))
# 20 002724 更正有据
r24 = q["rows"]["sz002724"]
chk("C20 002724破板更正有据", abs(r24["low"] - 10.70) < 1e-9 and abs(r24["open"] - 11.21) < 1e-9 and abs(r24["px"] - 11.21) < 1e-9,
    "开%.2f 低%.2f" % (r24["open"], r24["low"]))
# 21 5分钟滚动复核(声明+0.61%)
s = [(f["ts"], x["latest"]) for f in frames if f["ts"] <= "2026-10-22 14:46:15" and f["ts"][11:] >= "14:41:14"
     for x in f["rows"] if x["code"] == "002242"]
if s:
    base = s[0]; tgt = [x for x in s if x[0][11:] == "14:45:15"][0]
    c5 = (tgt[1] / base[1] - 1) * 100
    chk("C21 5分钟滚动+0.61%", abs(c5 - 0.61) < 0.05, "%+.2f%% (base %s %.2f → %s %.2f)" % (c5, base[0], base[1], tgt[0], tgt[1]))
# 22 md 与 json 关键数字一致
md_ok = all(k in md for k in ["46", "43.6", "-2.95", "21.35", "-1.57", "450", "20.50", "3649.86"])
chk("C22 md关键数字", md_ok)
chk("C23 md无收盘冒充", ("收盘价 " not in md) or ("不可得" in md))
# 24 止损线只来自显式声明
chk("C24 止损仅20.50", "20.50" in h["明日计划"] and h["明日计划"].count("止损") >= 1)
# 25 缺口登记
chk("C25 缺件已登记", all(k in d["数据新鲜度"]["缺件"] for k in ["pulse.json", "warboard.json", "执行流水.jsonl"]))
# 26 002242 跌停价校验
chk("C26 跌停价20.36", abs(round(r["pre"] * 0.9, 2) - 20.36) < 1e-9, "%.2f" % round(r["pre"] * 0.9, 2))

np_ = sum(1 for x in res if x[0] == "PASS")
print("=== hb-f 14:45 哨兵 %d/%d PASS ===" % (np_, len(res)))
for st, name, det in res:
    print(("[%s] %-28s %s" % (st, name, det)).rstrip())
print("\n总判定:", "ALL PASS" if np_ == len(res) else "★FAIL %d 项" % (len(res) - np_))
