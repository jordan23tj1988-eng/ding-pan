# -*- coding: utf-8 -*-
"""剔除停牌(今开<=0)后重算宽度; 并与20261019/20261016同口径对照"""
import gzip, os
import pandas as pd
ARC = r"D:\股票数据\市场数据\_学习\竞价快照存档"

def load(d):
    df = pd.read_csv(gzip.open(os.path.join(ARC, d + ".csv.gz"), "rt", encoding="utf-8"), dtype={"代码": str})
    df["代码"] = df["代码"].str.zfill(6)
    for c in ("今开", "昨收", "最新价", "成交额"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["高开幅度"] = (df["今开"] / df["昨收"] - 1) * 100
    live = df[(df["昨收"] > 0) & (df["今开"] > 0)].copy()
    return df, live

for d in ("20261016", "20261019", "20261020"):
    raw, df = load(d)
    n = len(df)
    print("\n===== %s  原始%d行 → 有效%d只(剔停牌%d) =====" % (d, len(raw), n, len(raw) - n))
    print("中位%.2f%% 均值%.2f%% 低开<0 %d(%.1f%%) 低开≤0 %d(%.1f%%)"
          % (df["高开幅度"].median(), df["高开幅度"].mean(),
             (df["高开幅度"] < 0).sum(), (df["高开幅度"] < 0).sum() * 100.0 / n,
             (df["高开幅度"] <= 0).sum(), (df["高开幅度"] <= 0).sum() * 100.0 / n))
    for th in (1, 2, 3, 5, 7):
        k = (df["高开幅度"] >= th).sum()
        print("   ≥%d%%: %d (%.2f%%)" % (th, k, k * 100.0 / n), end="")
    print()
    print("   竞价额合计%.1f亿  中位成交额%.0f万" % (df["成交额"].sum() / 1e8, df["成交额"].median() / 1e4))
