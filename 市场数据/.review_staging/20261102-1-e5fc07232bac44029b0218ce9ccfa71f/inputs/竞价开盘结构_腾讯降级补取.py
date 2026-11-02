# -*- coding: utf-8 -*-
"""20260917 开盘结构补取(腾讯降级源) —— 只读实时快照, 只取 今开/昨收/最高/最低/涨停价,
不取成交额(12:xx为盘中累计,口径污染)。输出明确标注"非A档·腾讯降级·不入训练"。
"""
import os, sys, json, time, math
import pandas as pd
import requests

ARC = r"D:\股票数据\市场数据\_学习\竞价快照存档"
MAPF = os.path.join(ARC, "代码名称映射.csv")
SL = r"D:\股票数据\量价因子库\data\meta\stock_list.csv"
OUT = os.path.join(ARC, "20260917_开盘结构_腾讯降级_非A档.json")

# ---- 代码表 ----
df = pd.read_csv(MAPF, dtype=str)
df.columns = [c.strip() for c in df.columns]
print("映射表列:", list(df.columns), "行数:", len(df))
ccol = "code" if "code" in df.columns else df.columns[0]
ncol = "name" if "name" in df.columns else df.columns[1]
codes = {}
for c, n in zip(df[ccol], df[ncol]):
    c = str(c).strip().zfill(6)
    if len(c) == 6 and c.isdigit():
        codes[c] = str(n).strip()
print("A股代码数:", len(codes))

# ---- 腾讯代码前缀 ----
def tx(c):
    if c[0] == "6":
        return "sh" + c
    if c[0] in "03":
        return "sz" + c
    return "bj" + c

def fetch(batch):
    url = "https://qt.gtimg.cn/q=" + ",".join(batch)
    for a in range(3):
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            r.encoding = "gbk"
            return r.text
        except Exception as e:
            if a == 2:
                print("批次失败:", str(e)[:80]); return ""
            time.sleep(0.6)

allc = sorted(codes.keys())
res = {}
t0 = time.time()
B = 60
fails = 0
for i in range(0, len(allc), B):
    grp = [tx(c) for c in allc[i:i + B]]
    txt = fetch(grp)
    if not txt:
        fails += 1
        continue
    for ln in txt.strip().split("\n"):
        if '="' not in ln:
            continue
        body = ln.split('="', 1)[1].rstrip('";').strip()
        f = body.split("~")
        if len(f) < 49:
            continue
        def num(k):
            try:
                return float(f[k])
            except Exception:
                return None
        res[f[2]] = dict(名称=f[1], 现价=num(3), 昨收=num(4), 今开=num(5),
                         最高=num(33), 最低=num(34), 涨停价=num(47), 跌停价=num(48),
                         量手=num(6))
print("取到:", len(res), "耗时%.1fs" % (time.time() - t0), "失败批次:", fails)

rows = []
for c, d in res.items():
    if not d["昨收"] or not d["今开"] or d["昨收"] <= 0 or d["今开"] <= 0:
        continue
    lim = d["涨停价"] or 0
    gap = (d["今开"] / d["昨收"] - 1) * 100
    zt_open = bool(lim and d["今开"] >= lim - 0.005)
    hi, lo = d["最高"], d["最低"]
    yizi = bool(zt_open and hi and lo and abs(hi - lim) < 0.005 and abs(lo - lim) < 0.005)
    rows.append(dict(代码=c, 名称=d["名称"] or codes.get(c, ""), 今开=d["今开"], 昨收=d["昨收"],
                     高开幅度=round(gap, 2), 开盘涨停=zt_open, 一字至午盘=yizi,
                     现价=d["现价"], 最高=hi, 最低=lo, 涨停价=lim, 现涨幅=round((d["现价"]/d["昨收"]-1)*100, 2) if d["现价"] else None))
d2 = pd.DataFrame(rows)
print("有效样本:", len(d2))

def bucket(g):
    if g >= 9.7: return "①开盘涨停(含一字)"
    if g >= 5: return "②高开≥5%"
    if g >= 2: return "③高开2~5%"
    if g > 0.05: return "④高开0~2%"
    if g > -0.05: return "⑤平开"
    if g > -2: return "⑥低开0~2%"
    if g > -5: return "⑦低开2~5%"
    return "⑧低开≥5%"

d2["桶"] = d2["高开幅度"].apply(bucket)
order = ["①开盘涨停(含一字)", "②高开≥5%", "③高开2~5%", "④高开0~2%", "⑤平开",
         "⑥低开0~2%", "⑦低开2~5%", "⑧低开≥5%"]
dist = {k: int((d2["桶"] == k).sum()) for k in order}
n = len(d2)
print("\n== 开盘(gap)分布 ==", {k: "%d(%.1f%%)" % (v, v / n * 100) for k, v in dist.items()})
print("高开家数:", int((d2["高开幅度"] > 0.05).sum()), "低开家数:", int((d2["高开幅度"] < -0.05).sum()))
print("开盘涨停:", int(d2["开盘涨停"].sum()), "| 一字(截至12:xx):", int(d2["一字至午盘"].sum()))

print("\n== 开盘涨停名单(按高开幅度) ==")
print(d2[d2["开盘涨停"]].sort_values("高开幅度", ascending=False)[["代码", "名称", "高开幅度", "现涨幅"]].to_string(index=False))

print("\n== 一字(截至12:xx)名单 ==")
print(d2[d2["一字至午盘"]][["代码", "名称", "高开幅度", "现涨幅"]].to_string(index=False))

print("\n== 9/11竞价路盯的3票 今晨开盘实价 ==")
for c in ["600876", "000993", "002912"]:
    r = d2[d2["代码"] == c]
    if len(r):
        r = r.iloc[0]
        print(f"  {c} {r['名称']}: 昨收{r['昨收']} 今开{r['今开']} gap={r['高开幅度']}% 现价{r['现价']} 现涨幅{r['现涨幅']}% 开盘涨停={r['开盘涨停']}")
    else:
        print("  ", c, "未取到")

print("\n== 指数(腾讯) ==")
idx = requests.get("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688,r_hkHSI,usNDX,usDJI,usIXIC", timeout=20)
idx.encoding = "gbk"
for ln in idx.text.strip().split("\n"):
    if '="' not in ln:
        continue
    f = ln.split('="', 1)[1].rstrip('";').split("~")
    nm = f[1]
    chg = f[32]
    price = f[3]
    tm = f[30]
    print(f"  {nm}: {price} ({chg}%) @{tm}")

json.dump(dict(日="20260917", 生成时间=time.strftime("%Y-%m-%d %H:%M:%S"),
               来源="腾讯qt.gtimg.cn(降级源)", A档=False,
               口径声明="仅取今开/昨收/最高/最低/涨停价(9:25集合竞价定价, 事后固定); 未取成交额(12:xx=盘中累计, 口径污染); 非竞价快照A档, 不入训练, 不替代 safter存档",
               样本=int(n), 分布=dist, 一字家数=int(d2["一字至午盘"].sum()),
               开盘涨停家数=int(d2["开盘涨停"].sum()),
               明细=d2.to_dict("records")),
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已写:", OUT)
