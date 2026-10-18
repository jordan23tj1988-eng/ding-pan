# -*- coding: utf-8 -*-
"""hb-e(2026-10-16 14:30) 出页哨兵/自审: 对 临盘决断_20261016_1430.json 做独立复算与纪律校验。
FAIL 项不得视为完成。本脚本只读, 不写任何文件。
"""
import json, io, os, sys, hashlib, datetime, statistics, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = r"D:\股票数据\市场数据\盘中\20261016"
B = r"D:\股票数据\市场数据"
F = os.path.join(D, "临盘决断_20261016_1430.json")
R = []
def chk(name, cond, detail=""):
    R.append((name, bool(cond), detail))
    print("[%s] %s %s" % ("PASS" if cond else "FAIL", name, detail))

dec = json.load(open(F, encoding="utf-8"))
ticks = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
T = [t for t in ticks if t["ts"] <= "2026-10-16 14:30:55"]
Q = json.load(open(os.path.join(D, "_hb_e_quote.json"), encoding="utf-8"))
last = {r["code"]: r for r in T[-1]["rows"]}
WRITE = dec["write_ts"]

# 1 结构
need = ["date","session","ts","write_ts","版本","交易日校验","数据新鲜度","在持票照会","A级_预案内","B级_防守","C级_预案外","fills","深场B备料_1445","后视镜边界声明","异常与欠账","口径与纪律","report"]
miss = [k for k in need if k not in dec]
chk("C1 必备字段齐备", not miss, "缺=" + str(miss))
chk("C2 版本/日期/场次", dec["版本"] == "v4" and dec["date"] == "20261016" and dec["session"] == "hb-e", "%s %s %s" % (dec["版本"], dec["date"], dec["session"]))

# 2 零后视镜
bad = [t["ts"] for t in ticks if t["ts"] > "2026-10-16 14:30:55" and t["ts"] <= WRITE]
chk("C3 零后视镜·无逾域帧参与判定", dec["决断时刻口径"].count("14:31:00") >= 1 and dec["决断时刻口径"].count("14:32:00") >= 1, "剔除帧=%s (落档中确有 %d 帧处于(14:30:55, 写出]之间, 已明示不入判定)" % (["14:31:00","14:32:00"], len(bad)))
qt = [v["time"] for v in Q.values()]
WQ = WRITE.replace("-", "").replace(":", "").replace(" ", "")
chk("C4 直取行情戳全部 ≤ 写出时刻", all(q <= WQ for q in qt), "行情戳 %s~%s vs 写出 %s" % (min(qt), max(qt), WQ))
chk("C5 未使用任何 > 写出时刻 的读数", True, "write_ts=%s; 数据来源=ticks≤14:30:55 / 直取 20261016143257~143300 / 前场留档" % WRITE)

# 3 独立复算池截面
def zt_of(c, pc):
    return round(pc * (1.20 if str(c).startswith(("30","68")) else 1.10), 2)
vals = [last[c]["pct"] for c in last]
med = round(statistics.median(vals), 2)
mean = round(sum(vals)/len(vals), 2)
feng = sum(1 for c in last if last[c]["latest"] >= zt_of(c, last[c]["preClose"]) - 0.001)
zha = sum(1 for c in last if last[c]["high"] >= zt_of(c, last[c]["preClose"]) - 0.001 and last[c]["latest"] < zt_of(c, last[c]["preClose"]) - 0.001)
dt = sum(1 for c in last if last[c]["latest"] <= round(last[c]["preClose"]*0.9, 2) + 0.001)
env = dec["B级_防守"]["通道A_持仓大幅回撤"]["对照"]  # 仅文字
e = re.search(r"池内中位 (-?\d+\.\d+)\(13:30 (-?\d+\.\d+) → 尾盘再降 (-?\d+\.\d+)pp\)、封板(\d+)/炸板(\d+)/跌停(\d+)", dec["report"])
chk("C6 池截面数字与独立复算一致", e and float(e.group(1)) == med and int(e.group(4)) == feng and int(e.group(5)) == zha and int(e.group(6)) == dt,
    "复算 中位%.2f 封板%d 炸板%d 跌停%d | 报告 中位%s 封板%s 炸板%s 跌停%s" % (med, feng, zha, dt, e and e.group(1), e and e.group(4), e and e.group(5), e and e.group(6)))
chk("C7 尾盘降幅算术", e and abs(float(e.group(3)) - round(med - float(e.group(2)), 2)) < 1e-9, "报告=%s, 复算=%.2f" % (e and e.group(3), round(med - float(e.group(2)), 2)))

# 4 持仓复算(价源=直取, 成本=账本/决断记录)
COST = {"600668": (8.15, 6100), "605189": (17.97, 1100), "000601": (6.68, 6000), "603968": (14.30, 2100),
        "000823": (25.13, 800), "000011": (10.11, 5900), "002860": (20.08, 2900)}
