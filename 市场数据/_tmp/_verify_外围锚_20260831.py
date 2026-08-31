# -*- coding: utf-8 -*-
"""外围盘前锚 20260831: HSI.HK / USDCNH.FX / NDX.GI 用 iFinD"""
import json
import iFinDPy

auth = json.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
print("登录:", iFinDPy.THS_iFinDLogin(auth["account"], auth["password"]))

codes = "HSI.HK,USDCNH.FX,NDX.GI"

print("\n=== RealtimeQuotes ===")
try:
    r = iFinDPy.THS_RealtimeQuotes(codes, "open;preClose;latest;changeRatio")
    print(json.dumps(r, ensure_ascii=False, default=str)[:4000])
except Exception as e:
    print("RQ异常:", repr(e))

print("\n=== THS_HQ ===")
try:
    r = iFinDPy.THS_HQ(codes, "open;preClose;latest;changeRatio")
    print(json.dumps(r, ensure_ascii=False, default=str)[:4000])
except Exception as e:
    print("THS_HQ异常:", repr(e))
