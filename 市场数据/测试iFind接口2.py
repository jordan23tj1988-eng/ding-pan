# -*- coding: utf-8 -*-
r"""测试iFind接口2.py — 第二轮探测: 概念指数正确取法 + 北交所行情覆盖(2026-07-18 #011)
双击 测试iFind接口2.bat。产物: _学习/ifind_测试报告2_{d}.json (全部记原始repr,沙箱照实修)。"""
import os, sys, json, datetime, traceback
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
import ifind_source as ifs

d = datetime.date.today()
ds = d.strftime("%Y-%m-%d"); start = (d - datetime.timedelta(days=9)).strftime("%Y-%m-%d")
rep = {"d": d.strftime("%Y%m%d"), "start": str(datetime.datetime.now()), "probes": {}}

if not ifs.login():
    rep["probes"]["登录"] = {"ok": False}
else:
    THS = ifs._mod()
    def raw(name, fn):
        try:
            v = fn()
            r = {"repr": repr(v)[:1500]}
            df = ifs._to_df(v)
            if df is not None and len(df):
                r["df_cols"] = [str(c) for c in df.columns]; r["df_shape"] = list(df.shape)
                r["df_head"] = json.loads(df.head(6).to_json(orient="records", force_ascii=False))
        except Exception as e:
            r = {"exc": "%s\n%s" % (e, traceback.format_exc()[-400:])}
        rep["probes"][name] = r
        print(name, "->", ("EXC " + r["exc"][:100]) if "exc" in r else r["repr"][:120].replace("\n", " "))

    # —— 概念指数五路 ——
    raw("iwencai_概念指数_zhishu", lambda: THS.THS_iwencai("概念指数", "zhishu"))
    raw("iwencai_同花顺概念指数", lambda: THS.THS_iwencai("同花顺概念指数", "zhishu"))
    raw("iwencai_概念指数涨跌幅", lambda: THS.THS_iwencai("概念指数的涨跌幅", "zhishu"))
    raw("RQ_直连概念码885556", lambda: THS.THS_RQ("885556.TI,885728.TI,885866.TI", "latest,changeRatio"))
    raw("HQ_直连概念码885556", lambda: THS.THS_HQ("885556.TI", "close,changeRatio", "", start, ds))
    for bid in ("001005393", "001005266", "001005341"):
        raw("DP_block_" + bid, lambda b=bid: THS.THS_DP("block", "%s;%s" % (ds, b), "date:Y,thscode:Y,security_name:Y"))
    # —— 北交所两路(920992在全A清单里有) ——
    raw("RQ_北交所920992", lambda: THS.THS_RQ("920992.BJ,920305.BJ", "open,latest,changeRatio,preClose"))
    raw("HQ_北交所920992", lambda: THS.THS_HQ("920992.BJ", "open,close,volume", "", start, ds))

rep["end"] = str(datetime.datetime.now())
outp = os.path.join(BASE, "_学习", "ifind_测试报告2_%s.json" % d.strftime("%Y%m%d"))
with open(outp, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print("报告已写: " + outp)
ifs.logout()
