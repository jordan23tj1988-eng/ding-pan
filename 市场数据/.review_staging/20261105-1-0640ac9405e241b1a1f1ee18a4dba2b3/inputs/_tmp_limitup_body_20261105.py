# -*- coding: utf-8 -*-
"""20261105 limitup body 生成（6 段：荐票/温度/台账/质量库+训练/自主深挖/认知迭代）。"""
import os, json
import pandas as pd, numpy as np

BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, '_学习')
T = '20261105'
b = json.load(open(os.path.join(L, '_tmp_limitup_bundle_%s.json' % T), encoding='utf-8'))
J = json.load(open(os.path.join(L, 'limitup判断_%s.json' % T), encoding='utf-8'))
V = {}
def _fb(s):
    s = str(s).split('.')[0].zfill(6); return s[:2]+':'+s[2:]
_zt = pd.read_csv(os.path.join(BASE, T, 'zt_pool.csv'), dtype={'代码': str})
_zt['开板'] = _zt['炸板次数'].astype(int); _zt['连板'] = _zt['连板数'].astype(int)
_zt['流通亿'] = _zt['流通市值']/1e8; _zt['封单比'] = _zt['封板资金']/_zt['流通市值']*100
def _f2(x, n=2): return ('%.'+str(n)+'f') % float(x)
LAD = []
for k in [1, 2, 3, 4]:
    g = _zt[_zt['连板'] == k]
    if not len(g): continue
    LAD.append(dict(板='%d 板' % k, n=len(g), pct=round(len(g)/len(_zt)*100, 1), 封亿=round(g['封板资金'].sum()/1e8, 2),
                    单票=round(g['封板资金'].mean()/1e8, 3), 封比中=_f2(g['封单比'].median(), 3),
                    换手中=_f2(g['换手率'].median(), 1), 回封=int((g['开板'] >= 1).sum()), 大票=int((g['流通亿'] >= 100).sum())))
OPN = []
for k, lab in [('0', '开板 0 次'), ('1-2', '开板 1-2 次'), ('>=3', '开板 ≥3 次')]:
    g = _zt[_zt['开板'] == 0] if k == '0' else (_zt[_zt['开板'].between(1, 2)] if k == '1-2' else _zt[_zt['开板'] >= 3])
    OPN.append(dict(组=lab, n=len(g), pct=round(len(g)/len(_zt)*100, 1), 封比中=_f2(g['封单比'].median(), 3),
                    换手中=_f2(g['换手率'].median(), 1), 单票=round(g['封板资金'].mean()/1e8, 3), 大票=int((g['流通亿'] >= 100).sum())))
V['LAD'] = LAD; V['OPN'] = OPN
zt = pd.read_csv(os.path.join(BASE, T, 'zt_pool.csv'), dtype={'代码': str}); zt['代码'] = zt['代码'].str.zfill(6)
gui = json.load(open(os.path.join(L, '题材归位_%s.json' % T), encoding='utf-8'))['映射']
grids = pd.read_csv(os.path.join(L, '_tmp_limitup_grids_%s.csv' % T), dtype={'代码': str}); grids['代码'] = grids['代码'].str.zfill(6)
Gm = {r['代码']: r for r in grids.to_dict('records')}
jian = json.load(open(os.path.join(L, '涨停质量荐票_%s.json' % T), encoding='utf-8'))
lib = b['lib']

def fb(s):
    s = str(s).split('.')[0].zfill(6); return s[:2]+':'+s[2:]
zt['首封'] = zt['首次封板时间'].map(fb)
zt['开板'] = zt['炸板次数'].astype(int); zt['连板'] = zt['连板数'].astype(int)
zt['流通亿'] = zt['流通市值']/1e8; zt['封单比'] = zt['封板资金']/zt['流通市值']*100
gm, go, wa, wo, lay, dec, to = b['GRID'], b['G_open'], b['W_all'], b['W_open'], b['LAYER'], b['DEC'], b['TO']
g1, g2 = b['gtop'][0], b['gtop'][1]
t8, t8_20 = b['TOP8'], b['TOP8_20']
tsc = b['tsc']; lt3 = tsc.get('<3%', 0)
th, thp = b['TH'], b['THP']; n_zt, n_zb, zbr = b['n_zt'], b['n_zb'], b['zb_rate']

def sg(x): return '+' + str(x) if float(x) > 0 else str(x)
H = []
a = H.append

