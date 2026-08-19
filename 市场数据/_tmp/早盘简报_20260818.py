# -*- coding: utf-8 -*-
"""早盘简报 20260818: 读竞价快照 + 外围盘前锚(THS_HQ/RealtimeQuotes)"""
import os, json, sys
import pandas as pd

ARC = r"D:\股票数据\市场数据\_学习\竞价快照存档"
d = "20260818"
fp = os.path.join(ARC, d + ".csv.gz")

print("=== 竞价快照读取 ===")
df = pd.read_csv(fp, compression="gzip")
df["代码"] = df["代码"].astype(str).str.zfill(6)
print("总条数:", len(df))

# 数值列
for c in ("今开", "昨收", "最新价", "成交额"):
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
if "高开幅度" not in df.columns:
    df["高开幅度"] = ((df["今开"] / df["昨收"] - 1) * 100).round(2)

# 高开/低开分布
ga = df["高开幅度"]
low = (ga <= 0).sum()
open05 = ((ga > 0) & (ga < 5)).sum()
open5p = (ga >= 5).sum()
print(f"低开<=0: {low} | 高开0~5: {open05} | 高开>=5: {open5p}")

# 一字板(今开≈涨停价): 30/68开头20%涨停, 其余10%
def is_yizi(code, ga):
    if code.startswith(("30", "68")):
        return ga >= 19.8
    return ga >= 9.8
df["_一字"] = df.apply(lambda r: is_yizi(r["代码"], r["高开幅度"]), axis=1)
yizi = df[df["_一字"]]
print("一字板数(今开≈涨停价):", len(yizi))
print("一字票:", yizi[["代码", "名称", "高开幅度", "成交额"]].head(30).to_string(index=False))

# 竞价额Top5
top5 = df.nsmallest(5, "成交额") if False else df.sort_values("成交额", ascending=False).head(5)
print("\n=== 竞价额Top5 ===")
print(top5[["代码", "名称", "高开幅度", "成交额"]].to_string(index=False))

# 盯盘清单(昨晚观察票 + 推演重点盯的票)
watch = {
    "002081": "金螳螂(4板观察)",
    "603186": "华正新材(2板观察)",
    "603118": "共进股份(3板观察)",
    "603330": "天洋新材(4板龙头)",
    "002172": "澳洋健康(4板龙头)",
    "002156": "通富微电(席位共振)",
    "300684": "中石科技(2板算力)",
    "300394": "天孚通信(CPO抢筹)",
    "300308": "中际旭创(CPO抢筹)",
    "600487": "亨通光电(CPO抢筹)",
}
print("\n=== 盯盘清单今晨竞价 ===")
for code, tag in watch.items():
    row = df[df["代码"] == code]
    if row.empty:
        print(f"{code} {tag}: 快照缺失(无此代码)")
        continue
    r = row.iloc[0]
    print(f"{code} {r['名称']} {tag}: 高开{r['高开幅度']}% 竞价额{r['成交额']/1e8:.2f}亿 竞价额排名{int(r['竞价额排名']) if '竞价额排名' in r and pd.notna(r['竞价额排名']) else 'NA'}")

# 全场竞价额Top12(供对齐判断)
print("\n=== 全场竞价额Top12 ===")
print(df.sort_values("成交额", ascending=False).head(12)[["代码", "名称", "高开幅度", "成交额"]].to_string(index=False))
