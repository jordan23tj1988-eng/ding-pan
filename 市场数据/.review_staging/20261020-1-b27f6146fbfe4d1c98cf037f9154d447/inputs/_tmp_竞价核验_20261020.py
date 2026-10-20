# -*- coding: utf-8 -*-
"""早盘竞价快照分析(20261020): 全市场宽度 + 昨日预判逐标的兑现对照"""
import gzip, json, os
import pandas as pd

ARC = r"D:\股票数据\市场数据\_学习\竞价快照存档"
d = "20261020"
df = pd.read_csv(gzip.open(os.path.join(ARC, d + ".csv.gz"), "rt", encoding="utf-8"), dtype={"代码": str})
df["代码"] = df["代码"].str.zfill(6)
for c in ("今开", "昨收", "最新价", "成交额", "高开幅度"):
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["高开幅度", "成交额"])

n = len(df)
print("=== 全市场宽度(%s) 条数=%d ===" % (d, n))
print("高开中位 %.2f%%  均值 %.2f%%" % (df["高开幅度"].median(), df["高开幅度"].mean()))
low = int((df["高开幅度"] < 0).sum())
lowin = int((df["高开幅度"] <= 0).sum())
print("低开<0: %d (%.1f%%)   低开≤0: %d (%.1f%%)" % (low, low * 100.0 / n, lowin, lowin * 100.0 / n))
for th in (0.1, 1, 2, 3, 5, 7, 9):
    k = int((df["高开幅度"] >= th).sum())
    print("  高开≥%.0f%%: %d (%.2f%%)" % (th, k, k * 100.0 / n))
print("竞价额合计 %.1f亿" % (df["成交额"].sum() / 1e8))

# 一字(开盘即涨停): 主板>=9.9 创业/科创(30/68)>=19.9 北交所(8/4)>=29.9
def lim(c):
    if c.startswith(("300", "301", "688", "689")):
        return 19.9
    if c.startswith(("8", "4", "92")):
        return 29.9
    return 9.9
df["limitpct"] = df["代码"].map(lim)
df["一字"] = df["高开幅度"] >= df["limitpct"] - 0.15
yizi = df[df["一字"]].sort_values("成交额", ascending=False)
print("\n一字板(开盘涨停)家数=%d" % len(yizi))
print(yizi[["代码", "名称", "高开幅度", "成交额", "竞价额排名"]].head(20).to_string(index=False))

print("\n=== 竞价额Top15 ===")
top = df.nlargest(15, "成交额")
print(top[["代码", "名称", "高开幅度", "成交额", "竞价额排名"]].to_string(index=False))

# 逐标的对照
watch = {
    "002889": "东方嘉盛", "003029": "吉大正元", "603278": "大业股份", "603197": "保隆科技",
    "002626": "金达威", "600487": "亨通光电", "000576": "甘化科工", "600267": "海正药业",
    "002085": "万丰奥威", "002929": "润建股份",
    "600668": "尖峰集团", "000601": "韶能股份", "000823": "超声电子",
    "600693": "东百集团", "603968": "醋化股份", "000530": "冰山冷热",
}
print("\n=== 逐标的今晨竞价 ===")
for code, nm in watch.items():
    r = df[df["代码"] == code]
    if len(r) == 0:
        print("%s %s: 快照缺(停牌/未上市?)" % (code, nm))
        continue
    r = r.iloc[0]
    print("%s %-6s gap=%+6.2f%% 今开=%7.2f 昨收=%7.2f 竞价额=%9.0f万 排名=%s"
          % (code, nm, r["高开幅度"], r["今开"], r["昨收"], r["成交额"] / 1e4, r["竞价额排名"]))

# 昨日竞价池整体今晨gap分布
poolf = r"D:\股票数据\市场数据\_学习\竞价池发出_20261019.json"
if os.path.isfile(poolf):
    p = json.load(open(poolf, encoding="utf-8"))
    def codes(o):
        out = []
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("代码", "code") and isinstance(v, str) and v.strip().isdigit():
                    out.append(v.strip()[:6])
                else:
                    out += codes(v)
        elif isinstance(o, list):
            for v in o:
                out += codes(v)
        return out
    pc = sorted(set(codes(p)))
    print("\n=== 昨日竞价池(%d只) 今晨gap ===" % len(pc))
    rows = []
    for c in pc:
        r = df[df["代码"] == c]
        if len(r):
            r = r.iloc[0]
            rows.append((c, r["名称"], r["高开幅度"], r["成交额"] / 1e4))
        else:
            rows.append((c, "?", None, None))
    for c, nm, g, a in sorted(rows, key=lambda x: (-(x[2] if x[2] is not None else -99))):
        if g is None:
            print("%s %-6s 快照缺" % (c, nm))
        else:
            print("%s %-6s gap=%+6.2f%% 竞价额=%8.0f万" % (c, nm, g, a))
    gs = [r[2] for r in rows if r[2] is not None]
    if gs:
        sr = pd.Series(gs)
        print("池内 n=%d 中位%.2f%% ≥5%%家数=%d 低开≤0家数=%d" % (len(sr), sr.median(), int((sr >= 5).sum()), int((sr <= 0).sum())))