# ================= 段1 =================
a('<section>')
a('<h2>一 今日涨停全景 · 荐票序列、昨日结算与全池执行期望</h2>')
a('')
a('<div class="kpi">')
a(f'<b>涨停 {n_zt}</b><span class="hint">昨 118（-28.8%）· 炸板 {n_zb}（炸板率 {zbr}%）· 跌停 0 · 封板总额 {b["feng_total"]} 亿（昨 95.39，-42%）</span>')
a('</div>')
a('<div class="kpi">')
a(f'<b>封单比中位 {b["fengbi_med"]}%</b><span class="hint">昨 0.35% · 单票 {b["feng_per"]} 亿（昨 0.81）· 封得厚、票变少</span>')
a('</div>')
a('<div class="kpi">')
a(f'<b>最高板 4</b><span class="hint">梯队 {b["ladder"]["1"]}/{b["ladder"]["2"]}/{b["ladder"]["3"]}/{b["ladder"]["4"]} · 二板加 {b["lian2plus"]}（昨 12）· 一进二 {b["yijiner"]}%</span>')
a('</div>')
a('<div class="kpi">')
a(f'<b>尾盘封 {b["weipan"]} 只</b><span class="hint">9.5%（昨 44 只/37.3%）· 早盘≤10:00 反增至 30 只 · 大票（≥100亿）{b["big"]} 只</span>')
a('</div>')
a('')
a('<div class="card">')
a(f'<p><b>一句话：宽度退、高度进、接力兑现——紧缩提质，不是退潮开启，但只配 C 档。</b>温度 {th}（中性，昨 {thp}），涨停 {n_zt}（昨 118）、炸板率 {zbr}%（昨 22.0%）、封板总额 {b["feng_total"]} 亿（昨 95.39）、成交 {b["summary"]["两市成交额_亿"]} 亿。'
  f'本路判 <b>C 档 / 置信度 63 / 名义总仓 0</b>，依据是昨日自设条款②「炸板率≥0.35 → 下调 C 档、总仓归零」机械命中（今日 {zbr}%），不带自由裁量；同日反向证据三条同时记录：昨日 118 只今日实测执1 <b>+{b["y_avg"]}%</b>/胜率 {b["y_win"]}%（昨 -1.99%/29.2%）、二板加 {b["lian2plus"]}（+75%）、最高板 4（昨 3）。'
  f'三态定性=混沌（分歧）：宽度与高度背离，封板难度与赚钱效应背离。</p>')
a('</div>')
a('')
a('<table class="table trow">')
a('<thead><tr><th>维度</th><th>20261105</th><th>20261104</th><th>读数</th></tr></thead><tbody>')
rows = [
 ('温度', th, thp, '中性区间 45-65，几乎持平'),
 ('涨停家数', n_zt, 118, '-28.8%，宽度收缩'),
 ('炸板 / 炸板率', f'{n_zb} / {zbr}%', '33 / 22.0%', '封板失败率升 14.4pp，唯一硬风险'),
 ('跌停', 0, 10, '无恐慌盘'),
 ('封板总额(亿)', b['feng_total'], 95.39, '-42%，资金缩量'),
 ('单票封板(亿)', b['feng_per'], 0.81, '降 18.6%，单票资金缩量'),
 ('封单比中位', f'{b["fengbi_med"]}%', '0.35%', '封单厚度翻倍＝质量上移'),
 ('最高连板', 4, 3, '高度推进 1 层'),
 ('二板加', b['lian2plus'], 12, '+75%，连板层扩张'),
 ('梯队', '63/17/2/2', '106/6/6', '首板占比 75.0%（昨 89.8%）'),
 ('一进二', f'{b["yijiner"]}% (17/106)', '18.2% (6/33)', '基本持平'),
 ('高度晋级(2→3以上)', f'{b["gaodu"]}% (4/12)', '50.0% (6/12)', '略降，未断档'),
 ('昨日池今日执1', f'+{b["y_avg"]}%', '-1.99%', '由负转正，接力兑现'),
 ('昨日池今日胜率', f'{b["y_win"]}%', '29.2%', '胜率翻 2.6 倍'),
 ('流通≥100亿占比', f'{b["big_pct"]}% ({b["big"]}只)', '55.1% (65只)', '大票退场，回到小票'),
 ('尾盘封占比', f'{round(b["weipan"]/n_zt*100,1)}% ({b["weipan"]}只)', '37.3% (44只)', '尾盘偷袭消失'),
 ('成交额(亿)', b['summary']['两市成交额_亿'], 20377, '+3.9%'),
]
for r in rows:
    a('<tr><td>%s</td><td><b>%s</b></td><td>%s</td><td class="hint">%s</td></tr>' % r)
