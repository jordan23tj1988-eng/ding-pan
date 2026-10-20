# -*- coding: utf-8 -*-
"""双源对账：快照(09:26:00 sina)今开 vs traj 末帧pct；并算『落闸门概率』= 各信号×连板桶的 T+1高开≥5% 频率（全部结算文件）。"""
import json, csv, gzip, os, glob, statistics as st
os.chdir(r"D:/股票数据/市场数据")
pool = json.load(open("_学习/竞价评分_20261020.json", encoding='utf-8'))['明细']
snap = {}
with gzip.open("_学习/竞价快照存档/20261020.csv.gz", 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        snap[r['代码']] = r
last = {}
for line in open("盘中/20261020/auction_traj.jsonl", encoding='utf-8'):
    o = json.loads(line)
    if o['ts'].split(' ')[1] <= '09:25:59':
        last = {x['code']: x['pct'] for x in o['rows']}
print("=== 双源对账（快照今开% vs traj末帧pct%） ===")
diffs = []
for p in pool:
    c = p['代码']
    if c in last and snap.get(c):
        a = float(snap[c]['高开幅度']); b = last[c]
        diffs.append(abs(a - b))
        print(f"{c} {p['名称']:6s} 快照{a:+7.2f} traj{b:+7.2f} 差{abs(a-b):.2f}pp")
print("对账可比只数", len(diffs), "最大差", max(diffs) if diffs else None,
      "≤0.05pp只数", sum(1 for d in diffs if d <= 0.05))

# 落闸门概率：所有结算文件的明细，按 信号 × 连板 统计 T1高开≥5% 占比
files = sorted(glob.glob("_学习/竞价池结算_[0-9]*.json"))
agg = {}
for fp in files:
    try:
        d = json.load(open(fp, encoding='utf-8'))
    except Exception:
        continue
    for r in d.get('明细', []):
        g = r.get('T1高开')
        if g is None:
            continue
        sig = (r.get('信号') or '').split('·')[0]
        lb = r.get('连板') or 0
        key = (sig, '首板' if lb <= 1 else ('2板' if lb == 2 else '3板+'))
        a = agg.setdefault(key, [0, 0, []])
        a[0] += 1
        a[1] += 1 if g >= 5 else 0
        a[2].append(r.get('执行收益'))
print("\n=== 落闸门概率 P(T+1高开≥5%) 按信号×连板 ===")
for k in sorted(agg, key=lambda x: (x[0], x[1])):
    n, ge5, ex = agg[k]
    e = [x for x in ex if x is not None]
    print(k, {"n": n, "≥5%只": ge5, "P闸门外%": round(100*ge5/n, 1),
              "执1均收%": round(sum(e)/len(e), 2) if e else None})
tot = sum(v[0] for v in agg.values()); ge = sum(v[1] for v in agg.values())
print("全体", {"n": tot, "P闸门外%": round(100*ge/tot, 1)})
json.dump({f"{k[0]}|{k[1]}": {"n": v[0], "ge5": v[1], "P%": round(100*v[1]/v[0], 1)} for k, v in agg.items()},
          open("_tmp/gate_prob.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
