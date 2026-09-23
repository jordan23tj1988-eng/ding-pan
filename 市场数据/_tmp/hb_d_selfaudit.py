# -*- coding: utf-8 -*-
"""hb-d 自审: 回读决断文件 + 关键数字逐一回溯到原始留档(零编造核对) + 未覆盖核对。"""
import json, os, datetime as dt, hashlib

ROOT = r"D:\股票数据\市场数据"
TODAY = "20260921"
D = os.path.join(ROOT, "盘中", TODAY)
DEC = os.path.join(D, "临盘决断_%s_1330.json" % TODAY)

d = json.load(open(DEC, encoding="utf-8"))
ok = []
def chk(name, cond, extra=""):
    ok.append((name, bool(cond), extra))

chk("文件可解析且为 dict", isinstance(d, dict))
chk("session=hb-d / ts=13:30", d["session"] == "hb-d" and d["ts"] == "13:30")
chk("level=ALARM_ONLY", d["level"] == "ALARM_ONLY")
chk("fills=[] 且 fills 内无 px_exec/qty 字段(仅声明文字提及)", d["fills"] == [] and not any(
    isinstance(f, dict) and ("px_exec" in f or "qty" in f) for f in d["fills"]))
chk("条件决断=[]", d["条件决断"] == [])

# 回溯 tick
rows = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
pre = [r for r in rows if dt.datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S") <= dt.datetime(2026, 9, 21, 13, 30)]
last = {x["code"]: x for x in pre[-1]["rows"]}
pcts = [v["pct"] for v in last.values()]
chk("tick 条数(<=13:30)=%d" % len(pre), len(pre) == d["data_freshness"]["realtime_channel"]["n_at_or_before_1330"])
chk("首/末 tick ts 一致", pre[0]["ts"] == d["data_freshness"]["realtime_channel"]["first_ts"] and pre[-1]["ts"] == d["data_freshness"]["realtime_channel"]["last_at_or_before_1330"])
gap = (dt.datetime(2026, 9, 21, 13, 30) - dt.datetime.strptime(pre[-1]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()
chk("断更 %.1fs = 文件中 %.2fmin" % (gap, gap / 60), abs(gap / 60 - d["data_freshness"]["realtime_channel"]["gap_min_at_decision"]) < 0.01)
mean = sum(pcts) / len(pcts)
chk("池内均值 %+.2f%% 出现在实况串" % mean, ("%+.2f%%" % mean) in d["池内实况_决断时点前最后留档"]["涨跌"])
chk("涨停数 1 且为 002585", [v["code"] for v in last.values() if v["pct"] >= 9.8] == ["002585"])
zt = [v for v in last.values() if v["code"] == "002585"][0]
chk("双星新材 pct=%.2f" % zt["pct"], ("%.2f" % zt["pct"]) in json.dumps(d["池内实况_决断时点前最后留档"]["涨停"], ensure_ascii=False))

# 回撤项
fh = last["000636"]
dd = round((fh["latest"] - fh["high"]) / fh["high"] * 100, 2)
chk("风华高科回撤 %.2f%% 在文件中" % dd, str(dd) in json.dumps(d["池内实况_决断时点前最后留档"]["风险扫描"], ensure_ascii=False))

# 账本
s1 = json.load(open(os.path.join(ROOT, "_学习", "_模拟盘", "盘中作战", "state.json"), encoding="utf-8"))
s2 = json.load(open(os.path.join(ROOT, "_学习", "_模拟盘", "master", "state.json"), encoding="utf-8"))
chk("盘中作战 cash=%s positions=%s" % (s1["cash"], s1["positions"]), s1["cash"] == 1000000.0 and s1["positions"] == [])
chk("master cash=%s positions=%s" % (s2["cash"], s2["positions"]), s2["cash"] == 1009012.5 and s2["positions"] == [])
chk("账本数字与文件一致", "1000000.0" in d["对账"]["账本"] and "1009012.5" in d["对账"]["账本"])

# 总审
zs = json.load(open(os.path.join(ROOT, "_学习", "总审_20260911.json"), encoding="utf-8"))
chk("总审档位=%s 置信=%s" % (zs["总裁决"]["档位"], zs["总裁决"]["置信度"]), zs["总裁决"]["档位"] == "C" and zs["总裁决"]["置信度"] == 0.82)
chk("总审 C/0.82 出现在文件", "档位 C/置信 0.82" in d["三级判定"]["C级_预案外进攻"]["依据"])

# 文件不存在项
chk("pulse.json 全盘 0 命中", not any("pulse.json" in f for _, _, fs in os.walk(ROOT) for f in fs))
chk("执行流水.jsonl 全盘 0 命中", not any("执行流水.jsonl" in f for _, _, fs in os.walk(ROOT) for f in fs))
chk("今日 warboard.json 不存在", not os.path.exists(os.path.join(D, "warboard.json")))

# 未覆盖核对: 既有 4 文件 mtime 应仍为 11:5x/12:0x
for f, exp in [("临盘决断_20260921_0921.json", "11:54"), ("临盘决断_20260921_1030.json", "12:02"),
               ("临盘决断_20260921_1100.json", "12:04"), ("临盘决断_20260921_0940.json", "12:04")]:
    mt = dt.datetime.fromtimestamp(os.path.getmtime(os.path.join(D, f))).strftime("%H:%M")
    chk("既有发出版未被动: %s mtime=%s" % (f, mt), mt == exp)

# 报警 jsonl
al = [json.loads(l) for l in open(os.path.join(D, "报警_%s.jsonl" % TODAY), encoding="utf-8") if l.strip()]
chk("报警行数=4 且末行=hb-d_1330", len(al) == 4 and al[-1]["session"] == "hb-d_1330")
chk("报警末行 decision_file 指向本文件", al[-1]["decision_file"].endswith("临盘决断_%s_1330.json" % TODAY))
chk("报警末行 fills=[]", al[-1]["fills"] == [])

print("=== 自审结果 ===")
bad = 0
for n, c, e in ok:
    print(("  [PASS] " if c else "  [FAIL] ") + n + ("" if c else "  " + str(e)))
    bad += (not c)
print("\n总项=%d FAIL=%d" % (len(ok), bad))
print("决断文件 sha256_16 =", hashlib.sha256(open(DEC, "rb").read()).hexdigest()[:16])
print("结论:", "SELF-AUDIT PASS" if bad == 0 else "SELF-AUDIT FAIL")