a('</tbody></table>')
a('')
a('<div class="card">')
a('<p><b>结构判读（三态=混沌）。</b>四条硬数据把「退潮开启」排除：①昨日 118 只今日执1 从 -1.99% 转到 +2.56%（胜率 29.2%→75.4%），接力有钱赚；②二板加 12→21，连板层在扩张而非萎缩；③最高板 3→4（002578 闽发铝业、601599 浙文影业一字），高度未断档；④尾盘偷袭（昨 44 只/37.3%）今日只剩 8 只（9.5%），封板时间前移到早盘≤10:00 的 30 只（35.7%），封单比中位从 0.35% 升到 0.729%——这是「资金挑票、封得厚」，不是「资金撤退、封不住」。'
  f'真正的问题在结构下沿：{lt3} 只换手&lt;3%（{round(lt3/n_zt*100,1)}%）落在库内最差换手桶（33.9%/-0.94%），63 只首板多数落在「&lt;100亿·10cm·首板 +0.35%」弱格，导致全池可兑现期望 <b>{b["pos"]} 正 / {n_zt-b["pos"]} 负、合计 {b["tot"]}pp</b>。宽度退不是崩塌，但也不够格给仓位。</p>')
a('</div>')
a('')
a('<div class="card">')
a('<p><b>昨日荐票结算（T+1 bars 实测，20261105）。</b>本路昨日 2 荐 1 观：002992 宝明科技（荐票 1.0%）gap -0.99%→执1 <b>-4.75%</b>；688809 强一股份（荐票 1.2%）gap +0.75%→执1 <b>+5.94%</b>（盘中最高 +10.66%）；002980 华盛昌（观察 0）gap -1.95%→执1 +0.63%。'
  f'按权重组合净贡献 <b>+{b["nav"]}pp</b>——正收益全部来自 688809 一只，002992 一票把组合从 +0.71pp 拉回 +0.024pp。002992 收绿（-5.69%）触发昨日条款②「收红失败→该格降观察级、n&lt;50 不得作荐票主依据」（其格 n=41），该格今日起退出荐票主依据。</p>')
a('</div>')
a('')
a('<table class="table trow">')
a('<thead><tr><th>代码</th><th>名称</th><th>类型</th><th>权重</th><th>开盘 gap</th><th>执1(开盘→收盘)</th><th>当日涨跌</th><th>结算</th></tr></thead><tbody>')
for s in b['SETTLE']:
    ok = '正' if s['e1'] > 0 else '负'
    a(f'<tr><td>{s["代码"]}</td><td>{s["名称"]}</td><td>{s["类型"]}</td><td>{s["权重"]}%</td><td>{sg(s["gap"])}%</td><td><b>{sg(s["e1"])}%</b></td><td>{sg(s["chg"])}%</td><td class="hint">{ok}贡献 {round(s["权重"]*s["e1"]/100,4)}pp</td></tr>')
a('</tbody></table>')
a('')
a('<div class="card">')
a('<h3>今日质量荐票卡（源：_学习/涨停质量荐票_20261105.json top5；题材列取 _学习/题材归位_20261105.json）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>代码</th><th>名称</th><th>题材（大方向·环节）</th><th>连板</th><th>封比</th><th>换手</th><th>质量分</th><th>理由</th></tr></thead><tbody>')
for x in jian['top5']:
    c = x.get('代码'); g = gui.get(c, {}); gr = Gm.get(c, {})
    a(f'<tr><td>{c}</td><td>{x.get("名称")}</td><td>{g.get("大方向","—")}·{g.get("环节","—")}<span class="hint"> {g.get("来源档","—")}</span></td>'
      f'<td>{x.get("连板", gr.get("连板","—"))}</td><td>{gr.get("封单比","—")}%</td><td>{gr.get("换手","—")}%</td><td>{x.get("质量分","—")}</td>'
      f'<td class="hint">{x.get("理由") or x.get("备注") or "—"}</td></tr>')
a('</tbody></table>')
a('<p class="hint">注：质量荐票 top5 是「质量分×当日池」排序结果，非本路最终荐票；本路最终结论见下（0 荐票 + 2 观察）。</p>')
a('</div>')
a('')
a('<div class="card">')
a('<h3>本路荐票结论：0 荐票 + 2 观察（0 权重）</h3>')
a(f'<p>{J["荐票"]["结论"]}</p>')
a('</div>')
a('')
a('<table class="table trow">')
a('<thead><tr><th>代码</th><th>名称</th><th>类型</th><th>题材</th><th>连板</th><th>首封</th><th>开板</th><th>换手</th><th>封比</th><th>流通(亿)</th><th>格期望</th></tr></thead><tbody>')
for w in J['荐票']['观察明细']:
    a(f'<tr><td>{w["代码"]}</td><td>{w["名称"]}</td><td>{w["类型"]}</td><td>{w["题材"]}</td><td>{w["连板"]}</td><td>{w["首封"]}</td><td>{w["开板"]}</td>'
      f'<td>{w["换手"]}%</td><td>{w["封单比"]}%</td><td>{w["市值"]}</td><td><b>+{w["期望"]}pp</b><span class="hint"> n={w["n"]} 胜率{w["格胜率"]}% 均收+{w["格均收"]}%</span></td></tr>')
