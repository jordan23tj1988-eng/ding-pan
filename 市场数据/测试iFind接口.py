# -*- coding: utf-8 -*-
"""测试iFind接口.py — iFind接入探测五连(仅宿主运行, 2026-07-18 变更总账#011)
双击 测试iFind接口.bat 运行。产物: _学习/ifind_测试报告_{d}.json (沙箱读它定切源方案)。
探测项: ①登录 ②日K ③全A清单 ④实时快照 ⑤概念指数涨幅。每项记录 ok/样本/原始结构。
"""
import os, sys, json, datetime, traceback
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
import ifind_source as ifs

d = datetime.date.today().strftime("%Y%m%d")
rep = {"d": d, "start": str(datetime.datetime.now()), "probes": {}}

def probe(name, fn):
    r = {"ok": False}
    try:
        v = fn()
        if v is None:
            r["err"] = "返回None"
        else:
            r["ok"] = True
            try:
                r["shape"] = list(getattr(v, "shape", []) or [])
                r["columns"] = [str(c) for c in getattr(v, "columns", [])]
                r["sample"] = json.loads(v.head(8).to_json(orient="records", force_ascii=False))
            except Exception:
                r["sample"] = repr(v)[:800]
    except Exception as e:
        r["err"] = "%s\n%s" % (e, traceback.format_exc()[-600:])
    rep["probes"][name] = r
    print(("[√] " if r["ok"] else "[X] ") + name + ("" if r["ok"] else "  " + str(r.get("err", ""))[:200]))
    return r["ok"]

# ① 登录
ok = ifs.login()
rep["probes"]["1_登录"] = {"ok": bool(ok)}
print(("[√] " if ok else "[X] ") + "1_登录")
if ok:
    day = datetime.date.today()
    start = (day - datetime.timedelta(days=12)).strftime("%Y-%m-%d")
    end = day.strftime("%Y-%m-%d")
    # ② 日K: 万科A+一只北交所, 验证代码后缀/字段名/北交所覆盖
    probe("2_日K", lambda: ifs.daily_bars(["000002", "920305"], start, end))
    # ③ 全A清单
    probe("3_全A清单", lambda: ifs.all_a_codes())
    # ④ 实时快照(盘后=收盘口径): 沪深北各一
    probe("4_实时快照", lambda: ifs.spot(["000002", "600519", "920305"]))
    # ⑤ 概念指数涨幅
    probe("5_概念指数", lambda: ifs.concept_index_quotes())
    # 附: 模块里没包的原始调用, 留结构样本帮沙箱侧适配
    try:
        THS = ifs._mod()
        raw = THS.THS_HQ("000002.SZ", "open,close,volume", "", start, end) if hasattr(THS, "THS_HQ") else THS.THS_HistoryQuotes("000002.SZ", "open,close,volume", "", start, end)
        rep["raw_hq_repr"] = repr(raw)[:1500]
        rep["has_new_api"] = {n: hasattr(THS, n) for n in ("THS_HQ", "THS_RQ", "THS_DP", "THS_BD", "THS_iwencai", "THS_HistoryQuotes", "THS_RealtimeQuotes", "THS_DataPool")}
    except Exception as e:
        rep["raw_hq_repr"] = "EXC " + str(e)
rep["end"] = str(datetime.datetime.now())
outp = os.path.join(BASE, "_学习", "ifind_测试报告_%s.json" % d)
os.makedirs(os.path.dirname(outp), exist_ok=True)
with open(outp, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print("报告已写: " + outp)
ifs.logout()
