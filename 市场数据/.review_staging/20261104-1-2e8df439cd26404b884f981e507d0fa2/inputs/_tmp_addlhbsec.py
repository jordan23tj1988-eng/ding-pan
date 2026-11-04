import json,io,shutil,datetime,re
p='_学习/judgment_20261104.json'
shutil.copy2(p,p+'.bak_addsec'+datetime.datetime.now().strftime('%H%M'))
j=json.load(io.open(p,encoding='utf-8-sig'))
b=j['bodies']['lhb']
if '四 档位与胜率' in b:
    print('already has section, skip'); raise SystemExit
det=io.open('_学习/席位分档库.html',encoding='utf-8').read().strip()
sec = ("<section>\n<h2>四 档位与胜率 · 席位分档库读数</h2>\n"
 "<table class=\"trow\">\n"
 "<tr><th>档位判据</th><th>今日读数</th><th>结论</th></tr>\n"
 "<tr><td>分档库规模（自我净化）</td><td>S 18 / A 43 / B 145 / C 92 / 共 176 席，窗口 20260401~20261103，20314 笔</td><td>库在跑：今日 20261104 动向已入库，待 T+1 结算入窗</td></tr>\n"
 "<tr><td>全体基准（执1）</td><td>48.6% / +0.63%</td><td>本路 55 个交易日 109 笔 42.2% / +0.13%（20261103 画像快照）低于基准 6.4pp</td></tr>\n"
 "<tr><td>S/A 出手（今日）</td><td>25 笔 / +11.3356 亿，散在 19 个代码</td><td>名单厚、强度薄：落涨停仅 6 只</td></tr>\n"
 "<tr><td>S/A ∩ 涨停 6 只的去向</td><td>2 只双源强矛盾（688072 拓荆科技、688361 中科飞测）；1 只票级净卖（600371 万向德农 −482 万）；1 只占比 24.58% 落 &gt;20% 极值桶（603248 锡华科技，桶 n=136 / 36.0% / −0.59%）</td><td>4 只被硬门否掉，剩 2 只（300139 占比 6.42%、688200 华峰测控）落 5-10% 弱桶</td></tr>\n"
 "<tr><td>小样本覆盖</td><td>A 档仅 43 席；今日 19 笔 A 档出手 15 笔标⚠（n&lt;25），300139 的中信建投福州东街 n=26 是唯一非小样本 A 档</td><td>分档胜率对今日荐票的解释力有限，只能当即否决用</td></tr>\n"
 "<tr><td>覆盖率盲区</td><td>118 只涨停仅 19 只有当日榜 = 16.1%（昨 25.0%）</td><td>84% 涨停本路无席位数据</td></tr>\n"
 "<tr><td>交集（硬门）</td><td>S/A 净买≥1000万 ∧ 涨停 ∧ 双源非强矛盾 ∧ 净买占比落 10-20% 最优桶 = 空集</td><td><b>档位 C（置信 70）· 0 荐票 · 1 观察</b></td></tr>\n"
 "</table>\n"
 "<div class=\"card\">\n"
 "<p><b>分档库今天告诉我们的是「席位名字可信、席位胜率不可用」。</b>库里 S 18 席 / A 43 席的结构说明高胜率席位是少数派，全体基准 48.6% / +0.63% 也就比抛硬币好一点点；本路长期 42.2% / +0.13%（20261103 画像快照）还低于这个基准 6.4pp，所以分档胜率只能拿来「否票」，不能拿来「选票」。今日 25 笔 S/A 出手散在 19 个代码、落涨停只有 6 只，正是这种结构的写照：名字对得上的票，最近 3 笔记录里今日共有 15 笔落在小样本（n&lt;25）区间，单个席位的历史胜率不足以支撑仓位。</p>\n"
 "<p class=\"mut\">口径提醒：分档用收缩胜率（向全体基准收缩 K=10），n&lt;25 标小样本；执1 = T+1 开盘买→T+1 收盘，执2 = 至 T+2 收盘；零后视镜 = 只用已有前向的笔、每晚重算掉档自动净化。分档库窗口止于 20261103，今日动向已入库但未结算入窗，故今日荐票不能引用「今天之后」的胜率。</p>\n"
 "</div>\n"
 + det +
 "\n</section>")
j['bodies']['lhb']=b+sec
print('div balance:',j['bodies']['lhb'].count('<div') , j['bodies']['lhb'].count('</div>'))
json.dump(j,io.open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('appended, new len',len(j['bodies']['lhb']))