a('</tbody></table>')
a('')
a('<div class="card">')
a('<p><b>为什么是 0 仓而不是小仓试错。</b>全池 {0} 只可兑现期望合计 {1}pp，最高单票 +{2}pp，本路既设门槛是「单票期望≥+1pp 才给权重」，今日无一票过线；炸板率 {3}% 又在昨日条款②的「或」门里直接命中「总仓归零」。'
  '在混沌态、且本路执行胜率 36.1%/均收 -0.75% 的历史下，用 0 仓换一张完整的次日结算表（2 只观察票照常登记、照常结算）比用小仓试错更省成本。观察票的启用条件写入交易计划与可证伪条件，明日按机械口径放行或作废。'.format(n_zt, b['tot'], g1['期望pp'], zbr))
a('</p>')
a('</div>')
a('</section>')
a('')

# ================= 段2 =================
a('<section>')
a(f'<h2>二 市场温度 · {th} 中性档位下的梯队、封板时段与炸板结构</h2>')
a('')
a('<div class="kpi">')
a(f'<b>温度 {th}</b><span class="hint">中性（45-65）· 昨 {thp} · 前日 20.3 · 连续两日 49 附近，无方向</span>')
a('</div>')
a('<div class="kpi">')
a(f'<b>挡位 C</b><span class="hint">条款②命中：炸板率 {zbr}%≥35% → 总仓归零 · 名义仓位 0</span>')
a('</div>')
a('<div class="kpi">')
a(f'<b>梯队 {b["ladder"]["1"]}/{b["ladder"]["2"]}/{b["ladder"]["3"]}/{b["ladder"]["4"]}</b><span class="hint">首板占 75.0% · 2板及以上 {b["lian2plus"]} 只（25.0%，昨 10.2%）</span>')
a('</div>')
a('<div class="kpi">')
a(f'<b>炸板 {n_zb} 只</b><span class="hint">炸板率 {zbr}% · 回封（开板≥1后仍封）{b["open_grp"]["1-2"]+b["open_grp"][">=3"]} 只 · 未开板 {b["open_grp"]["0"]} 只</span>')
a('</div>')
a('')
a('<h3>连板梯队画像</h3>')
a('<table class="table trow">')
a('<thead><tr><th>板数</th><th>家数</th><th>占比</th><th>封板资金(亿)</th><th>单票(亿)</th><th>封单比中位</th><th>换手中位</th><th>开过板</th><th>≥100亿</th></tr></thead><tbody>')
for r in V['LAD']:
    a(f'<tr><td>{r["板"]}</td><td><b>{r["n"]}</b></td><td>{r["pct"]}%</td><td>{r["封亿"]}</td><td>{r["单票"]}</td><td>{r["封比中"]}%</td><td>{r["换手中"]}%</td><td>{r["回封"]}</td><td>{r["大票"]}</td></tr>')
a('</tbody></table>')
a('<p class="hint">读法：4 板 2 只封板资金 {0} 亿、封单比中位 {1}%，是全池最厚的一层；首板 63 只单票仅 {2} 亿＝薄封居多，这是全池期望为负的结构位置。'.format(V['LAD'][3]['封亿'], V['LAD'][3]['封比中'], V['LAD'][0]['单票']))
a('</p>')
a('')
a('<h3>炸板结构（开板次数分层）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>组</th><th>家数</th><th>占比</th><th>封单比中位</th><th>换手中位</th><th>单票封板(亿)</th><th>≥100亿</th></tr></thead><tbody>')
for r in V['OPN']:
    a(f'<tr><td>{r["组"]}</td><td><b>{r["n"]}</b></td><td>{r["pct"]}%</td><td>{r["封比中"]}%</td><td>{r["换手中"]}%</td><td>{r["单票"]}</td><td>{r["大票"]}</td></tr>')
a('</tbody></table>')
a('')
a('<h3>首封时段分布</h3>')
a('<table class="table trow">')
a('<thead><tr><th>时段</th><th>家数</th><th>占比</th><th>昨</th><th>读数</th></tr></thead><tbody>')
segrows = [('严格一字(≤09:25且炸0)', 5, '4', '略增'), ('秒板(≤09:31)', 8, '5', '抢筹前移'), ('早盘(≤10:00)', 30, '12', '翻倍，资金提前动手'),
           ('盘中(10:00-14:00)', 33, '52', '主力段收缩'), ('尾盘(>14:00)', b['weipan'], '44', '偷袭基本消失')]
