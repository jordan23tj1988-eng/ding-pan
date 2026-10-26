# -*- coding: utf-8 -*-
"""孵化区超期项机械结算探针(20261023) —— 只用留档数据, 不新增判断。"""
import json, os, glob, statistics

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(BASE, '_学习')
out = {}

# --- A. limitup-弱票池荐票门槛: 弱票日样本统计 ---
files = sorted(glob.glob(os.path.join(L, '质量荐票结算_*.json')))
rows = []
for f in files:
    d = os.path.basename(f).split('_')[-1].replace('.json', '')
    try:
        x = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    top = x.get('Top5') or []
    s = x.get('汇总') or {}
    hits = sum(int(t.get('命中数') or 0) for t in top)
    # Top1 抓龙率: 取 Top1 是否次日封板/次日涨停(用明细字段 次日封板 或 执行收益>=9.8 近似不做)
    top1 = top[0] if top else {}
    gain = s.get('选股增益pp')
    rows.append(dict(日=d, n=len(top), 命中合计=hits, 增益=gain,
                     top1=top1.get('代码'), top1名=top1.get('名称'),
                     top1预测胜率=top1.get('预测执1胜率'), top1执行=top1.get('执行收益')))
weak = [r for r in rows if r['n'] == 5 and r['命中合计'] <= 1]
gains = [r['增益'] for r in weak if isinstance(r['增益'], (int, float))]
out['A_弱票池'] = {'总票日': len(rows), '弱票日数(命中合计≤1且发满5只)': len(weak),
                 '增益样本': len(gains),
                 '增益中位pct': round(statistics.median(gains), 2) if gains else None,
                 '增益均值pct': round(sum(gains) / len(gains), 2) if gains else None,
                 '增益为正天数': sum(1 for g in gains if g > 0),
                 '明细': weak}
# 全部票日 vs 弱票日对照
allg = [r['增益'] for r in rows if isinstance(r['增益'], (int, float))]
out['A_对照'] = {'全部票日增益中位': round(statistics.median(allg), 2) if allg else None,
               '全部票日增益均值': round(sum(allg) / len(allg), 2) if allg else None, 'n': len(allg)}

# --- B. auction-秒板失效复盘: 秒板 × 温度档 (库内交叉表) ---
lib = json.load(open(os.path.join(L, '_竞价池分桶库.json'), encoding='utf-8'))
cross = (lib.get('交叉') or {}).get('信号x温度') or {}
out['B_秒板x温度'] = {'更新': lib.get('更新'), '窗口': lib.get('窗口'),
                    '桶': {k: v for k, v in cross.items() if '秒板' in k},
                    '一字桶': {k: v for k, v in cross.items() if '一字' in k}}

# --- C. master-裁决对照账: 各账nav最新 vs 最佳子路 ---
def nav(route):
    p = os.path.join(L, '_模拟盘', route, '净值.json')
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding='utf-8'))
    ks = sorted(k for k in d if str(k).isdigit())
    if not ks:
        return None
    last = ks[-1]
    v = d[last]
    return {'日': last, 'nav': v.get('nav') if isinstance(v, dict) else v}

navs = {r: nav(r) for r in ('auction', 'lhb', 'theme', 'logic', 'limitup', 'master')}
out['C_账本nav'] = navs

# --- D. cycle-量能台阶: 近10交易日量能档 ---
t = json.load(open(os.path.join(L, '_市场温度表.json'), encoding='utf-8'))
ks = sorted(k for k in t if str(k).isdigit())[-12:]
amt = []
for k in ks:
    row = t[k] or {}
    amt.append(dict(日=k, 成交额亿=row.get('两市成交额_亿') or row.get('两市成交额')))
out['D_量能'] = amt

# --- E. lhb-东吴扬富路立档: 近10日上榜笔数 ---
DIR = os.path.join(L, '_席位动向')
key = '扬富'
hit_days = []
if os.path.isdir(DIR):
    for f in sorted(glob.glob(os.path.join(DIR, '20*.csv')))[-15:]:
        try:
            txt = open(f, encoding='utf-8-sig', errors='ignore').read()
        except Exception:
            continue
        if key in txt:
            hit_days.append(os.path.basename(f).replace('.csv', ''))
out['E_东吴扬富路'] = {'近15个动向日中命中': hit_days, '命中笔数(日数)': len(hit_days)}

# --- F. lhb-新面孔扫描降噪: 最近一次自主拓展扫描 lhb 域输出 ---
cand = sorted(glob.glob(os.path.join(L, '自主拓展扫描_*.json')))
out['F_扫描'] = {'可用文件': [os.path.basename(x) for x in cand[-3:]]}

json.dump(out, open(os.path.join(L, '_周训练孵化探针_20261023.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('A 弱票日:', out['A_弱票池']['弱票日数(命中合计≤1且发满5只)'], '增益中位', out['A_弱票池']['增益中位pct'],
      '均值', out['A_弱票池']['增益均值pct'], '正天数', out['A_弱票池']['增益为正天数'], '/', out['A_弱票池']['增益样本'])
print('A 对照 全票日:', out['A_对照'])
print('B 秒板桶:', json.dumps(out['B_秒板x温度']['桶'], ensure_ascii=False))
print('C nav:', json.dumps(navs, ensure_ascii=False))
print('D 量能:', json.dumps(amt, ensure_ascii=False))
print('E 东吴扬富路:', out['E_东吴扬富路'])
print('F 扫描文件:', out['F_扫描'])
