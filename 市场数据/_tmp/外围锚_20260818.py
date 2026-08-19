# -*- coding: utf-8 -*-
"""外围盘前锚 20260818: HSI.HK / USDCNH.FX / NDX.GI 用 iFinD"""
import json
import iFinDPy

auth = json.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
print("登录:", iFinDPy.THS_iFinDLogin(auth["account"], auth["password"]))

codes = "HSI.HK,USDCNH.FX,NDX.GI"

# 尝试1: RealtimeQuotes
for fields in ["open;preClose;latest;changeRatio", "open;preClose;latest"]:
    print(f"\n=== RealtimeQuotes fields={fields} ===")
    try:
        r = iFinDPy.THS_RealtimeQuotes(codes, fields)
        print(json.dumps(r, ensure_ascii=False, default=str)[:2000])
    except Exception as e:
        print("RQ异常:", e)

# 尝试2: THS_HQ 如果存在
print("\n=== THS_HQ ===")
try:
    r = iFinDPy.THS_HQ(codes, "open;preClose;latest;changeRatio")
    print(json.dumps(r, ensure_ascii=False, default=str)[:2000])
except Exception as e:
    print("THS_HQ异常:", e)

# 尝试3: 历史行情(昨收/今收) THS_HistoryQuotes
print("\n=== THS_HistoryQuotes ===")
try:
    r = iFinDPy.THS_HistoryQuotes(codes, "open;preClose;close;changeRatio", "interval:D,startDate:2026-08-14,endDate:2026-08-18")
    print(json.dumps(r, ensure_ascii=False, default=str)[:2000])
except Exception as e:
    print("HQ异常:", e)
