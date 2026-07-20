# -*- coding: utf-8 -*-
"""一次性:补 920305(北交所) 20260717 日bar进 _bars_cache(宿主跑,sina bj前缀)。用完即弃。"""
import os, glob, pandas as pd
BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    BASE = glob.glob("/sessions/*/mnt/股票数据/市场数据")[0]
import akshare as ak
f = os.path.join(BASE, "_学习", "_bars_cache", "920305.csv")
old = pd.read_csv(f)
b = ak.stock_zh_a_daily(symbol="bj920305", start_date="20260710", end_date="20260717")
b["date"] = b["date"].astype(str).str[:10]
add = b[~b["date"].isin(old["date"].astype(str))]
if len(add):
    cols = [c for c in old.columns if c in b.columns]
    pd.concat([old, add[cols]], ignore_index=True).to_csv(f, index=False)
    print("追加", len(add), "行 ->", f)
else:
    print("无新行(已是最新)")
print(pd.read_csv(f).tail(2).to_string())
