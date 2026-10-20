# -*- coding: utf-8 -*-
"""临时分析：MA-20261019-01 末段位移Δgap 多日分档 + 今日快照/池结构。只读，不改生产文件。"""
import json, csv, gzip, os, glob, statistics as st

ROOT = r"D:/股票数据/市场数据"
os.chdir(ROOT)

def read_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def traj_frames(d):
    p = f"盘中/{d}/auction_traj.jsonl"
    if not os.path.exists(p):
        return None
    out = []
    with open(p, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def dgap_for(d):
    """返回 {code: (pct0920, pct0925, dgap)}，口径=最后一个ts<=09:25:59帧 减 第一个ts>=09:20:00帧"""
    fr = traj_frames(d)
    if not fr:
        return None, "no_file"
    def hm(ts):
        return ts.split(' ')[1]
    pre = [o for o in fr if '09:20:00' <= hm(o['ts']) <= '09:25:59']
    if len(pre) < 2:
        return None, f"frames_in_window={len(pre)}"
    a, b = pre[0], pre[-1]
    A = {r['code']: r['pct'] for r in a['rows']}
    B = {r['code']: r['pct'] for r in b['rows']}
    res = {}
    for c in set(A) & set(B):
        res[c] = (A[c], B[c], round(B[c] - A[c], 2))
    return (res, a['ts'], b['ts'], len(pre)), None

# ---- 1. 多日 Δgap 分档 vs 执1 ----
TRAJ_DAYS = ["20260911", "20260923", "20260924", "20260929", "20260930",
             "20261009", "20261012", "20261013", "20261014", "20261015",
             "20261016", "20261019", "20261020"]
# traj_T 覆盖 zt_pool_{P}，P=前一交易日
PREV = {"20260911": "20260910", "20260923": "20260922", "20260924": "20260923",
        "20260929": "20260928", "20260930": "20260929", "20261009": "20260930",
        "20261012": "20261009", "20261013": "20261012", "20261014": "20261013",
        "20261015": "20261014", "20261016": "20261015", "20261019": "20261016",
        "20261020": "20261019"}

rows = []
day_log = []
for T in TRAJ_DAYS:
    P = PREV[T]
    sp = f"_学习/竞价池结算_{P}.json"
    g, err = dgap_for(T)
    if g is None:
        day_log.append({"traj日": T, "池日": P, "可用": False, "原因": err})
        continue
    res, ts0, ts1, nfr = g
    if not os.path.exists(sp):
        day_log.append({"traj日": T, "池日": P, "可用": False, "原因": "结算缺件", "帧": nfr})
        continue
    stl = read_json(sp)
    det = stl.get('明细', [])
    used = 0
    noexec = 0
    for r in det:
        c = r.get('代码')
        ex = r.get('执行收益')
        if c in res and ex is not None:
            rows.append({"traj": T, "pool_day": P, "代码": c, "名称": r.get('名称'),
                         "pct0920": res[c][0], "pct0925": res[c][1], "dgap": res[c][2],
                         "执1": ex, "T1高开": r.get('T1高开'), "封板": r.get('次日封板'),
                         "信号": r.get('信号'), "连板": r.get('连板')})
            used += 1
        elif c in res and ex is None:
            noexec += 1
    day_log.append({"traj日": T, "池日": P, "可用": True, "帧": nfr, "首帧": ts0, "末帧": ts1,
                    "池": len(det), "可算": used, "执1缺失": noexec})

def bucket(v):
    if v < -5:
        return "A_<-5pp"
    if v < 0:
        return "B_-5~0pp"
    return "C_>=0pp"

by = {}
for r in rows:
    by.setdefault(bucket(r['dgap']), []).append(r)

print("=== 逐日可用性 ===")
for d in day_log:
    print(d)
print("\n=== 总样本 n=%d ===" % len(rows))
summary = {}
for k in ["A_<-5pp", "B_-5~0pp", "C_>=0pp"]:
    v = by.get(k, [])
    if not v:
        print(k, "n=0")
        summary[k] = {"n": 0}
        continue
    n = len(v)
    win = sum(1 for x in v if x['执1'] > 0)
    mean = round(sum(x['执1'] for x in v) / n, 2)
    days = {}
    for x in v:
        days.setdefault(x['pool_day'], []).append(x['执1'])
    posdays = sum(1 for _, vv in days.items() if sum(vv) / len(vv) > 0)
    summary[k] = {"n": n, "胜率": round(100 * win / n, 1), "均收": mean,
                  "正日数": f"{posdays}/{len(days)}", "均收中位": round(st.median([x['执1'] for x in v]), 2),
                  "涉及池日": sorted(days.keys())}
    print(k, summary[k])

# 相关性（简单）
try:
    xs = [x['dgap'] for x in rows]; ys = [x['执1'] for x in rows]
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    cov = sum((a-mx)*(b-my) for a, b in zip(xs, ys))
    sx = sum((a-mx)**2 for a in xs) ** .5; sy = sum((b-my)**2 for b in ys) ** .5
    print("\nPearson r =", round(cov/(sx*sy), 3), "n=", len(rows))
except Exception as e:
    print("corr err", e)

# 今日池(20261019)用 traj_20261020 的 Δgap 逐票
print("\n=== 20261019池 用 20261020 traj 的Δgap 逐票（今日执行） ===")
for r in sorted([x for x in rows if x['pool_day'] == "20261019"], key=lambda z: z['dgap']):
    print(f"{r['代码']} {r['名称']} 09:20 {r['pct0920']:+.2f} → 09:25 {r['pct0925']:+.2f} Δ{r['dgap']:+.2f}pp 执1 {r['执1']:+.2f}% T1高开 {r['T1高开']}")

json.dump({"n": len(rows), "summary": summary, "day_log": day_log,
           "rows": rows}, open("_tmp/dgap_analysis.json", "w", encoding='utf-8'),
          ensure_ascii=False, indent=1)
