# -*- coding: utf-8 -*-
"""早盘简报 20260826: 读竞价快照 + 盯盘清单 + 昨日0825池8只今晨竞价"""
import os, json
import pandas as pd

ARC = r"D:\股票数据\市场数据\_学习\竞价快照存档"
d = "20260826"
fp = os.path.join(ARC, d + ".csv.gz")

df = pd.read_csv(fp, compression="gzip")
df["代码"] = df["代码"].astype(str).str.zfill(6)
print("总条数:", len(df))

for c in ("今开", "昨收", "最新价", "成交额"):
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
if "高开幅度" not in df.columns:
    df["高开幅度"] = ((df["今开"] / df["昨收"] - 1) * 100).round(2)

ga = df["高开幅度"]
low = (ga <= 0).sum()
open05 = ((ga > 0) & (ga < 5)).sum()
open5p = (ga >= 5).sum()
print(f"低开<=0: {low} ({low/len(df)*100:.1f}%) | 高开0~5: {open05} ({open05/len(df)*100:.1f}%) | 高开>=5: {open5p} ({open5p/len(df)*100:.1f}%)")

# 一字板(今开≈涨停价)
def is_yizi(code, g):
    if code.startswith(("30", "68")):
        return g >= 19.8
    return g >= 9.8
df["_一字"] = df.apply(lambda r: is_yizi(r["代码"], r["高开幅度"]), axis=1)
yizi = df[df["_一字"]]
print("一字板数(今开≈涨停价):", len(yizi))
print("一字票:", yizi[["代码", "名称", "高开幅度", "成交额"]].sort_values("成交额", ascending=False).head(25).to_string(index=False))

print("\n=== 竞价额Top5 ===")
print(df.sort_values("成交额", ascending=False).head(5)[["代码", "名称", "高开幅度", "成交额"]].to_string(index=False))

# 盯盘清单: 昨晚竞价路观察票 + 推演盯票
watch = {
    "002412": "汉森制药(5板·中药/创新药·最高板观察)",
    "000017": "深中华A(4板·黄金珠宝·次高板观察)",
    "002041": "登海种业(2板·农业萌发·推演盯)",
    "003040": "楚天龙(3板·数字货币·推演盯)",
    "300308": "中际旭创(AI算力·低开背离对齐)",
    "603986": "兆易创新(AI算力·低开背离对齐)",
    "600487": "亨通光电(AI算力·低开背离对齐)",
    "300502": "新易盛(AI算力·低开背离对齐)",
    "002384": "东山精密(AI算力·低开背离对齐)",
    "600460": "士兰微(AI算力·低开背离对齐)",
    "688766": "普冉股份(AI算力·低开背离对齐)",
}
print("\n=== 盯盘清单今晨竞价 ===")
for code, tag in watch.items():
    row = df[df["代码"] == code]
    if row.empty:
        print(f"{code} {tag}: 快照缺失(无此代码)")
        continue
    r = row.iloc[0]
    rank = r["竞价额排名"] if ("竞价额排名" in r.index and pd.notna(r["竞价额排名"])) else "NA"
    print(f"{code} {r['名称']} {tag}: 高开{r['高开幅度']}% 竞价额{r['成交额']/1e8:.2f}亿 排名{int(rank) if str(rank).replace('.','',1).isdigit() else rank}")

# 昨日0825池8只今晨竞价(结算对象,验证"空仓被证伪")
pool825 = {
    "000017": "深中华A", "002445": "中南文化", "600984": "建设机械", "002084": "海鸥住工",
    "600127": "金健米业", "600508": "上海能源", "002880": "卫光生物", "000428": "华天酒店",
}
print("\n=== 昨日0825池8只今晨竞价(闸门高开≥5必弃检查) ===")
for code, name in pool825.items():
    row = df[df["代码"] == code]
    if row.empty:
        print(f"{code} {name}: 快照缺失")
        continue
    r = row.iloc[0]
    flag = "【≥5必弃】" if r["高开幅度"] >= 5 else ("【平开/低开】" if r["高开幅度"] <= 0 else "【0~5可观察】")
    print(f"{code} {name}: 高开{r['高开幅度']}% {flag}")
