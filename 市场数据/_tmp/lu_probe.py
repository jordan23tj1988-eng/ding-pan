# -*- coding: utf-8 -*-
import json, csv, os, statistics as st

B = "D:/股票数据/市场数据"
D = "20261020"

def rows(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

zt = rows(f"{B}/{D}/zt_pool.csv")
zb = rows(f"{B}/{D}/zb_pool.csv")
dt = rows(f"{B}/{D}/dt_pool.csv")
print("counts zt/zb/dt:", len(zt), len(zb), len(dt))

ladder = {}
for r in zt:
    n = int(float(r['连板数']))
    ladder.setdefault(n, []).append((r['代码'], r['名称'], r['首次封板时间'], r['炸板次数'], r['换手率'], r['封板资金']))
print("LADDER", {k: len(v) for k, v in sorted(ladder.items(), reverse=True)})
for k in sorted(ladder, reverse=True):
    print(" ", k, [x[0]+x[1] for x in ladder[k]])

# 炸板率
print("炸板率 %.4f" % (len(zb)/(len(zt)+len(zb))))
# 早封占比 / 开板占比
early = sum(1 for r in zt if r['首次封板时间'] <= '100000')
seal0 = sum(1 for r in zt if int(float(r['炸板次数'])) == 0)
print("早封<=10:00 %d/%d=%.3f ; 未开板 %d=%.3f" % (early, len(zt), early/len(zt), seal0, seal0/len(zt)))
print("炸板次数>=2 家数:", sum(1 for r in zt if int(float(r['炸板次数'])) >= 2))
print("封板资金max亿: %.2f" % (max(float(r['封板资金']) for r in zt)/1e8))
print("封单>=4亿家数:", sum(1 for r in zt if float(r['封板资金']) >= 4e8))
# 跌停
print("跌停:", [(r.get('代码'), r.get('名称')) for r in dt])
print("跌停表头:", list(dt[0].keys()) if dt else None)
# 炸板池平均涨幅
print("炸板表头:", list(zb[0].keys()))
try:
    pm = [float(r['涨跌幅']) for r in zb]
    print("炸板池均涨 %.2f 翻绿 %d" % (st.mean(pm), sum(1 for x in pm if x < 0)))
except Exception as e:
    print("zb no pct", e)

# 质量荐票全池
q = json.load(open(f"{B}/_学习/涨停质量荐票_20261020.json", encoding='utf-8'))
det = q['明细']
def agg(sub, label):
    if not sub:
        print(label, "n=0"); return
    w = [x['预测执1胜率'] for x in sub]
    m = [x['预测执1均涨'] for x in sub]
    print("%s n=%d 执1胜率均%.2f%% 执1均涨%.3f%% 正均涨%d只 max胜率%.1f%%" % (
        label, len(sub), st.mean(w), st.mean(m), sum(1 for x in m if x > 0), max(w)))
agg(det, "全池")
agg([x for x in det if x['连板'] == 1], "首板")
agg([x for x in det if x['连板'] >= 2], "连板")
for k in (2, 3, 4):
    agg([x for x in det if x['连板'] == k], f"{k}板")
print("质量分分布:", sorted(set(x['质量分'] for x in det)))
print("质量分>=7只数:", sum(1 for x in det if x['质量分'] >= 7))
print("命中规则>=1只数:", sum(1 for x in det if x['命中数'] >= 1))
print("TOP8 by 抓龙率:")
for x in sorted(det, key=lambda y: (-y['命中数'], -y['抓龙率']))[:8]:
    print("  %s %s 板%d 抓龙%.1f 分%d 命中%d 执1胜%.1f 均涨%.2f 换手%.2f 封单比%.2f 首封%s" % (
        x['代码'], x['名称'], x['连板'], x['抓龙率'], x['质量分'], x['命中数'],
        x['预测执1胜率'], x['预测执1均涨'], x['换手'], x['封单比'], x['首封']))
print("TOP8 by 质量分/执1:")
for x in sorted(det, key=lambda y: -y['预测执1胜率'])[:8]:
    print("  %s %s 板%d 抓龙%.1f 分%d 命中%d 执1胜%.1f 均涨%.2f" % (
        x['代码'], x['名称'], x['连板'], x['抓龙率'], x['质量分'], x['命中数'], x['预测执1胜率'], x['预测执1均涨']))