for r in segrows:
    a(f'<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{round(r[1]/n_zt*100,1)}%</td><td>{r[2]}</td><td class="hint">{r[3]}</td></tr>')
a('</tbody></table>')
a('')
a('<div class="card">')
a('<p><b>温度与档位的分工。</b>温度 49.3 是「环境坐标」——中性、连续两日在 49 附近、前日 20.3 冰点后修复，说明环境既未进主升也未回冰点；档位是「今日能不能下手」——炸板率 36.4% 直接把仓位门关死。'
  '两者不矛盾：温度管环境，档位管执行。今日温度中性而炸板率高企＝环境可做、个股难做，正是「宽度退、高度进」的环境签名。'
  '另需记录：今日炸板池 48 只中 21 只流通≥100 亿（占炸板池 43.8%，而涨停池只有 26.2%），大票封不住是炸板率的主因，而不是小票乱封。</p>')
a('</div>')
a('</section>')
a('')

# ================= 段3 =================
a('<section>')
a(f'<h2>三 全量归位台账 · {n_zt} 只涨停逐票（题材取归位真源，禁自编）</h2>')
a(f'<p class="hint">全量 {n_zt} 行，按连板降序、封板资金降序。格期望＝该票所在「连板桶×首封桶×换手桶」格的执1历史均值×闸门触发率折算后偏差（正=可兑现、负=不可兑现）；题材列取 _学习/题材归位_20261105.json（A 档 0 / B 档 83 / C 档 1）。</p>')
a('<!--LEDGER-->')
a('<table class="table trow">')
a('<thead><tr><th>#</th><th>代码</th><th>名称</th><th>题材（大方向·环节）</th><th>档</th><th>连板</th><th>首封</th><th>开板</th><th>换手%</th><th>封单比%</th><th>流通(亿)</th><th>格期望pp</th></tr></thead><tbody>')
zz = zt.sort_values(['连板', '封板资金'], ascending=[False, False]).reset_index(drop=True)
for i, r in zz.iterrows():
    c = r['代码']; g = gui.get(c, {}); gr = Gm.get(c, {})
    a(f'<tr><td>{i+1}</td><td>{c}</td><td>{r["名称"]}</td><td>{g.get("大方向","—")}·{g.get("环节","—")}</td><td>{g.get("来源档","—")}</td>'
      f'<td>{r["连板"]}</td><td>{r["首封"]}</td><td>{r["开板"]}</td><td>{round(float(r["换手率"]),1)}</td><td>{round(float(r["封单比"]),2)}</td>'
      f'<td>{round(float(r["流通亿"]),1)}</td><td>{sg(gr.get("期望pp","—"))}</td></tr>')
a('</tbody></table>')
a('<!--/LEDGER-->')
a('</section>')
a('')

# ================= 段4 =================
a('<section>')
a('<h2>四 涨停质量库 · 因子主导度、Top8 抓龙率与格重算训练</h2>')
a('')
a(f'<div class="card"><p><b>库健康度：</b>更新 {lib.get("更新")}、样本 {lib.get("样本")}、活跃因子 {len(lib.get("活跃因子") or [])}/{len(lib.get("因子") or {})}；基准：执1 胜率 {lib["基准"]["执1胜率"] if "执1胜率" in lib["基准"] else "—"}%、均收 {lib["基准"]["执1均涨"] if "执1均涨" in lib["基准"] else "—"}%、抓龙率 {lib["基准"]["抓龙率"]}%。窗口 20250701~20261105。</p></div>')
a('')
a('<h3>因子主导度（权重与区分度）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>因子</th><th>权重</th><th>区分度(pp)</th><th>状态</th><th>说明</th></tr></thead><tbody>')
ACT = lib.get('活跃因子') or []
for k, v in lib['因子'].items():
    st = v.get('状态', '—')
    note = v.get('说明') or v.get('备注') or ('活跃' if k in ACT else '已淘汰（不参与打分）')
    a(f'<tr><td>{k}</td><td>{v.get("权重",0):.4f}</td><td>{v.get("区分度",0)}</td><td>{st}</td><td class="hint">{note}</td></tr>')
a('</tbody></table>')
a('')
a('<h3>质量分分档单调性（20250701~20261105 全样本，n=19822）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>质量分档</th><th>样本</th><th>执1胜率</th><th>执1均收</th><th>执2胜率</th><th>执2均收</th><th>抓龙率(执2≥+8%)</th></tr></thead><tbody>')
for r in dec:
    a(f'<tr><td>{r["档"]}</td><td>{r["n"]}</td><td><b>{r["w"]}%</b></td><td><b>{sg(r["r"])}%</b></td><td>{r["w2"]}%</td><td>{sg(r["r2"])}%</td><td>{r["dr"]}%</td></tr>')
