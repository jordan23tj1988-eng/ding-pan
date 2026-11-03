# -*- coding: utf-8 -*-
"""外围盘前锚: HSI.HK / USDCNH.FX / NDX.GI (iFinD RealtimeQuotes + THS_HQ 兜底)"""
import json, traceback
try:
    import iFinDPy
    a = json.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
    rc = iFinDPy.THS_iFinDLogin(a["account"], a["password"])
    print("login rc=", rc)
except Exception as e:
    print("初始化失败:", e); raise SystemExit(0)

codes = "HSI.HK,USDCNH.FX,NDX.GI"
funcs = ["latest;preClose;open;changeRatio", "latest;preClose", "latest;preClose;change"]
ok = False
for f in funcs:
    try:
        rt = iFinDPy.THS_RealtimeQuotes(codes, f)
        print("--- funcs=%s errcode=%s" % (f, rt.get("errorcode") if isinstance(rt, dict) else "?"))
        if isinstance(rt, dict):
            print(json.dumps(rt, ensure_ascii=False)[:2000])
            if rt.get("errorcode") == 0:
                ok = True
                break
    except Exception as e:
        print("异常 funcs=%s: %s" % (f, e))

if not ok:
    try:
        h = iFinDPy.THS_HQ(codes, "close", "2026-10-21", "2026-10-30", "D")
        print("--- THS_HQ errcode=", h.get("errorcode") if isinstance(h, dict) else "?")
        print(json.dumps(h, ensure_ascii=False)[:3000])
    except Exception as e:
        print("THS_HQ异常:", e)
        traceback.print_exc()