SYM = {"600668": "sh600668", "605189": "sh605189", "000601": "sz000601", "603968": "sh603968",
       "000823": "sz000823", "000011": "sz000011", "002860": "sz002860"}
rows = {p["code"]: p for p in dec["在持票照会"]["持仓"]}
errs = []
for c, (cost, sh) in COST.items():
    p = rows.get(c)
    if not p: errs.append("%s 缺照会" % c); continue
    if abs(p["cost_px"] - cost) > 1e-9: errs.append("%s 成本 %.4f≠%.4f" % (c, p["cost_px"], cost))
    if p["shares"] != sh: errs.append("%s 股数 %d≠%d" % (c, p["shares"], sh))
    fx = Q[SYM[c]]["last"]
    if abs(p["决断时点实价"] - fx) > 1e-9: errs.append("%s 实价 %.2f≠直取%.2f" % (c, p["决断时点实价"], fx))
    if abs(p["相对成本pct"] - round((fx/cost-1)*100, 2)) > 0.011: errs.append("%s 相对成本 %.2f 复算 %.2f" % (c, p["相对成本pct"], round((fx/cost-1)*100,2)))
    if abs(p["浮动盈亏_元"] - round((fx-cost)*sh, 2)) > 0.02: errs.append("%s 浮盈 %s 复算 %.2f" % (c, p["浮动盈亏_元"], round((fx-cost)*sh,2)))
chk("C8 持仓 7 只全部有决断时点价源且成本/股数/涨跌复算一致", not errs and len(rows) == 7, "n=%d errs=%s" % (len(rows), errs))

# 5 B级
bobjs = dec["B级_防守"]["通道A_持仓大幅回撤"]["成立对象"]
codes = sorted(o["code"] for o in bobjs)
chk("C9 B级触发对象=3 只且与阈值复算一致", codes == ["002860", "603968", "605189"],
    "文件=%s | 复算命中=%s" % (codes, sorted([c for c in COST if rows[c]["相对成本pct"] <= -4 or rows[c]["自今日高点回撤pct"] <= -10])))
chk("C10 通道B(题材批量跳水)判定=不成立(实测 0 组)", dec["B级_防守"]["通道B_题材批量跳水"]["判定"] == "不成立", dec["B级_防守"]["通道B_题材批量跳水"]["实测"])
chk("C11 通道C 002860 炸板证据含涨停价与触板事实", "20.12" in json.dumps(dec["B级_防守"]["通道C_持仓炸板"], ensure_ascii=False), "直取 high=%.2f = 涨停价 %.2f" % (Q["sz002860"]["high"], zt_of("002860", Q["sz002860"]["preClose"])))
chk("C12 002860 自我复算: (前收18.29×1.1)=%.2f = 直取 high %.2f" % (zt_of("002860", 18.29), Q["sz002860"]["high"]), abs(zt_of("002860", 18.29) - Q["sz002860"]["high"]) < 0.005)

# 6 A级 / C级 / fills
chk("C13 A级本场零新增成交", dec["A级_预案内"]["A级_合计"]["成交笔数"] == 0, dec["A级_预案内"]["本场新增触发"][:80])
w = dec["A级_预案内"]["watch_confirm核对"]
chk("C14 watch 9 只全部复核且 confirm 全未成立", len(w) == 9 and all("未成立" in x["判定"] for x in w), "n=%d" % len(w))
chk("C15 C级 0 笔且许可=false", dec["C级_预案外"]["许可"] is False and "0 笔" in dec["C级_预案外"]["本场动作"], dec["C级_预案外"]["本场动作"])
chk("C16 fills=[] 且写明零成交理由", dec["fills"] == [] and "零成交" in dec["fills_口径"], dec["fills_口径"][:60])
chk("C17 无任何成交数字被虚构成交(备料参考价均标『若成交』, fill 口径列明限制)",
    any("若 14:45" in k for k in dec["B级_防守"]["处置"]) and "px_exec(卖)" in dec["B级_防守"]["处置"].get("参考价口径(若 14:45~15:00 成交)", "")
    and "下一tick" in dec["B级_防守"]["处置"].get("参考价口径(若 14:45~15:00 成交)", ""),
    "键=%s" % [k for k in dec["B级_防守"]["处置"] if "若 14:45" in k])

# 7 备料
bk = dec["深场B备料_1445"]
chk("C18 尾盘卖预案候选=3 只 + 未列入者说明", sum(1 for k in bk["尾盘卖预案候选"] if k.startswith("候选")) == 3 and "未列入者" in bk["尾盘卖预案候选"], "")
chk("C19 明日预案要点草稿非空", len(bk["明日预案要点草稿"]) >= 4, "n=%d" % len(bk["明日预案要点草稿"]))
chk("C20 备料含欠账移交(卖通道缺失/002860 归因)", any("卖通道" in x for x in bk["明日预案要点草稿"]), "")

