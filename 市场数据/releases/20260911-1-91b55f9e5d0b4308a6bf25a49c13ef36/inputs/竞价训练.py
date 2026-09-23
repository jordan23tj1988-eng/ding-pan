# -*- coding: utf-8 -*-
"""竞价训练.py —— 多因子统计"什么情况下(封板时间/连板层/封单/炸板/题材)次日封板概率大"
数据: 历史涨停池(优先读 市场数据\\YYYYMMDD\\zt_pool.csv 缓存,缺则akshare拉并缓存)。
join T→T+1:T日涨停股是否T+1仍涨停(=次日封板/晋级)。全部真实数据,不编。
用法: python 竞价训练.py [天数,默认30]"""
import os, sys, glob, json, datetime
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q"); import akshare as ak
import pandas as pd, numpy as np

def _safe_dump(obj,path):
    import json
    with open(path,"w",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,indent=2,default=str)); f.truncate()

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

def load_pool(d):
    """某日涨停池:先读缓存,缺则拉akshare并缓存到 市场数据\\d\\zt_pool.csv。"""
    cache = os.path.join(BASE, d, "zt_pool.csv")
    if os.path.isfile(cache):
        try:
            df = pd.read_csv(cache, dtype={"代码": str}); df["代码"] = df["代码"].str.zfill(6); return df
        except Exception:
            pass
    try:
        df = ak.stock_zt_pool_em(date=d)
    except Exception:
        return None
    if df is None or len(df) == 0:
        return None
    df["代码"] = df["代码"].astype(str).str.zfill(6)
    os.makedirs(os.path.join(BASE, d), exist_ok=True)
    df.to_csv(cache, index=False, encoding="utf-8-sig")
    return df

def seal_bucket(t):
    t = str(int(t)).zfill(6)
    if t <= "092530": return "竞价一字"
    if t <= "093100": return "秒板(≤9:31)"
    if t <= "103000": return "早盘封"
    if t <= "133000": return "午前"
    return "午后封"

def rate_table(df, by):
    g = df.groupby(by)["次日封板"].agg(["mean", "count"])
    return {str(k): [round(float(v["mean"]), 3), int(v["count"])] for k, v in g.iterrows()}