a('</tbody></table>')
a('<p class="hint">执1 五档单调（30.9%→58.1%），抓龙率不单调（24.6/14.0/15.4/16.9/14.1%）＝质量分是「隔日兑现筛子」，不是「连板抓龙模型」。11+ 档执1 最高但执2 转负 -0.89%，只配隔日盯市。</p>')
a('')
a('<h3>Top8 抓龙率与组合 edge（每日取质量分前 8）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>口径</th><th>Top8 执1</th><th>全池执1</th><th>超额</th><th>Top8 抓龙率</th><th>全池抓龙率</th><th>日胜率</th></tr></thead><tbody>')
a(f'<tr><td>全窗口 {t8["days"]} 日</td><td><b>+{t8["e1"]}%</b>（胜率 {t8["e1w"]}%）</td><td>{t8["pool"]}%</td><td>+{round(t8["e1"]-t8["pool"],2)}pp</td><td><b>{t8["dr"]}%</b></td><td>{t8["pdr"]}%</td><td>超额日 {t8["beat"]}/{t8["days"]}＝{t8["beat_pct"]}%；抓龙超额仅 {t8["beat_dr"]}/{t8["days"]}＝{t8["beat_dr_pct"]}%</td></tr>')
a(f'<tr><td>近 20 日</td><td><b>+{t8_20["e1"]}%</b>（胜率 {t8_20["e1w"]}%）</td><td>{t8_20["pool"]}%</td><td>+{round(t8_20["e1"]-t8_20["pool"],2)}pp</td><td>{t8_20["dr"]}%</td><td>{t8_20["pdr"]}%</td><td class="hint">近期 edge 放大，抓龙仍无效</td></tr>')
a('</tbody></table>')
a('<p class="hint">抓龙率结论：Top8 与全池抓龙率 16.8% vs 16.5%、日胜率 45.0%（≈掷硬币），<b>质量分对抓龙率无 edge</b>；今日 Top8 平均预测抓龙率 {0}% 反而低于基准 {1}%。荐票排序只能按执1，抓龙率只作 tie-break。'.format(b['top8_dr_avg'], lib['基准']['抓龙率']))
a('</p>')
a('')
a('<h3>今日质量分 Top8（含主导因子）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>代码</th><th>名称</th><th>质量分</th><th>预测抓龙</th><th>换手</th><th>连板</th><th>首封</th><th>开板</th><th>流通(亿)</th><th>主导因子</th></tr></thead><tbody>')
for x in b['TOP8_TODAY']:
    a(f'<tr><td>{x["代码"]}</td><td>{x["名称"]}</td><td><b>{x["质量分"]}</b></td><td>{x["抓龙"]}%</td><td>{x["换手"]}%</td><td>{x["连板"]}</td><td>{x["首封"]}</td><td>{x["开板"]}</td><td>{x["市值"]}</td><td class="hint">{x["主导"]}</td></tr>')
a('</tbody></table>')
a('<p class="hint">Top8 抓龙率均值 {0}%（基准 {1}%）、抓龙数 2/8——<b>今日抓龙率不成立</b>；质量分高的原因集中在「开板次数(开2次+)、封单比弱(&lt;0.5%+1.3)、股价≥40元」三条，其中「开板 2 次+加分」正是本段深挖要重算的口径。'.format(b['top8_dr_avg'], lib['基准']['抓龙率']))
a('</p>')
a('')
a('<details class="chain"><summary>历史格验证（尾盘族按开板重分桶 · 首板×尾盘×换手10-20% 格重算）</summary>')
a('<table class="table trow">')
a('<thead><tr><th>子集</th><th>n</th><th>执1胜率</th><th>执1均收</th><th>执2胜率</th><th>执2均收</th><th>闸门触发</th></tr></thead><tbody>')
a(f'<tr><td>格全体</td><td><b>{gm["n"]}</b></td><td>{gm["w"]}%</td><td>{sg(gm["r"])}%</td><td>{gm["w2"]}%</td><td>{sg(gm["r2"])}%</td><td>{gm["gate"]}%</td></tr>')
for k, lab in [('0', '开板 0 次'), ('1-2', '开板 1-2 次'), ('>=3', '开板 ≥3 次')]:
    r = go[k]
    a(f'<tr><td>{lab}</td><td>{r["n"]}</td><td>{r["w"]}%</td><td>{sg(r["r"])}%</td><td>{r["w2"]}%</td><td>{sg(r["r2"])}%</td><td>{r["gate"]}%</td></tr>')
