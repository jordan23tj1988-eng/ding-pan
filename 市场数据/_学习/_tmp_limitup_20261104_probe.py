# -*- coding: utf-8 -*-
import sys, json, time
sys.path.insert(0, r"D:/股票数据/市场数据")
import 涨停质量训练 as M
import pandas as pd
t0=time.time()
P=M._factor_table()
print("factor_table", P.shape, list(P.columns)[:30], "%.1fs"%(time.time()-t0))
D=M._enrich(P)
print("enrich", D.shape, list(D.columns))
print(D.head(2).to_string()[:1200])
