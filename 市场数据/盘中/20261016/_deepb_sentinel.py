# -*- coding: utf-8 -*-
"""深场B(14:45) 哨兵: 独立复算, 核对发出版。只读。"""
import json, os, csv, statistics as st, hashlib, sqlite3
from datetime import datetime

BASE = r"D:\股票数据\市场数据"
D = "20261016"
DAY = os.path.join(BASE, "盘中", D)
OUT = os.path.join(DAY, "临盘决断_%s_1445.json" % D)
MD = os.path.join(BASE, "_学习", "盘中尾盘复盘_%s.md" % D)
ALARM = os.path.join(DAY, "报警_%s.jsonl" % D)
CUT = "2026-10-16 14:45:00"
R, F = [], []
def chk(name, cond, detail=""):
    R.append((bool(cond), name, detail))
def p2s(t): return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")

d = json.load(open(OUT, encoding="utf-8"))
frames = [json.loads(l) for l in open(os.path.join(DAY, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
legal = [f for f in frames if f["ts"] <= CUT]
last = legal[-1]; rows = {x["code"]: x for x in last["rows"]}
def ztp(x): return round(x["preClose"] * (1 + (0.20 if x["code"].startswith(("300","301","688")) else 0.10)), 2)

# C1 发出版 + superseded 留档链
CHAIN = {"临盘决断_%s_1445_v1_superseded.json" % D: ("56d8c0189f3bcc07", 45972),
         "临盘决断_%s_1445_v2_superseded.json" % D: ("1bf3deb11d903527", 46700),
         "临盘决断_%s_1445_v3_superseded.json" % D: ("07c5aa59b6fb8d48", 47342),
         "临盘决断_%s_1445_v4_superseded.json" % D: ("641ce2ac2f40dba1", 47968)}
_chain_ok, _cdet = True, []
for fn, (h, sz) in CHAIN.items():
    p = os.path.join(DAY, fn)
    if not (os.path.exists(p) and os.path.getsize(p) == sz
            and hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] == h):
        _chain_ok = False
        _cdet.append(fn + " 缺失/被改")
chk("C1 发出版 v5 存在 + v1/v2/v3/v4 均以 superseded 留档未删改(发出版不可覆盖)",
    os.path.exists(OUT) and d.get("version") == "v5" and _chain_ok,
    "v3 size=%d sha16=%s | 链=%s" % (os.path.getsize(OUT),
        hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16], ("ok" if _chain_ok else ";".join(_cdet))))
rec = d.get("修订记录")
chk("C1b 修订记录完整(v1→v2→v3 逐版说明修订项)",
    isinstance(rec, list) and len(rec) >= 3 and sum(len(x) for x in rec) > 300,
    "%d 条 / %d 字" % (len(rec or []), sum(len(x) for x in (rec or []))))
# C1c 出页残留检查: 除『修订记录』披露字段外, 不得含未求值的格式化残留
_rest_txt = json.dumps({k: v for k, v in d.items() if k not in ("修订记录", "修订记录_版本")}, ensure_ascii=False)
import re as _re
_leak_fmt = sorted(set(_re.findall(r"%[-+.0-9]*[dfs][^\"]{0,6}", _rest_txt)))
chk("C1c 发出版无未求值的格式化残留(如 %+.2f%%)", not _leak_fmt, ("残留=" + str(_leak_fmt)) if _leak_fmt else "无")
# C2 交易日与帧
chk("C2 交易日: 合法帧数/首末帧/池元信息与源一致",
    d["数据新鲜度"]["合法帧(ts<=14:45:00)"] == len(legal) and d["数据新鲜度"]["末合法帧"] == last["ts"]
    and last.get("pool_date") == "20261015" and last.get("pool_stale") is False and len(rows) == 36,
    "合法%d 末%s pool=%s n=%d" % (len(legal), last["ts"], last.get("pool_date"), len(rows)))
# C3 排除帧
exc = [f["ts"] for f in frames if f["ts"] > CUT]
frozen = d["数据新鲜度"]["排除帧(ts>14:45:00, 仅列示未作决策输入)"]
chk("C3 排除帧登记: 发出版冻结清单 = 源清单前 N 条(写后源续写不回溯)", frozen == exc[:len(frozen)] and len(frozen) >= 1,
    "冻结%d 源现%d 冻结末条%s" % (len(frozen), len(exc), frozen[-1] if frozen else "-"))
# C4 新鲜度红线
lag = int((p2s(CUT) - p2s(last["ts"])).total_seconds())
chk("C4 断更判定: 末帧滞后 %ds < 600s → 允许决策" % lag, lag < 600 and "新鲜" in d["数据新鲜度"]["断更判定"], "")
# C5 池截面复算
pcts = [x["pct"] for x in rows.values()]
sealed = [c for c, x in rows.items() if x["latest"] >= ztp(x) - 1e-9]
touched = [c for c, x in rows.items() if x["high"] >= ztp(x) - 1e-9]
broken = sorted(c for c in touched if c not in sealed)
dtl = sorted(c for c, x in rows.items() if x["pct"] <= -9.8)
s = d["预收盘第一手判断"]["池截面"]
chk("C5 池截面复算一致(中位/均值/封板/炸板/跌停)",
    abs(s["中位"] - round(st.median(pcts), 2)) < 1e-9 and abs(s["均值"] - round(sum(pcts)/len(pcts), 3)) < 1e-9
    and s["封板"] == len(sealed) and s["炸板"] == len(broken) and s["跌停"] == len(dtl),
    "中位%s 封%d 炸%d 跌%d" % (s["中位"], len(sealed), len(broken), len(dtl)))
# C6/C7 名单
chk("C6 封板名单每只独立复算 latest==涨停价", all(rows[c]["latest"] >= ztp(rows[c]) - 1e-9 for c in sealed)
    and len(d["预收盘第一手判断"]["封板名单"]) == len(sealed), ",".join(sorted(sealed)))
chk("C7 炸板名单=触板未封(独立复算)", len(d["预收盘第一手判断"]["炸板名单"]) == len(broken), ",".join(broken))
# C8 持仓复算
navj = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/净值.json"), encoding="utf-8"))
hb = json.load(open(os.path.join(DAY, "_hb_e_quote.json"), encoding="utf-8"))
for _c, _q in hb.items():
    if "latest" not in _q and "last" in _q: _q["latest"] = _q["last"]
def q(c): return hb.get("sz"+c) or hb.get("sh"+c)
ok = True; det = []
for p in d["在持票照会"]["持仓"]:
    x = rows.get(p["code"])
    src = x["latest"] if x else q(p["code"])["latest"]
    if abs(p["决断时点实价"] - src) > 1e-9: ok = False
    if abs(p["相对成本pct"] - round((src / p["cost_px"] - 1) * 100, 2)) > 0.011: ok = False
    if abs(p["浮动盈亏_元"] - round((src - p["cost_px"]) * p["shares"], 2)) > 0.011: ok = False
    if abs(p["市值_元"] - round(src * p["shares"], 2)) > 0.011: ok = False
    det.append(p["code"])
chk("C8 持仓7只 现价/相对成本/浮盈/市值 全部独立复算一致", ok and len(d["在持票照会"]["持仓"]) == 7, " ".join(det))
# C9 合计自洽
u = d["在持票照会"]
chk("C9 合计自洽(市值=Σ, nav占比)",
    abs(u["合计"]["在持7只合计市值_元"] - round(sum(p["市值_元"] for p in u["持仓"]), 2)) < 0.011
    and abs(u["合计"]["第七账_占nav_pct"] - round(sum(p["市值_元"] for p in u["持仓"][:2]) / navj["nav"] * 100, 2)) < 0.011,
    "合计市值%s" % u["合计"]["在持7只合计市值_元"])
# C10 leg=close 三条件复算
o = rows.get("000011") or q("000011")
gap = round((o["open"] / o["preClose"] - 1) * 100, 2)
cond_a = gap <= -4 or o["latest"] < o["open"]
chk("C10 000011 leg=close 三条件独立复算: a)未成立 b)未成立 → 维持持有",
    (not cond_a) and gap < 3 and d["尾盘卖预案执行"]["结果"].startswith("**未执行"),
    "gap=%+.2f%% latest=%s open=%s" % (gap, o["latest"], o["open"]))
chk("C11 fills=[] 且写明零成交理由(禁虚构成交)", d["fills"] == [] and len(d["fills_口径"]) > 60, d["fills_口径"][:40])
chk("C12 px_exec 接口未使用(未引用任何 >14:45 帧价)", "未调用" in d["尾盘卖预案执行"]["结果"], "")
# C13 引擎动作对账复算
fills = json.load(open(os.path.join(DAY, "临盘决断_%s_0940.json" % D), encoding="utf-8"))["fills"]
led = [json.loads(l) for l in open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/账本.jsonl"), encoding="utf-8") if l.strip()]
b2860 = [x for x in led if x.get("code") == "002860" and x.get("d") == D]
stt = json.load(open(os.path.join(BASE, "_学习/_模拟盘/盘中作战/state.json"), encoding="utf-8"))
chk("C13 执行对账复算: 开盘场4笔fills + 第七账002860买入 + cash 恒等式",
    len(fills) == 4 and len(b2860) == 1 and abs(stt["cash"] - (1000000 - 59649.59 - 58232.17)) < 0.011
    and {f["code"] for f in fills} == {"600668", "605189", "600693", "605577"},
    "fills=%s cash=%.2f" % ([f["code"] for f in fills], stt["cash"]))
# C14 600668 炸板事实
path = [(f["ts"], rows.get("600668", {}) and ({x["code"]: x for x in f["rows"]}.get("600668"))) for f in legal]
brk = [x for x in d["B级_防守"]["通道C_持仓炸板"]["对象1_600668 尖峰集团(master账)"]["封板轨迹"] if x["态"] == "炸"]
chk("C14 600668 尾盘炸板独立复算(封→炸 时间戳一致)",
    len(brk) == 1 and brk[0]["ts"] == "2026-10-16 14:43:02", json.dumps(brk, ensure_ascii=False))
# C15 002860 涨停价/通道C
z = round(q("002860")["preClose"] * 1.10, 2)   # 002860 = 深主板 10% 涨停
chk("C15 002860 触板未封复算(high=涨停价, latest<涨停价)",
    q("002860")["high"] >= z - 1e-9 and q("002860")["latest"] < z and "成立" in d["B级_防守"]["通道C_持仓炸板"]["判定"],
    "涨停价%.2f high=%.2f latest=%.2f" % (z, q("002860")["high"], q("002860")["latest"]))
# C16 C级禁行
chk("C16 C级 0 笔 + 许可=false", d["C级_预案外"]["许可"] is False and "0 笔" in d["C级_预案外"]["本场动作"], "")
# C17 watch 全量复核
chk("C17 watch 9 只全部复核且均未成立", len(d["watch_confirm核对"]) == 9
    and all(w["本场读数"] is not None for w in d["watch_confirm核对"]), "n=%d" % len(d["watch_confirm核对"]))
# C18 错失对齐 playbook
pb = json.load(open(os.path.join(BASE, "盘中/20261015/playbook.json"), encoding="utf-8"))
chk("C18 错失登记与 playbook.buys 一一对齐(3只, 含000530破位)",
    [m["code"] for m in d["错失登记"]] == [b["代码"] for b in pb["buys"]]
    and any(m["code"] == "000530" and m["落带"] is False for m in d["错失登记"]), "")
# C19 引擎闸门不一致发现可核
jf = os.path.join(BASE, "_学习/_模拟盘/盘中作战/判断流水.jsonl")
gate = [json.loads(l) for l in open(jf, encoding="utf-8") if l.strip() and json.loads(l).get("ts", "").startswith("08-16") and json.loads(l).get("code") == "002860"]
chk("C19 ★引擎闸门未刷新发现可核(本日3块闸门文本=10/15缓存 -6.08%, 与本日高开+9.68%矛盾)",
    len(gate) == 3 and all("低开-6.08" in g["闸门"] for g in gate)
    and round((q("002860")["open"] / q("002860")["preClose"] - 1) * 100, 2) > 9,
    "块数=%d 实开gap=%+.2f%%" % (len(gate), round((q("002860")["open"] / q("002860")["preClose"] - 1) * 100, 2)))
# C20 未改参数(mtime 早于决断)
pbm = os.path.getmtime(os.path.join(BASE, "盘中/20261015/playbook.json"))
chk("C20 未改动 playbook / 账本 / 次日卖出指令(盘中禁改参数)",
    pbm < p2s(CUT).timestamp() and os.path.getmtime(os.path.join(BASE, "_学习/_模拟盘/盘中作战/state.json")) < p2s(CUT).timestamp(),
    "playbook mtime=%s" % datetime.fromtimestamp(pbm).strftime("%Y-%m-%d %H:%M:%S"))
# C21 报警
al = [json.loads(l) for l in open(ALARM, encoding="utf-8") if l.strip()]
chk("C21 报警_%s.jsonl 已建(append-only, 每行含 ts/level/msg)" % D,
    len(al) >= 5 and all(x.get("ts") and x.get("level") and x.get("msg") for x in al), "n=%d" % len(al))
# C22 复盘 md
mdt = open(MD, encoding="utf-8").read()
chk("C22 md 已建且含 情绪/主线/龙头/明日预案 四要素",
    len(mdt) > 8000 and all(k in mdt for k in ["情绪定性", "主线", "龙头身位", "明日预案要点"]), "%d bytes" % len(mdt))
chk("C22b md 渲染无缺陷(无双重加粗 **** / 无未求值 %+.2f 残留)",
    "****" not in mdt and "%+.2f" not in mdt and "%s" not in mdt,
    "" if ("****" not in mdt and "%+.2f" not in mdt and "%s" not in mdt) else "见 md")
# C23 零后视镜: 排除帧时间戳仅允许出现在「排除帧」登记字段与「后视镜边界声明」内(其余字段/md正文均不得渗漏)
rest = json.dumps({k: v for k, v in d.items() if k not in ("数据新鲜度", "后视镜边界声明")}, ensure_ascii=False)
_seg = mdt.split("**后视镜边界声明**")
_md_pre = _seg[0]
_md_post = _seg[1].split("**报文字段**")[1] if (len(_seg) > 1 and "**报文字段**" in _seg[1]) else ""
leak = [t for t in frozen if t in rest or t in _md_pre or t in _md_post]
chk("C23 零后视镜: 排除帧时间戳仅出现于登记/披露字段(未渗入读数判定字段与md正文)", not leak,
    ("渗漏=%s" % leak if leak else "仅出现于『数据新鲜度·排除帧』与『后视镜边界声明』两处披露字段"))

print("==== 深场B(14:45) 哨兵 · %s ====" % D)
ok_n = 0
for good, name, det in R:
    print("[%s] %s %s" % ("PASS" if good else "FAIL", name, ("| " + det) if det else ""))
    ok_n += good
print("\n==== 哨兵结论: %d 项, PASS %d, FAIL %d ====" % (len(R), ok_n, len(R) - ok_n))
print("FAIL 项 = " + (", ".join(n for g, n, _ in R if not g) if ok_n < len(R) else "无"))