def main():
    ndays = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    pools = {}; day = datetime.date.today(); back = 0
    while len(pools) < ndays + 1 and back < ndays * 2 + 15:
        d = (day - datetime.timedelta(days=back)).strftime("%Y%m%d"); back += 1
        p = load_pool(d)
        if p is not None:
            pools[d] = p
    dates = sorted(pools.keys())
    # 防脏:盘前eastmoney会把前一日数据挂到今天→若最新日涨停池与前一日完全相同,丢弃(盘前滞后)
    while len(dates) >= 2 and set(pools[dates[-1]]["代码"]) == set(pools[dates[-2]]["代码"]):
        print("丢弃盘前滞后日", dates[-1]); dates.pop()
    if len(dates) < 3:
        print("涨停池历史不足"); return
    print(f"窗口 {dates[0]}~{dates[-1]} 共{len(dates)}日")

    rows = []
    for i in range(len(dates) - 1):
        z = pools[dates[i]]; nxt = set(pools[dates[i + 1]]["代码"])
        for _, r in z.iterrows():
            liu = r.get("流通市值", 0) or 1
            fc = (r.get("封板资金", 0) or 0) / max(liu, 1)
            rows.append(dict(
                封档=seal_bucket(r["首次封板时间"]),
                连板层=("首板" if r["连板数"] == 1 else ("2板" if r["连板数"] == 2 else "3板+")),
                封单强度=("强(封成比>3%)" if fc > 0.03 else ("中(1-3%)" if fc > 0.01 else "弱(<1%)")),
                炸板=("0炸板" if (r.get("炸板次数", 0) or 0) == 0 else "有炸板"),
                行业=r.get("所属行业", ""),
                日=dates[i],
                次日封板=1 if r["代码"] in nxt else 0))
    df = pd.DataFrame(rows)
    # 题材主线:当日该行业涨停≥3只算主线内
    cnt = df.groupby(["日", "行业"]).size().rename("行业涨停数").reset_index()
    df = df.merge(cnt, on=["日", "行业"])
    df["题材"] = np.where(df["行业涨停数"] >= 3, "主线内(行业≥3涨停)", "散票")

    res = {"窗口": f"{dates[0]}~{dates[-1]}", "交易日数": len(dates), "总样本": int(len(df)),
           "基准次日封板率": round(float(df["次日封板"].mean()), 3),
           "按封板时间": rate_table(df, "封档"),
           "按连板层": rate_table(df, "连板层"),
           "按封单强度": rate_table(df, "封单强度"),
           "按炸板": rate_table(df, "炸板"),
           "按题材": rate_table(df, "题材")}
    # 连板层×封板时间 矩阵
    piv = df.pivot_table(index="封档", columns="连板层", values="次日封板", aggfunc="mean")
    cntp = df.pivot_table(index="封档", columns="连板层", values="次日封板", aggfunc="count")
    res["连板层x封板时间"] = {r: {c: [round(float(piv.loc[r, c]), 3), int(cntp.loc[r, c])]
                                  for c in piv.columns if pd.notna(piv.loc[r, c])} for r in piv.index}
    # 黄金组合:多因子分组,样本≥8,按次日封板率排序取前12
    grp = df.groupby(["封档", "连板层", "封单强度", "炸板", "题材"])["次日封板"].agg(["mean", "count"])
    grp = grp[grp["count"] >= 8].sort_values("mean", ascending=False).head(12)
    # 用最新交易日涨停池匹配"今日符合票"(=明日候选),并补 龙头分/席位
    zt_today = pools[dates[-1]].copy().reset_index(drop=True)
    tcnt = zt_today.groupby("所属行业").size()
    tmax = zt_today.groupby("所属行业")["连板数"].max().to_dict()
    tmain = set(tcnt.sort_values(ascending=False).head(3).index)
    tamt = zt_today["成交额"].rank(pct=True)
    def lscore(r):
        tb = max(tmax.get(r["所属行业"], 1), 1)
        sp = 30 * min(r["连板数"] / tb, 1.0)
        fc = (r.get("封板资金", 0) or 0) / max(r.get("流通市值", 1) or 1, 1)
        tt = str(int(r["首次封板时间"])).zfill(6)
        early = 1.0 if tt <= "093000" else (0.6 if tt <= "100000" else 0.3)
        ss = 25 * (min(fc / 0.05, 1.0) * 0.5 + early * 0.35 + (0 if (r.get("炸板次数", 0) or 0) > 0 else 0.15))
        sa = 20 * float(tamt.get(r.name, 0.5))
        st = 15 * ((0.6 if r["所属行业"] in tmain else 0) + (0.4 if r["连板数"] == tmax.get(r["所属行业"], 0) else 0))
        return round(sp + ss + sa + st, 1)
    zt_today["龙头分"] = zt_today.apply(lscore, axis=1)
    # 席位: 读最新日 analysis.json 席位动向 -> 代码 -> 买家
    seatmap = {}
    apath = os.path.join(BASE, dates[-1], "analysis.json")
    if os.path.isfile(apath):
        try:
            aj = json.load(open(apath, encoding="utf-8"))
            for s in aj.get("席位动向", []):
                if s.get("净额", 0) > 0 and (s.get("游资") or s.get("类型") != "其他/未知"):
                    seatmap.setdefault(str(s["代码"]).zfill(6), []).append(str(s.get("游资") or s.get("类型")))
        except Exception:
            pass
    def tag_today(r):
        fc = (r.get("封板资金", 0) or 0) / max(r.get("流通市值", 1) or 1, 1)
        seal = seal_bucket(r["首次封板时间"])
        lvl = "首板" if r["连板数"] == 1 else ("2板" if r["连板数"] == 2 else "3板+")
        strg = "强(封成比>3%)" if fc > 0.03 else ("中(1-3%)" if fc > 0.01 else "弱(<1%)")
        zb = "0炸板" if (r.get("炸板次数", 0) or 0) == 0 else "有炸板"
        thm = "主线内(行业≥3涨停)" if tcnt.get(r["所属行业"], 0) >= 3 else "散票"
        return (seal, lvl, strg, zb, thm)
    today_rows = []
    for _, r in zt_today.iterrows():
        code = str(r["代码"]).zfill(6)
        today_rows.append((tag_today(r), str(r["名称"]), str(r["所属行业"]),
                           float(r["龙头分"]), seatmap.get(code, []), code))
    gold = []
    for k, v in grp.iterrows():
        ms = [(nm, ind, sc, se, cd) for tup, nm, ind, sc, se, cd in today_rows if tup == tuple(k)]
        ms.sort(key=lambda x: -x[2])
        picks = [dict(代码=cd, 名称=nm, 题材=ind, 龙头分=sc, 席位=("/".join(se[:2]) if se else ""))
                 for nm, ind, sc, se, cd in ms[:4]]
        gold.append(dict(条件=" + ".join(k), 次日封板率=round(float(v["mean"]), 3), 样本=int(v["count"]),
                         今日符合票=picks))
    res["黄金组合Top"] = gold
    res["最新交易日"] = dates[-1]
    res["说明"] = "条件=T日特征;百分比=该类票T+1日再封板的历史概率;今日符合票=最新交易日符合该组合的涨停股(=明日封板候选)"
    json.dump(res, open(os.path.join(BASE, "_竞价训练结果.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # 存当日候选快照(供次日晨验证)
    ldir = os.path.join(BASE, "_学习"); os.makedirs(ldir, exist_ok=True)
    snap = {"日期": dates[-1], "候选": []}
    for g in gold:
        for p in g["今日符合票"]:
            snap["候选"].append({**p, "组合": g["条件"], "组合次日封板率": g["次日封板率"]})
    json.dump(snap, open(os.path.join(ldir, "候选_%s.json" % dates[-1]), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("\n基准次日封板率 %.1f%% (总样本%d)" % (res["基准次日封板率"] * 100, res["总样本"]))
    print("\n[按封板时间]"); [print("  %-12s %5.1f%% (n=%d)" % (k, v[0]*100, v[1])) for k, v in res["按封板时间"].items()]
    print("[按连板层]"); [print("  %-6s %5.1f%% (n=%d)" % (k, v[0]*100, v[1])) for k, v in res["按连板层"].items()]
    print("[按封单强度]"); [print("  %-14s %5.1f%% (n=%d)" % (k, v[0]*100, v[1])) for k, v in res["按封单强度"].items()]
    print("[按炸板]"); [print("  %-8s %5.1f%% (n=%d)" % (k, v[0]*100, v[1])) for k, v in res["按炸板"].items()]
    print("[按题材]"); [print("  %-20s %5.1f%% (n=%d)" % (k, v[0]*100, v[1])) for k, v in res["按题材"].items()]
    print("\n[黄金组合Top(样本≥8)]")
    for g in res["黄金组合Top"]:
        print("  %5.1f%% (n=%d)  %s" % (g["次日封板率"]*100, g["样本"], g["条件"]))
    print("\n已存 _竞价训练结果.json")

if __name__ == "__main__":
    main()
