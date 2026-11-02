# -*- coding: utf-8 -*-
"""外围盘前锚 20261102: HSI.HK / USDCNH.FX / NDX.GI
优先 THS_RealtimeQuotes(latest;preClose;open;changeRatio)，兜底 THS_HQ 日线近10日
只打印真实返回，不推断。拿不到就输出"缺"。
"""
import json
try:
    import iFinDPy
    a = json.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
    rc = iFinDPy.THS_iFinDLogin(a["account"], a["password"])
    print("login rc=", rc)
except Exception as e:
    print("初始化失败:", e); raise SystemExit(0)

codes = "HSI.HK,USDCNH.FX,NDX.GI"
for f in ["latest;preClose;open;changeRatio;time", "latest;preClose;open;changeRatio", "latest;preClose"]:
    try:
        rt = iFinDPy.THS_RealtimeQuotes(codes, f)
        ec = rt.get("errorcode") if isinstance(rt, dict) else "?"
        print("=== RealtimeQuotes funcs=%s errorcode=%s" % (f, ec))
        print(json.dumps(rt, ensure_ascii=False)[:2500])
        if ec == 0:
            break
    except Exception as e:
        print("RealtimeQuotes异常(%s): %s" % (f, e))

print("\n=== THS_HQ 日线 close 近12日 ===")
for c in ["HSI.HK", "USDCNH.FX", "NDX.GI"]:
    try:
        h = iFinDPy.THS_HQ(c, "close;open;preClose", "2026-10-19", "2026-11-02", "D")
        ec = h.get("errorcode") if isinstance(h, dict) else "?"
        print("--- %s errorcode=%s" % (c, ec))
        if isinstance(h, dict) and h.get("tables"):
            for t in h["tables"]:
                print("  time:", t.get("time"))
                print("  thscode:", t.get("thscode"))
                print("  table:", json.dumps(t.get("table"), ensure_ascii=False)[:1800])
        else:
            print("  raw:", json.dumps(h, ensure_ascii=False)[:800])
    except Exception as e:
        print("THS_HQ异常 %s: %s" % (c, e))
