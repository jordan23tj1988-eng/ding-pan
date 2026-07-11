#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题材四维.py —— 题材宽度/高度/晋级率/宽度环比 日序列 + 缩圈自动警报(P0-3,2026-07-11评估落地)。
数据: _学习/题材归位_{d}.json(题材唯一真源,映射{code:{大方向,...}}) × THS三池(连板数,无ST口径,本地池兜底)。
四维(全部T日收盘可知,零后视镜):
  宽度=该大方向涨停家数; 高度=题材内最高连续板(N天N板);
  题材晋级率=今日题材内2连板/昨日题材内首板; 宽度环比=今日宽度/昨日宽度-1。
缩圈警报: 宽度连续2日下降且累计降幅>30% 且 高度未抬升 -> 【缩圈】;
扩散提示: 宽度环比>+50%且宽度>=10 -> 【放宽】。
口径提醒: 线名以归位json当日命名为准(线名归一在12号agent处理),跨日改名会造成序列断裂,断裂处如实呈现不拼接。
产出: _学习/_题材四维.json {date:{theme:{...}}} + print。用法: python3 题材四维.py [YYYYMMDD|--all]
"""
import os, sys, json, re, glob
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
OUT = os.path.join(L, "_题材四维.json")
PAT = re.compile(r'(\d+)天(\d+)板')

def is_junk(name):
    s = str(name or "")
    return ("ST" in s.upper()) or ("退" in s) or s.startswith("N") or s.startswith("C")

def boards_map(d):
    """{code:(板数,是否连续)}。THS优先,本地zt_pool兜底,都缺返回{}。"""
    p = os.path.join(L, "_ths_zt_pool.json")
    if os.path.isfile(p):
        ths = json.load(open(p, encoding="utf-8"))
        if d in ths:
            out = {}
            for r in ths[d]:
                if is_junk(r.get("name")):
                    continue
                s = str(r.get("high_days") or "")
                m = PAT.search(s)
                n, mm = (int(m.group(1)), int(m.group(2))) if m else (1, 1)
                out[str(r.get("code", "")).zfill(6)] = (mm, n == mm)
            return out
    zp = os.path.join(BASE, d, "zt_pool.csv")
    if os.path.isfile(zp):
        z = pd.read_csv(zp, dtype={"代码": str})
        z = z[~z["名称"].astype(str).map(is_junk)]
        out = {}
        for _, r in z.iterrows():
            try:
                lb = int(float(r.get("连板数", 1)))
            except Exception:
                lb = 1
            st = str(r.get("涨停统计", "") or "")
            m = re.match(r'(\d+)/(\d+)', st)
            n = int(m.group(1)) if m else lb
            out[str(r["代码"]).zfill(6)] = (lb, n == lb)
        return out
    return {}

def theme_day(d):
    """{theme:{宽度,高度,首板,二连板}} for date d;归位文件缺=None。"""
    fp = os.path.join(L, f"题材归位_{d}.json")
    if not os.path.isfile(fp):
        return None
    mp = json.load(open(fp, encoding="utf-8")).get("映射", {})
    bm = boards_map(d)
    th = {}
    for code, v in mp.items():
        theme = str(v.get("大方向") or "未归位")
        b, cons = bm.get(str(code).zfill(6), (1, True))
        e = th.setdefault(theme, {"宽度": 0, "高度": 1, "首板": 0, "二连板": 0})
        e["宽度"] += 1
        if cons:
            e["高度"] = max(e["高度"], b)
            if b == 1:
                e["首板"] += 1
            elif b == 2:
                e["二连板"] += 1
    return th

def alerts(t, d):
    """基于序列出缩圈/放宽警报,只用<=d的数据(零后视镜)。"""
    days = sorted(x for x in t if x <= d)
    if len(days) < 2:
        return []
    cur = t[days[-1]]; prev = t[days[-2]]
    prev2 = t[days[-3]] if len(days) >= 3 else None
    out = []
    for theme, e in cur.items():
        if theme == "未归位":
            continue
        p = prev.get(theme)
        if not p:
            if e["宽度"] >= 10:
                out.append(f"【新线】{theme} 宽度{e['宽度']}·高度{e['高度']}板(序列首日)")
            continue
        chg = e["宽度"] / p["宽度"] - 1 if p["宽度"] else None
        e["宽度环比"] = round(chg, 3) if chg is not None else None
        e["题材晋级率"] = round(e["二连板"] / p["首板"], 3) if p["首板"] else None
        if chg is not None and chg > 0.5 and e["宽度"] >= 10:
            out.append(f"【放宽】{theme} 宽度{p['宽度']}→{e['宽度']}(+{chg*100:.0f}%)")
        if chg is not None and chg < -0.5 and p["宽度"] >= 15:
            out.append(f"【急缩】{theme} 宽度{p['宽度']}→{e['宽度']}({chg*100:.0f}%)单日腰斩——高潮回落/兑现日特征")
        if prev2 is not None:
            p2 = prev2.get(theme)
            if p2 and p2["宽度"] > p["宽度"] > e["宽度"]:
                tot = e["宽度"] / p2["宽度"] - 1
                if tot < -0.3 and e["高度"] <= max(p["高度"], p2["高度"]):
                    out.append(f"【缩圈】{theme} 宽度{p2['宽度']}→{p['宽度']}→{e['宽度']}({tot*100:.0f}%)且高度未抬升——高潮回落段特征,减仓位不是上车位")
    return out

def main():
    t = json.load(open(OUT, encoding="utf-8")) if os.path.isfile(OUT) else {}
    arg = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if arg == "--all":
        days = sorted(os.path.basename(x)[5:-5] for x in glob.glob(os.path.join(L, "题材归位_*.json")))
    else:
        days = [arg]
    for d in days:
        th = theme_day(d)
        if th is None:
            print(f"[跳过] {d} 无题材归位文件")
            continue
        t[d] = th
        al = alerts(t, d)
        t[d]["_警报"] = al
        json.dump(t, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        rows = sorted(((k, v) for k, v in th.items() if k != "_警报"), key=lambda x: -x[1]["宽度"])
        print(f"== {d} 题材四维 ==")
        for k, v in rows[:8]:
            jl = v.get("题材晋级率")
            print(f"  {k:<12} 宽{v['宽度']:>3} 高{v['高度']}板 晋级率{('%.0f%%' % (jl*100)) if jl is not None else 'null'} 环比{('%+.0f%%' % (v['宽度环比']*100)) if v.get('宽度环比') is not None else 'null'}")
        for a in al:
            print("  " + a)

if __name__ == "__main__":
    main()
