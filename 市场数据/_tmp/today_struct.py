# -*- coding: utf-8 -*-
import json, csv, gzip, os, statistics as st
os.chdir(r"D:/股票数据/市场数据")
d = json.load(open("_tmp/dgap_analysis.json", encoding='utf-8'))
rows = d['rows']

# 剔除『09:25已在涨停价』(一字/封死，买不进→执1恒0)后的纯位移检验
def is_sealed(r):
    return r['pct0925'] >= 9.8

free = [r for r in rows if not is_sealed(r)]
sealed = [r for r in rows if is_sealed(r)]
def bucket(v):
    return "A_<-5" if v < -5 else ("B_-5~0" if v < 0 else "C_>=0")
print("=== 剔除09:25封死(买不进) n=%d，封死组 n=%d ===" % (len(free), len(sealed)))
for k in ["A_<-5", "B_-5~0", "C_>=0"]:
    v = [r for r in free if bucket(r['dgap']) == k]
    if not v:
        print(k, "n=0"); continue
    n = len(v); win = sum(1 for x in v if x['执1'] > 0)
    print(k, {"n": n, "胜率%": round(100*win/n,1), "均收%": round(sum(x['执1'] for x in v)/n,2),
              "中位%": round(st.median([x['执1'] for x in v]),2)})
n = len(free); win = sum(1 for x in free if x['执1'] > 0)
print("自由可买组全体", {"n": n, "胜率%": round(100*win/n,1), "均收%": round(sum(x['执1'] for x in free)/n,2)})
n = len(sealed); win = sum(1 for x in sealed if x['执1'] > 0)
print("封死组全体", {"n": n, "胜率%": round(100*win/n,1), "均收%": round(sum(x['执1'] for x in sealed)/n,2)})

# ---- 今日(20261020)快照结构 ----
snap = []
with gzip.open("_学习/竞价快照存档/20261020.csv.gz", 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        try:
            r['高开幅度'] = float(r['高开幅度']); r['成交额'] = float(r['成交额'])
            r['竞价额排名'] = int(r['竞价额排名'])
        except Exception:
            continue
        snap.append(r)
print("\n=== 20261020 快照 n=%d ===" % len(snap))
gaps = [r['高开幅度'] for r in snap]
def gb(g):
    return "低开≤0" if g <= 0 else ("高开0~5" if g < 5 else "高开≥5")
cnt = {}
for g in gaps:
    cnt[gb(g)] = cnt.get(gb(g), 0) + 1
print("全市场高开档分布", {k: (v, round(100*v/len(snap),1)) for k, v in cnt.items()},
      "中位", round(st.median(gaps),2))

pool = json.load(open("_学习/竞价评分_20261020.json", encoding='utf-8'))['明细']
by_code = {r['代码']: r for r in snap}
print("\n=== 今日池15只（快照09:26:00 A档） ===")
pool_gap = {}
for p in pool:
    s = by_code.get(p['代码'])
    g = s['高开幅度'] if s else None
    rk = s['竞价额排名'] if s else None
    amt = round(s['成交额']/1e8, 3) if s else None
    pool_gap[p['代码']] = (g, rk, amt)
    print(f"{p['代码']} {p['名称']:6s} 信号{p['信号']:8s} 封单比{p['封单比']:5.2f} 炸{p['炸板']:2d} 分{p['竞价分']:5.1f} 今开%{g if g is None else round(g,2):>7} 竞价额亿{amt} 排名{rk}")
pv = [v[0] for v in pool_gap.values() if v[0] is not None]
c2 = {}
for g in pv:
    c2[gb(g)] = c2.get(gb(g), 0) + 1
print("池高开档", c2, "池中位", round(st.median(pv), 2) if pv else None,
      "池竞价额合计亿", round(sum(v[2] for v in pool_gap.values() if v[2]), 3),
      "池均分", round(sum(p['竞价分'] for p in pool)/len(pool), 2))
allamt = sum(r['成交额'] for r in snap) / 1e8
print("全市场竞价额合计亿", round(allamt, 1), "池占全市场%", round(100*sum(v[2] for v in pool_gap.values() if v[2])/allamt, 2))
print("池内可买(高开<5)只数", sum(1 for g in pv if g < 5), "/", len(pv))

# 今日池 ∩ traj_20261020（昨日池监控清单）
codes = set()
for line in open("盘中/20261020/auction_traj.jsonl", encoding='utf-8'):
    for r in json.loads(line)['rows']:
        codes.add(r['code'])
inter = [p['代码'] for p in pool if p['代码'] in codes]
print("\n今日池∩今日轨迹", len(inter), "/", len(pool), inter)
json.dump({"free": free and None, "pool_gap": {k: list(v) for k, v in pool_gap.items()},
           "snapshot": {"n": len(snap), "档分布": cnt, "中位": round(st.median(gaps),2),
                        "池中位": round(st.median(pv),2), "池档": c2}},
          open("_tmp/today_struct.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
