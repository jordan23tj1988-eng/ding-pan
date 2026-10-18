# -*- coding: utf-8 -*-
"""
席位训练.py —— 用历史龙虎榜"营业部上榜后表现"训练"值得跟踪席位库"
================================================================
数据源: akshare stock_lhb_yybph_em(营业部排行,含上榜后1/2/3/5/10天平均涨幅+上涨概率)。
产出: _席位胜率库.json + _席位胜率库.md(分档), 供分析引擎按真实胜率给"席位加成"。
分档(上榜后1天,买入次数≥15): S=胜率≥65%&涨幅≥3% / A=胜率≥55%&涨幅≥1.5% / B=其余 / C=胜率<48%(接近抛硬币,慎跟)
用法: python 席位训练.py
"""
import os, sys, json, glob
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q"); import akshare as ak
import pandas as pd

def _safe_dump(obj,path):
    import json
    with open(path,"w",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,indent=2,default=str)); f.truncate()

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

MI = {"太华路": "开源量化·最凶", "西大街": "开源量化·首板1-2", "成章路": "开源量化·锁仓",
      "紫阳东路": "量化·大长腿地天", "知春路": "量化·派神审美", "永城路": "地天20cm",
      "光复路": "章盟主", "溧阳路": "中信溧阳路系", "上塘路": "欢乐海岸系", "万豪世家": "量化·紫阳系"}

def tier(win, prob, chg, n):
    if n < 15: return "样本不足"
    if prob >= 65 and chg >= 3: return "S"
    if prob >= 55 and chg >= 1.5: return "A"
    if prob < 48: return "C(慎跟)"
    return "B"

def main():
    out = {"训练时间源": "akshare yybph", "档位说明": "S最强/A可跟/B一般/C慎跟(近抛硬币)", "近三月": {}, "近一月": {}}
    md = ["# 值得跟踪席位库（历史上榜后表现训练）\n",
          "> 数据源：akshare 营业部排行(上榜后1天平均涨幅+上涨概率)。档位:S最强/A可跟/B一般/C慎跟。\n",
          "> 用途:分析引擎席位加成按此库胜率加权;复盘席位动向标注该席位靠不靠谱。\n"]
    for win in ("近一月", "近三月"):
        try:
            df = ak.stock_lhb_yybph_em(symbol=win)
        except Exception as e:
            print(win, "拉取失败", str(e)[:50]); continue
        df.to_csv(os.path.join(BASE, f"_席位胜率_{win}.csv"), index=False, encoding="utf-8-sig")
        c_n, c_a, c_p = "上榜后1天-买入次数", "上榜后1天-平均涨幅", "上榜后1天-上涨概率"
        d = df[df[c_n] >= 15].copy()
        d["综合分"] = (d[c_a] * d[c_p] / 100).round(3)
        d["档"] = [tier(win, p, a, n) for p, a, n in zip(d[c_p], d[c_a], d[c_n])]
        # 米氏席位命中
        def mi(n):
            for k in MI:
                if k in str(n): return k
            return ""
        d["米氏"] = d["营业部名称"].map(mi)
        # 存库(dict: 营业部全名→{胜率,涨幅,次数,档,米氏})
        for _, r in d.iterrows():
            a2,p2=float(r["上榜后2天-平均涨幅"]),float(r["上榜后2天-上涨概率"])
            a3,p3=float(r["上榜后3天-平均涨幅"]),float(r["上榜后3天-上涨概率"])
            d21,d31=round(a2-float(r[c_a]),2),round(a3-float(r[c_a]),2)  # 跟随差值(估):T+1买入后还能吃到的部分
            if d21>=1 and p2>=55: gen="跟随友好"
            elif a2<0 or p2<48: gen="只利日内,跟随=接刀"
            elif d21<0: gen="T+1买无肉"
            else: gen="跟随一般"
            out[win][str(r["营业部名称"])] = dict(胜率=round(float(r[c_p]), 1), 涨幅=round(float(r[c_a]), 2),
                                               次数=int(r[c_n]), 档=r["档"], 米氏=r["米氏"],
                                               涨幅2日=round(a2,2), 胜率2日=round(p2,1),
                                               涨幅3日=round(a3,2), 胜率3日=round(p3,1),
                                               跟随差值2日=d21, 跟随差值3日=d31, 跟随评价=gen)
        # md: 米氏席位表现 + S/A档榜
        md.append(f"\n## {win}\n\n> ★跟随口径:榜单T日盘后公布,实操最早T+1买/T+2卖→\"1日\"仅观察,\"2日/3日\"才是可吃区间。\n\n### 米氏手册席位·实测表现\n| 席位 | 全名 | 1日(观察) | 2日 | 3日 | 次数 | 档 |\n|---|---|---|---|---|---|---|")
        mih = d[d["米氏"] != ""].sort_values("综合分", ascending=False)
        for _, r in mih.iterrows():
            md.append(f"| {r['米氏']}({MI[r['米氏']]}) | {r['营业部名称']} | {r[c_a]:+.2f}%/{r[c_p]:.0f}% | {r['上榜后2天-平均涨幅']:+.2f}%/{r['上榜后2天-上涨概率']:.0f}% | {r['上榜后3天-平均涨幅']:+.2f}%/{r['上榜后3天-上涨概率']:.0f}% | {int(r[c_n])} | **{r['档']}** |")
        md.append(f"\n### 经验最强席位 S/A档 Top20（数据发现）\n| 营业部 | 1日(观察) | 2日 | 3日 | 次数 | 档 |\n|---|---|---|---|---|---|")
        for _, r in d[d["档"].isin(["S", "A"])].sort_values("综合分", ascending=False).head(20).iterrows():
            md.append(f"| {r['营业部名称']} | {r[c_a]:+.2f}%/{r[c_p]:.0f}% | {r['上榜后2天-平均涨幅']:+.2f}%/{r['上榜后2天-上涨概率']:.0f}% | {r['上榜后3天-平均涨幅']:+.2f}%/{r['上榜后3天-上涨概率']:.0f}% | {int(r[c_n])} | {r['档']} |")
    _safe_dump(out, os.path.join(BASE, "_席位胜率库.json"))
    f_md=open(os.path.join(BASE, "_席位胜率库.md"), "w", encoding="utf-8"); f_md.write("\n".join(md)); f_md.truncate(); f_md.close()

    # 追加每日快照(供盯盘台追踪胜率变化,只加不删)
    try:
        import datetime as _dt
        _snap=dict(快照日=_dt.date.today().strftime("%Y%m%d"))
        _snap["data"]=out
        open(os.path.join(BASE,"_学习","席位胜率快照.jsonl"),"a",encoding="utf-8").write(json.dumps(_snap,ensure_ascii=False,default=str)+"\n")
    except Exception as _e: print("快照失败",_e)
    print("完成: _席位胜率库.json / _席位胜率库.md / _席位胜率_近一月,近三月.csv")
    print(f"近三月收录 {len(out['近三月'])} 席位, 近一月 {len(out['近一月'])} 席位")

if __name__ == "__main__":
    main()
