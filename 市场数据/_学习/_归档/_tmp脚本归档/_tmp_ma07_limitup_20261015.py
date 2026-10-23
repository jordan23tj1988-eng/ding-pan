# -*- coding: utf-8 -*-
"""MA-20261014-07 承接回测（limitup路）：
 A. 冰点档(温度<25) × 换手率/开板次数/首封时间 分桶，n>=5 检验，判定是否需专用闸门。
 B. 一字/秒板 → 次日(T+1)追不进率，并给出计入该率后的池均执1口径。
数据源：_涨停质量库.json 同源样本（涨停质量训练.py._factor_table + _enrich，K线取 _bars_cache 本地缓存，零网络、零后视镜）。
输出：_学习/_ma07_limitup_20261015.json
"""
import importlib.util, os, json, math
import numpy as np, pandas as pd

BASE = r"D:\股票数据\市场数据"
L = os.path.join(BASE, "_学习")
spec = importlib.util.spec_from_file_location("zqzl", os.path.join(BASE, "涨停质量训练.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

P = m._factor_table()
D = m._enrich(P, forward=True)

# ---- 追加：T+1 开盘跳空 + 次日一字判定（追不进口径） ----
gap1, oneword1, openup_limit = [], [], []
cache = {}
for _, r in D.iterrows():
    c = r["代码"]
    if c not in cache:
        cache[c] = m._bars(c)
    b = cache[c]; g = np.nan; ow = np.nan; lim = np.nan
    if b is not None:
        idx = b.index[b["date"] == r["日"]]
        if len(idx):
            i = idx[0]; Tc = b.loc[i, "close"]
            if i + 1 < len(b) and Tc and Tc > 0:
                o1 = b.loc[i + 1, "open"]; h1 = b.loc[i + 1, "high"]; l1 = b.loc[i + 1, "low"]; c1 = b.loc[i + 1, "close"]
                g = o1 / Tc - 1
                lim_ = 0.198 if str(c).startswith(("30", "68")) else (0.098)
                lim = 1.0 if (g >= lim_ - 0.002 and abs(h1 - l1) < 1e-9) else 0.0
                # 追不进=开盘即涨停(价>=涨停价附近)且全天一字；或开盘涨幅>=limit-0.2pp
                ow = 1.0 if (g >= lim_ - 0.002) else 0.0
    gap1.append(g); oneword1.append(lim); openup_limit.append(ow)
D["gap1"] = gap1; D["追不进"] = oneword1; D["开盘即板"] = openup_limit

S = D[D["E1"].notna()].copy()
S["换手桶"] = pd.cut(S["换手"], [-1, 3, 10, 20, 1e9], labels=["<3%", "3-10%", "10-20%", "≥20%"])
S["开板桶"] = np.where(S["开板"] >= 2, "开2次+", np.where(S["开板"] == 1, "开1次", "未开板"))
ff = S["首封"].fillna("")
S["首封桶"] = np.where(ff <= "09:25", "一字≤9:25",
                    np.where(ff <= "09:31", "秒板≤9:31",
                             np.where(ff <= "10:00", "早盘≤10:00",
                                      np.where(ff <= "14:00", "盘中10-14", "尾盘>14"))))
S["冰点"] = pd.to_numeric(S["温度"], errors="coerce") < 25

def agg(df):
    n = len(df)
    if n == 0: return None
    return dict(n=int(n),
                执1胜率=round(float((df["E1"] > 0).mean()) * 100, 1),
                执1均涨=round(float(df["E1"].mean()) * 100, 2),
                执2胜率=round(float((df["E2"] > 0).mean()) * 100, 1) if df["E2"].notna().any() else None,
                执2均涨=round(float(df["E2"].mean()) * 100, 2) if df["E2"].notna().any() else None)

out = {"口径": "执1=T+1开盘买入→T+1收盘;执2=T+1开→T+2收;样本=质量库同源(涨停质量训练._factor_table+_enrich),零后视镜",
       "全样本": agg(S), "冰点样本": agg(S[S["冰点"]])}

# A. 冰点档 × 各因子桶
A = {}
for f in ["换手桶", "开板桶", "首封桶"]:
    A[f] = {}
    for k, g in S[S["冰点"]].groupby(f, observed=True):
        a = agg(g)
        if a: A[f][str(k)] = a
    A[f]["_全样本对照"] = {str(k): agg(g) for k, g in S.groupby(f, observed=True)}
out["A_冰点档分桶"] = A

# 冰点 × 换手 × 开板 二维（n>=5 才保留）
two = {}
for (t, ob), g in S[S["冰点"]].groupby(["换手桶", "开板桶"], observed=True):
    a = agg(g)
    if a and a["n"] >= 5: two[f"{t}×{ob}"] = a
    elif a: two[f"{t}×{ob}"] = dict(a, 标注="n<5仅观察")
out["A2_冰点_换手x开板"] = two

# A2b 冰点专用闸门候选组合（n>=5）
ice = S[S["冰点"]]
gates = {
 "G1_开板≥2次": ice[ice["开板桶"] == "开2次+"],
 "G2_开1次": ice[ice["开板桶"] == "开1次"],
 "G3_换手<3%": ice[ice["换手桶"] == "<3%"],
 "G4_开板≥2次&换手≥3%": ice[(ice["开板桶"] == "开2次+") & (ice["换手"] >= 3)],
 "G5_开板≥2次&换手≥10%": ice[(ice["开板桶"] == "开2次+") & (ice["换手"] >= 10)],
 "G6_开1次&换手≥3%": ice[(ice["开板桶"] == "开1次") & (ice["换手"] >= 3)],
 "G7_未开板&换手<3%": ice[(ice["开板桶"] == "未开板") & (ice["换手"] < 3)],
 "G8_一字≤9:25": ice[ice["首封桶"] == "一字≤9:25"],
 "G9_开板≥2次&换手≥3%&非一字秒板": ice[(ice["开板桶"] == "开2次+") & (ice["换手"] >= 3) & (~ice["首封桶"].isin(["一字≤9:25", "秒板≤9:31"]))],
 "G10_全冰点": ice,
 "G11_开板≥2&换手≥3&首封≤09:31": ice[(ice["开板桶"] == "开2次+") & (ice["换手"] >= 3) & (ice["首封桶"].isin(["一字≤9:25", "秒板≤9:31"]))],
 "G12_开板≥2&换手≥3&盘中10-14": ice[(ice["开板桶"] == "开2次+") & (ice["换手"] >= 3) & (ice["首封桶"] == "盘中10-14")],
}
# 近30个交易日（库窗口末尾）冰点档
days = sorted(S["日"].unique())[-30:]
recent = S[S["日"].isin(days)]
out["A2c_近30交易日"] = {"窗口": [str(days[0]), str(days[-1])], "全档": agg(recent),
                    "冰点": agg(recent[recent["冰点"]]),
                    "冰点G4": agg(recent[(recent["冰点"]) & (recent["开板"] >= 2) & (recent["换手"] >= 3)])}
out["A2b_冰点闸门候选"] = {k: agg(v) for k, v in gates.items()}
# 非冰点同口径对照
nonic = S[~S["冰点"]]
out["A2b_非冰点同口径对照"] = {
 "开板≥2次&换手≥3%": agg(nonic[(nonic["开板桶"] == "开2次+") & (nonic["换手"] >= 3)]),
 "开1次": agg(nonic[nonic["开板桶"] == "开1次"]),
 "换手<3%": agg(nonic[nonic["换手桶"] == "<3%"])}

# 非冰点对照（同二维）
two2 = {}
for (t, ob), g in S[~S["冰点"]].groupby(["换手桶", "开板桶"], observed=True):
    a = agg(g)
    if a: two2[f"{t}×{ob}"] = a
out["A3_非冰点_换手x开板"] = two2

# B. 一字/秒板 → 次日追不进率
B = {}
for k, g in S.groupby("首封桶", observed=True):
    gg = g[g["gap1"].notna()]
    if not len(gg): continue
    B[str(k)] = dict(n=int(len(gg)),
                     次日开盘即板率=round(float((gg["开盘即板"] == 1).mean()) * 100, 1),
                     次日一字率=round(float((gg["追不进"] == 1).mean()) * 100, 1),
                     次日开盘均跳空=round(float(gg["gap1"].mean()) * 100, 2),
                     次日开盘跳空中位=round(float(gg["gap1"].median()) * 100, 2),
                     执1均涨_全含=round(float(gg["E1"].mean()) * 100, 2),
                     可成交子集n=int((gg["追不进"] == 0).sum()),
                     执1均涨_剔追不进=round(float(gg[gg["追不进"] == 0]["E1"].mean()) * 100, 2))
out["B_追不进率"] = B

# 池均口径：今日36只预测执1均涨 与 扣除追不进率后
rec = json.load(open(os.path.join(L, "涨停质量荐票_20261015.json"), encoding="utf-8"))
det = rec["明细"]
pu = [x["预测执1均涨"] for x in det]
out["C_今日池均"] = {
    "池均执1均涨": round(float(np.mean(pu)), 4),
    "池均执1胜率": round(float(np.mean([x["预测执1胜率"] for x in det])), 2),
    "n": len(det),
    "正值": int(sum(1 for v in pu if v > 0)),
    "同池一字/秒板只数": int(sum(1 for x in det if x["首封"] <= "09:31")),
    "同池一字/秒板占比": round(float(sum(1 for x in det if x["首封"] <= "09:31")) / len(det) * 100, 1),
}
# 历史：一字/秒板样本占比 与 扣减后全库池均
soleil = S[S["首封桶"].isin(["一字≤9:25", "秒板≤9:31"])]
out["C_今日池均"].update({
    "历史一字秒板占比": round(len(soleil) / len(S) * 100, 1),
    "历史一字秒板_追不进率": round(float((soleil["追不进"] == 1).mean()) * 100, 1),
    "历史一字秒板_执1均涨_全含": round(float(soleil["E1"].mean()) * 100, 2),
    "历史一字秒板_执1均涨_剔追不进": round(float(soleil[soleil["追不进"] == 0]["E1"].mean()) * 100, 2),
    "全库执1均涨_全含": round(float(S["E1"].mean()) * 100, 2),
})

json.dump(out, open(os.path.join(L, "_ma07_limitup_20261015.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- D. 冰点 vs 非冰点：结构占比（解释冰点档池均偏负的成因） ----
ice2 = S[S["冰点"]]; non2 = S[~S["冰点"]]
def share(df):
    n = len(df)
    if not n: return None
    return dict(n=int(n),
                一字秒板占比=round(float(df["首封桶"].isin(["一字≤9:25", "秒板≤9:31"]).mean()) * 100, 1),
                一字占比=round(float((df["首封桶"] == "一字≤9:25").mean()) * 100, 1),
                换手lt3占比=round(float((df["换手"] < 3).mean()) * 100, 1),
                开板2plus占比=round(float((df["开板"] >= 2).mean()) * 100, 1),
                次日追不进率=round(float((df["追不进"] == 1).mean()) * 100, 1),
                执1均涨=round(float(df["E1"].mean()) * 100, 2))
out["D_结构占比对照"] = {"冰点": share(ice2), "非冰点": share(non2), "全库": share(S)}

# ---- E. 追不进率是否应进入池均期望：全库/冰点 的可成交子集口径 ----
def adj(df):
    n = len(df); fill = df[df["追不进"] == 0]
    return dict(n=int(n), 可成交n=int(len(fill)),
                追不进率=round(float(n and (df["追不进"] == 1).mean()) * 100, 1),
                执1均涨_全含=round(float(df["E1"].mean()) * 100, 3),
                执1均涨_可成交=round(float(fill["E1"].mean()) * 100, 3),
                执1胜率_全含=round(float((df["E1"] > 0).mean()) * 100, 1),
                执1胜率_可成交=round(float((fill["E1"] > 0).mean()) * 100, 1))
out["E_追不进口径修正"] = {"全库": adj(S), "冰点": adj(ice2), "非冰点": adj(non2),
                        "冰点G4闸门": adj(ice2[(ice2["开板"] >= 2) & (ice2["换手"] >= 3)])}
json.dump(out, open(os.path.join(L, "_ma07_limitup_20261015.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("【D】", out["D_结构占比对照"])
for k, v in out["E_追不进口径修正"].items(): print("【E】", k, v)

print("OK", len(S), len(S[S["冰点"]]))

# 控制台摘要
print("全样本", out["全样本"]); print("冰点", out["冰点样本"])
for f in A:
    print("==", f)
    for k, v in A[f].items():
        if k == "_全样本对照": continue
        print("  ", k, v)
print("二维冰点"); [print("  ", k, v) for k, v in two.items()]
print("追不进"); [print("  ", k, v) for k, v in B.items()]
print("池均", out["C_今日池均"])