a('</tbody></table>')
a('<table class="table trow">')
a('<thead><tr><th>尾盘族全体</th><th>n</th><th>执1胜率</th><th>执1均收</th><th>执2胜率</th><th>执2均收</th><th>闸门触发</th></tr></thead><tbody>')
a(f'<tr><td>全体</td><td><b>{wa["n"]}</b></td><td>{wa["w"]}%</td><td>{sg(wa["r"])}%</td><td>{wa["w2"]}%</td><td>{sg(wa["r2"])}%</td><td>{wa["gate"]}%</td></tr>')
for k, lab in [('0', '开板 0 次'), ('1-2', '开板 1-2 次'), ('>=3', '开板 ≥3 次')]:
    r = wo[k]
    a(f'<tr><td>{lab}</td><td>{r["n"]}</td><td>{r["w"]}%</td><td>{sg(r["r"])}%</td><td>{r["w2"]}%</td><td>{sg(r["r2"])}%</td><td>{r["gate"]}%</td></tr>')
a('</tbody></table>')
a('<table class="table trow">')
a('<thead><tr><th>尾盘族三层（市值×制度×连板）</th><th>n</th><th>执1胜率</th><th>执1均收</th><th>执2胜率</th><th>执2均收</th><th>闸门触发</th></tr></thead><tbody>')
for r in lay:
    a(f'<tr><td>{r["格"]}</td><td>{r["n"]}</td><td>{r["w"]}%</td><td><b>{sg(r["r"])}%</b></td><td>{r["w2"]}%</td><td>{sg(r["r2"])}%</td><td>{r["gate"]}%</td></tr>')
a('</tbody></table>')
a('</details>')
a('')
a('<h3>换手率因子复检（本路可复用能力 cap-limitup-turnover-valid）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>换手桶</th><th>n</th><th>执1胜率</th><th>执1均收</th><th>执2胜率</th><th>执2均收</th><th>闸门触发</th><th>库权重</th></tr></thead><tbody>')
for k in ['<3%', '3-10%', '10-20%', '≥20%']:
    r = to[k]
    a(f'<tr><td>{k}</td><td>{r["n"]}</td><td><b>{r["w"]}%</b></td><td><b>{sg(r["r"])}%</b></td><td>{r["w2"]}%</td><td>{sg(r["r2"])}%</td><td>{r["gate"]}%</td><td>0.1516</td></tr>')
a('</tbody></table>')
a(f'<p class="hint">结论：四档执1 单调 33.9%→45.4%（唯一正桶 ≥20% +0.11%），与库记录逐位一致；20260901 起近 2 月仍单调（29.9/41.7/42.6/46.2）。今日 {lt3} 只换手&lt;3% 票（占 {round(lt3/n_zt*100,1)}%）全部落入最差桶，构成本路 0 仓的第二条硬依据。</p>')
a('</section>')
a('')

# ================= 段5 =================
D = J['深挖']
a('<section>')
a('<h2>五 自主深挖 · 承接Master指派[MA-20261104-01]：688809 炸板次数修正与开板分层次日检验</h2>')
a('')
a('<div class="card">')
a(f'<p><b>指派回执：<code>承接Master指派[MA-20261104-01]</code> 三项全部完成</b>——①688809 荐票卡炸板次数修正（0→6）并按其真实开板次数重算所在格；②按开板次数重算「首板×尾盘×换手10-20%」格；③把昨日两处互相矛盾的开板口径唯一化。结论：昨日「开板 39.3%/-0.699% 弱族」与「开过板＝双正交集」两句不能同时用，唯一口径＝<b>先锁首封时段、再切开板次数</b>。</p>')
a('</div>')
a('')
a('<h3>① 688809 强一股份：字段修正与格内定位</h3>')
a('<table class="table trow">')
a('<thead><tr><th>字段</th><th>昨日本路所写</th><th>zt_pool 20261104 真值</th></tr></thead><tbody>')
A = D['① 688809 修正']['正确字段(zt_pool 20261104)']
a(f'<tr><td>炸板次数</td><td>0 次（错）</td><td><b>{A["炸板"]} 次</b></td></tr>')
a(f'<tr><td>首次封板</td><td>未记</td><td>{A["首封"]}</td></tr>')
a(f'<tr><td>最后封板</td><td>未记</td><td>{A["末封"]}</td></tr>')
a(f'<tr><td>封板资金 / 流通</td><td>封死</td><td>{A["封亿"]} 亿 / {A["流通亿"]} 亿＝封单比 {A["封单比"]}%</td></tr>')
a(f'<tr><td>换手</td><td>未记</td><td>{A["换手"]}%</td></tr>')
a(f'<tr><td>今日实测(20261105)</td><td>—</td><td>gap +{A["today"]["gap"]}%、执1 <b>+{A["today"]["e1"]}%</b>、盘中最高 +{A["today"]["high"]}%、收 {A["today"]["close"]}（+{A["today"]["chg"]}%）</td></tr>')
a('</tbody></table>')
a(f'<p class="hint">{D["① 688809 修正"]["结论"]}</p>')
a('')
a('<h3>② 「首板×尾盘&gt;14:00×换手10-20%」格按开板重算</h3>')
a('<table class="table trow">')
a('<thead><tr><th>子集</th><th>n</th><th>执1胜率</th><th>执1均收</th><th>执2胜率</th><th>执2均收</th><th>vs 格均值</th></tr></thead><tbody>')
for k, lab in [('0', '开板 0 次（未开板）'), ('1-2', '开板 1-2 次'), ('>=3', '开板 ≥3 次')]:
    r = go[k]
    a(f'<tr><td>{lab}</td><td>{r["n"]}</td><td>{r["w"]}%</td><td><b>{sg(r["r"])}%</b></td><td>{r["w2"]}%</td><td>{sg(r["r2"])}%</td><td>{sg(round(r["r"]-gm["r"],2))}pp</td></tr>')
