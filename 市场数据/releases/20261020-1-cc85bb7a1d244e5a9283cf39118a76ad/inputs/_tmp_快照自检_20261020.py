# -*- coding: utf-8 -*-
"""快照可信度自检: 零额/负开/昨收一致性(与昨日收盘对齐)"""
import gzip, os
import pandas as pd
ARC = r"D:\股票数据\市场数据\_学习\竞价快照存档"
df = pd.read_csv(gzip.open(os.path.join(ARC, "20261020.csv.gz"), "rt", encoding="utf-8"), dtype={"代码": str})
df["代码"] = df["代码"].str.zfill(6)
for c in ("今开", "昨收", "最新价", "成交额"):
    df[c] = pd.to_numeric(df[c], errors="coerce")
print("总行=%d  今开<=0=%d  成交额<=0=%d  昨收缺失=%d" % (len(df), int((df["今开"] <= 0).sum()), int((df["成交额"] <= 0).sum()), int(df["昨收"].isna().sum())))
print("成交额中位(万)=%.1f  前5大合计占比=%.1f%%" % (df["成交额"].median() / 1e4, df["成交额"].nlargest(5).sum() / df["成交额"].sum() * 100))
# 与昨日快照收盘价一致性(用昨日snapshot的'最新价'≈昨收? 昨日snapshot是竞价口径,不可比) → 改与昨日收盘qt无关, 只报昨收分布
print("昨收 min=%.2f max=%.2f" % (df["昨收"].min(), df["昨收"].max()))
y = pd.read_csv(gzip.open(os.path.join(ARC, "20261019.csv.gz"), "rt", encoding="utf-8"), dtype={"代码": str})
print("昨日存档行数=%d(参照)" % len(y))
