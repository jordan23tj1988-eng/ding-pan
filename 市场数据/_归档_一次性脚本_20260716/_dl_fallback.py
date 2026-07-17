# -*- coding: utf-8 -*-
import socket, json, os, collections, datetime
socket.setdefaulttimeout(20)
import importlib.util, sys
spec = importlib.util.spec_from_file_location("dl", "市场数据下载.py")
dl = importlib.util.module_from_spec(spec)
# avoid running main
import types
spec.loader.exec_module(dl)
import pandas as pd
d = "20260715"
OUT = os.path.join(dl.BASE, d)
# LHB via direct API (bounded 15s per request)
lhb = dl.fetch_lhb_direct(d)
if lhb is not None and len(lhb) > 0:
    lhb.to_csv(os.path.join(OUT, "lhb.csv"), index=False, encoding="utf-8-sig")
    print("lhb rows:", len(lhb))
else:
    print("lhb EMPTY/None")
# turnover
try:
    to = dl.turnover_yi()
except Exception as e:
    to = None
    print("turnover err", e)
print("turnover", to)