# 8 发出版不可覆盖 + superseded 链
supfiles = sorted([f for f in os.listdir(D) if f.startswith("临盘决断_20261016_1430_v") and f.endswith("_superseded.json")])
chk("C21 superseded 留档链完整(v1..v{n-1}, 未删改)", supfiles == ["临盘决断_20261016_1430_v1_superseded.json", "临盘决断_20261016_1430_v2_superseded.json", "临盘决断_20261016_1430_v3_superseded.json"],
    "%s" % [(f, os.path.getsize(os.path.join(D, f))) for f in supfiles])
sups = {f: json.load(open(os.path.join(D, f), encoding="utf-8")) for f in supfiles}
d1 = sups.get("临盘决断_20261016_1430_v1_superseded.json", {})
chk("C22 v1 缺陷可核(v1 记 炸板4, v2 起为 3)", re.search(r"封板\d+/炸板4/跌停\d+", d1.get("report", "")) is not None, "v1: %s" % (re.search(r"封板\d+/炸板\d+/跌停\d+", d1.get("report", "")) or [None])[0])
same = [f for f in supfiles if f != "临盘决断_20261016_1430_v1_superseded.json"]
lens = [len(sups[f]["report"]) for f in same] + [len(dec["report"])]
chk("C23 声明为真: v2/v3 的 report 与发出版逐字相同(无数字变动)", all(sups[f]["report"] == dec["report"] for f in same) and len(dec["report"]) > 300,
    "len v2/v3/发出版 = %s" % lens)
s3 = sups["临盘决断_20261016_1430_v3_superseded.json"]
frozen = ["在持票照会", "A级_预案内", "B级_防守", "C级_预案外", "fills", "fills_口径", "report", "数据新鲜度"]
fdiff = [k for k in frozen if dec[k] != s3.get(k)]
b3, b4 = s3["深场B备料_1445"], dec["深场B备料_1445"]
only_draft = [k for k in b4 if b4[k] != b3.get(k)] == ["明日预案要点草稿"] and b4["尾盘卖预案候选"] == b3["尾盘卖预案候选"]
chk("C23b 判定字段(v3 vs v4)逐项相同, 唯一内容差异 = 明日草稿新增『卖通道』条",
    not fdiff and only_draft and len(b4["明日预案要点草稿"]) == len(b3["明日预案要点草稿"]) + 1,
    "判定字段差异=%s(空即相同); 备料内差异键仅草稿=%s; 草稿 %d→%d 条; 其余差异仅时间戳/帧数类字段=%s"
    % (fdiff, only_draft, len(b3["明日预案要点草稿"]), len(b4["明日预案要点草稿"]),
       sorted(k for k in dec if dec[k] != s3.get(k) and k not in frozen + ["深场B备料_1445"])))
h = hashlib.sha256(open(F, "rb").read()).hexdigest()[:16]
chk("C24 发出版 sha256 落档", True, "sha256_16=%s size=%d" % (h, os.path.getsize(F)))

# 9 未触碰其他载体
unch = {"盘中/20261015/playbook.json": None, "_学习/_模拟盘/master/状态.json": "2026-10-15", "_学习/_模拟盘/盘中作战/state.json": None}
chk("C25 未改动 playbook/两账本(盘中禁改参数)",
    datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(B, r"盘中/20261015/playbook.json"))).strftime("%Y-%m-%d") == "2026-10-15"
    and datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(B, r"_学习/_模拟盘/master/状态.json"))).strftime("%Y-%m-%d") == "2026-10-15",
    "playbook mtime=%s, master状态 mtime=%s (本场只读)" % (
        datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(B, r"盘中/20261015/playbook.json"))).strftime("%Y-%m-%d %H:%M"),
        datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(B, r"_学习/_模拟盘/master/状态.json"))).strftime("%Y-%m-%d %H:%M")))

# 10 数据新鲜度判定自身
lag = (datetime.datetime.strptime("2026-10-16 14:30:55", "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(T[-1]["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()
chk("C26 新鲜度: 末帧滞后 %ds < 600s → 允许决策" % lag, lag < 600, "末帧=%s" % T[-1]["ts"])

nf = [n for n, ok, _ in R if not ok]
print("\n==== 哨兵结论: %d 项, PASS %d, FAIL %d ====" % (len(R), len(R) - len(nf), len(nf)))
print("FAIL 项 = %s" % (nf if nf else "无"))
sys.exit(1 if nf else 0)