a('</tbody></table>')
a(f'<p>{D["② 格重算(开板分层)"]["回答"]}</p>')
a('')
a('<h3>③ 尾盘族按开板重分桶 & ④ 三层切分（开板之外的更硬切分）</h3>')
a('<table class="table trow">')
a('<thead><tr><th>尾盘族子集</th><th>n</th><th>执1胜率</th><th>执1均收</th><th>执2胜率</th><th>执2均收</th></tr></thead><tbody>')
for k, lab in [('0', '开板 0 次'), ('1-2', '开板 1-2 次'), ('>=3', '开板 ≥3 次')]:
    r = wo[k]
    a(f'<tr><td>{lab}</td><td>{r["n"]}</td><td>{r["w"]}%</td><td>{sg(r["r"])}%</td><td>{r["w2"]}%</td><td>{sg(r["r2"])}%</td></tr>')
a('</tbody></table>')
a('<table class="table trow">')
a('<thead><tr><th>尾盘族·三层格</th><th>n</th><th>执1胜率</th><th>执1均收</th><th>执2均收</th><th>闸门触发</th></tr></thead><tbody>')
for r in lay:
    a(f'<tr><td>{r["格"]}</td><td>{r["n"]}</td><td>{r["w"]}%</td><td><b>{sg(r["r"])}%</b></td><td>{sg(r["r2"])}%</td><td>{r["gate"]}%</td></tr>')
a('</tbody></table>')
a(f'<p>{D["④ 尾盘族三层切分"]["结论"]}</p>')
a('')
a('<h3>⑤ 口径唯一化与可结算判定</h3>')
a(f'<p><b>昨日矛盾：</b>{D["⑤ 矛盾口径唯一化"]["昨日矛盾"]}。<b>唯一口径：</b>{D["⑤ 矛盾口径唯一化"]["唯一口径"]}</p>')
a(f'<p><b>次日可结算判定条件：</b>{D["可结算判定条件"]}</p>')
a('</section>')
a('')

# ================= 段6 =================
a('<section>')
a('<h2>六 我的认知迭代 · 今日五条（全部带可回查证据）</h2>')
a('')
for i, c in enumerate(J['认知迭代'], 1):
    a('<div class="card">')
    a(f'<h3>{i}. {c["标题"]}</h3>')
    a(f'<p>{c["正文"]}</p>')
    a(f'<p class="hint">证据：{c["证据"]}</p>')
    a('</div>')
    a('')
a('<div class="card">')
a('<h3>本路今日对系统的三个硬请求</h3>')
a('<p>①质量库把「开板次数」因子从「开次数加分」拆成「时段内开板」条件项：现有口径给「开2次+1.6」加分，与尾盘族「开板 1-2 最强」同向，但在早盘/一字族可能反号，需按时段重估权重。'
  '②质量库的「抓龙率」字段建议降级为展示项：Top8 抓龙率与全池无差（16.8% vs 16.5%、日胜率 45.0%），今日预测均值 14.8% 还低于基准 15.9%，继续参与排序会把荐票引向「高分不高收益」。'
  '③总审侧把「昨日池执1」与「二板加环比」纳入档位下调的合取条件：只靠炸板率一条会像今日这样，把接力改善读成退潮。</p>')
a('</div>')
a('</section>')

html = '\r\n'.join(H)
open(os.path.join(L, 'limitup_body_%s.html' % T), 'w', encoding='utf-8').write(html)
print('body chars', len(html), 'rows', len(zz))
print('segments', html.count('<h2>'))
