# -*- coding: utf-8 -*-
"""宿主侧: 生成 index_body / cycle_body (20261104) 并注入 judgment 七页 body"""
import json, io, os

BASE = r"D:/股票数据/市场数据"
L = os.path.join(BASE, "_学习")
D = "20261104"

def jl(p): return json.load(io.open(p, encoding="utf-8"))
def w(p, s):
    with io.open(p, "w", encoding="utf-8") as f: f.write(s)

temp = jl(os.path.join(L, "_市场温度表.json"))
lead = jl(os.path.join(L, "_情绪先行指标.json"))
z = jl(os.path.join(L, "总审_%s.json" % D))
p = jl(os.path.join(L, "推演_%s.json" % D))
pre = sorted(k for k in temp if k < D)[-1]

def dayc(k, now=False):
    v = temp[k]
    return '<span class="dayc%s">%s-%s %.1f°</span>' % (" now" if now else "", k[4:6], k[6:8], v.get("温度", 0))

days = "".join(dayc(k, k == D) for k in sorted(temp)[-5:])

verdict = z.get("总裁决") or {}
picks = verdict.get("明日验证点") or verdict.get("可证伪条件") or ""

# ---------- index body ----------
idx = []
idx.append('<div class="rowA"><div class="hero"><div class="kick">Index · 总判断 · 截至 11-04 收盘</div>'
           '<h1>温度 49.0 从冰点直跳中性档 · 宽度修复但接力没回来</h1>'
           '<p>涨停 118（昨 48）、炸板率 22.0%（昨 41.5%）、封板总额 95.4 亿（+148%）、成交 20377 亿（+19.6%）——四项宽度指标同日修复；'
           '但最高连板只有 3（昨 4）、首封≥13:00 占 72.0%、封单比中位 0.35%、昨日 48 只今日开→收 −1.99%／胜率 29.2%，'
           '接力层是负的。五路四 C 一 B、总裁决 C 档 68 分名义 1.5%，只做窄口径试探，不站线。</p>'
           '<div class="stance"><span class="pill">总裁决 · <b>C 档</b> · 名义 1.5%</span></div></div></div>')

idx.append('<h2>一 总判断 · 冰点后的换血型修复</h2>')
idx.append('<div class="card"><p>温度 <b>49.0</b>（昨 20.3，Δ+28.7）落中 40~65 档；涨停 118 只里 65 只（55.1%）流通≥100 亿，昨日仅 2 只（4.2%）——'
           '宽度是<b>新钱换血</b>不是老票延续。近 5 日温度：' + days + '</p>'
           '<table class="p2"><tr><th class="l">口径</th><th>今日</th><th>昨</th><th>读数含义</th></tr>'
           '<tr><td class="l">情绪温度</td><td>49.0</td><td>20.3</td><td>中性档中位，历史该档票级胜率 35.0%~38.2%</td></tr>'
           '<tr><td class="l">净涨停 / 跌停</td><td>118 / 10</td><td>48 / 17</td><td>宽度单日放 2.5 倍</td></tr>'
           '<tr><td class="l">炸板率 / 封板率</td><td>22.0% / 78.15%</td><td>41.5% / —</td><td>封板质量同步修复，回封 65 只</td></tr>'
           '<tr><td class="l">最高连板 / 梯队</td><td>3 / 106-6-6</td><td>4 / —</td><td>高度反而退一格，天花板未破</td></tr>'
           '<tr><td class="l">两市成交额</td><td>20377 亿</td><td>17034 亿</td><td>+19.6%，量能跟上宽度</td></tr>'
           '<tr><td class="l">一进二 / 二进三</td><td>18.2% / 50.0%</td><td>10.5% / —</td><td>腰部略回暖，但高度晋级仅 40.0%</td></tr>'
           '<tr><td class="l">昨日涨停溢价</td><td>—</td><td>—</td><td>标准源取数失败（东财 spot），禁用替代估算</td></tr></table>'
           '<div class="hint">口径来源：_学习/_市场温度表.json#20261104、_学习/_情绪先行指标.json#20261104、20261104/summary.json。昨停溢价取数失败，页面按「—」呈现不补造。</div></div>'
           )

idx.append('<h2>二 核心观察 · 明日三个必看</h2>')
preds = (p.get("次日可证伪预测") or [])[:4]
rows = []
for x in preds:
    c = x.get("判定条件") or {}
    rows.append('<tr><td class="l">%s</td><td>%s</td><td>%s %s</td></tr>' % (
        x.get("项", "—"), str(x.get("预测", "—"))[:160], c.get("指标", "—"), c.get("阈值", "—")))
idx.append('<div class="card"><table class="p2"><tr><th class="l">可证伪项</th><th>预测</th><th>判定条件</th></tr>'
           + "".join(rows) + '</table>'
           '<p class="mut">全部 %d 条预测与判定条件见「周期情绪」页与 _学习/推演_%s.json，次日由 预判结算.py 机械结算。</p></div>'
           % (len(p.get("次日可证伪预测") or []), D))

idx.append('<h2>三 题材树与五路看牌</h2>')
idx.append('<div class="card"><p><b>无主流（退为轮动）</b>：归位 118 只覆盖 16 条方向、A 档 0（无公告级催化，全部来自 THS 涨停原因）。'
           '宽度第一 半导体 34 只（占 28.8%、封单 35.30 亿＝37.0%）是午后扩散——早封 0/34、≥13:00 封 31/34（91.2%）、封单比中位 0.31%、题材晋级率 0，判「宽度陷阱」；'
           '传媒/出版AI应用 6 只有 3 只 3 板（600892/601599/605577）、封单比中位 1.92% 全场第一，但宽度 6＜15 门，只给「主线候选」；'
           '有色/小金属的 5/6 是单票假主流（002827 4.20 亿＋002428 4.09 亿＝74.8% 封单）。</p>'
           '<table class="p2"><tr><th class="l">路</th><th>档位</th><th>置信度</th><th>荐票</th><th>核心一句</th></tr>'
           '<tr><td class="l">①竞价 auction</td><td>C</td><td>67</td><td>1.0%（605577，被总审否决）</td><td>中档 20 个池日均收 −0.51%、中档+涨停≥90 的 7 池日 −1.53%，基准仓为 0</td></tr>'
           '<tr><td class="l">②席位 lhb</td><td>C</td><td>70</td><td>0（空仓）</td><td>榜票级净买 −22.21 亿、全场真实率 −21.11%，强度不可读</td></tr>'
           '<tr><td class="l">③题材 theme</td><td>C</td><td>68</td><td>0（3 观察）</td><td>无主流；半导体是宽度不是方向</td></tr>'
           '<tr><td class="l">④产逻 logic</td><td>C</td><td>72</td><td>0（2 观察）</td><td>业绩腿 52.5% 真增长，但首封≥13:00 占 72%</td></tr>'
           '<tr><td class="l">⑤涨停 limitup</td><td>B</td><td>64</td><td>2（002992/688809）</td><td>宽度与封板质量同日修复，机械触发上调 B，但非接力修复</td></tr>'
           '</table><div class="hint">五路看牌明细见对应五页；总裁决对 limitup 的 B 降档至 C（与各路同为 C 档口径）。</div></div>')

idx.append('<h2>四 拐点预警与明日验证</h2>')
idx.append('<div class="card"><p><b>总裁决：%s 档 · %s 分 · 名义 %s</b>（单票上限 1.0%%）。%s</p>'
           '<p>明日验证（互斥、机械）：①温度≥35 且 ≤55 → 宽度不塌也不发烧，C 档维持；温度≤34.9 → 宽度为一日反抽、总仓归零。'
           '②涨停数 60~90 带内 → 换血型修复成立；≥91 → 宽度延续，C 上调 B；≤59 → 单日孤峰，开盘前新单作废。'
           '③最高连板≥4 → 高度续一格（6 只 3 板至少 1 只晋级）；≤3 全断 → 传媒缩圈线出池、高度轴 0 权重。'
           '④一进二率≥0.12 → 腰部不断；≤0.119 → 002992/688809 若成交即按 −3%% 离场。</p>'
           '<p class="mut">数据缺口：昨日涨停溢价（东财 spot 失败）缺失；竞价快照仅覆盖首封≤09:31 的 10 只（118 只的 8.5%%），对 96 只盘中/尾盘封票无竞价定价能力，页面与推演均不宣称竞价分位。</p></div>'
           % (verdict.get("档位", "C"), verdict.get("置信度", 68),
              str(verdict.get("名义仓位") or verdict.get("仓位") or "1.5%"),
              str(verdict.get("依据") or "")[:300]))

idx.append('<h2>五 自主深挖 · 承接与线索</h2>')
idx.append('<div class="card"><p>今日总审签发 5 条新指派（均截止 20261106）：MA-01 limitup（688809 炸板计数修正＋尾盘族三层切分）、MA-02 auction（尾盘封票次日 gap 分布，补昨日 MA-04 零进展）、'
           'MA-03 theme（半导体 vs 传媒分母归属＋20cm 分层）、MA-04 logic（PCB 链抢筹/接盘＋002992 归位污染）、MA-05 lhb（覆盖率-宽度函数＋分层脚本化）。'
           '昨日 MA-20261103-01（theme 三项）与 MA-20261103-02（limitup 002652 正交检验）按期完成：剔除谐音标签后 n=28／64.3%%／+2.229%%＞+1%%，判「形态格与标签正交」。</p>'
           '<p class="mut">自主拓展清单 15 项已逐项应答：立项 1（竞价低开档下界）、并入 9、不深挖 5，明细见 _学习/自主拓展应答_%s.json。</p></div>' % D)

idx.append('<h2>六 我的认知迭代</h2>')
zrec = z.get("认知迭代") or []
if isinstance(zrec, dict): zrec = [zrec]
items = []
for it in zrec[:3]:
    if isinstance(it, dict):
        items.append('<div class="tli"><div class="d">%s</div><div class="h">%s</div><div class="b">%s</div></div>' % (
            str(it.get("日期", D)), str(it.get("标题", "—"))[:60], str(it.get("内容") or it.get("正文") or "")[:600]))
    else:
        items.append('<div class="tli"><div class="d">%s</div><div class="b">%s</div></div>' % (D, str(it)[:600]))
if not items:
    items.append('<div class="tli"><div class="d">%s</div><div class="b">温度从冰点 20.3 一日跳回 49.0，但该档历史票级胜率只有 35.0%%~38.2%%——「温度回升」本身不是进攻理由，环境档才是仓位的自变量。</div></div>' % D)
idx.append('<div class="card"><p class="mut">最新在上，其余折叠。</p>' + "".join(items) +
           '<details class="chain"><summary><b>完整时间线</b></summary><div class="inner"><p class="mut">见 _学习/认知迭代全量.json</p></div></details></div>')
index_body = "\n".join(idx)

# ---------- cycle body ----------
cy = []
cy.append('<div class="rowA"><div class="hero"><div class="kick">Cycle · 周期情绪 · 截至 11-04 收盘</div>'
          '<h1>阶段：启动 · 方向：升（宽度修复，高度未接力）</h1>'
          '<p>五路周期投票 2 降 / 2 平 / 1 升，主判取「启动·升」；加权反对份额 0.35＜0.60 阈值，当日不复议。</p>'
          '<div class="stance"><span class="pill">攻防 · <b>C 档</b> · 名义 1.5%</span></div></div>'
          '<div class="kpi"><div class="lab">温度</div><div class="big">49.0</div><div class="mut">昨 20.3 · Δ+28.7</div></div>'
          '<div class="kpi"><div class="lab">涨停</div><div class="big">118</div><div class="mut">昨 48</div></div>'
          '<div class="kpi"><div class="lab">炸板率</div><div class="big">22.0%</div><div class="mut">昨 41.5%</div></div>'
          '<div class="kpi"><div class="lab">最高板</div><div class="big">3</div><div class="mut">昨 4</div></div></div>')

cy.append('<h2>一 量能台阶 · 我站在第几档</h2>')
cy.append('<div class="card"><p>两市成交额 <b>20377 亿</b>（昨 17034 亿，+19.6%）。量能台阶口径（近 5 日）：17034 → 20377，回到 2 万亿级；'
          '配套 封板总额 95.4 亿（昨 38.5 亿，+148%）、封板率 78.15%、回封 65 只（昨 21）。<b>量增价不增</b>：'
          '成交放 19.6% 而最高连板从 4 退到 3、封单比中位从 1.219% 掉到 0.35%——放量买的是新宽度，不是老高度。</p>'
          '<div class="ladder"><div class="rung"><span class="lv">冰点收缩 &lt;1.7 万亿</span></div>'
          '<div class="rung high"><span class="lv">当下 2.04 万亿 · 台阶三</span></div>'
          '<div class="rung"><span class="lv">扩张 &gt;2.3 万亿</span></div></div>'
          '<div class="hint">台阶 = 成交额分档；台阶三对应「宽度可扩散、高度不可押」。</div></div>')

cy.append('<h2>二 先行指标 · 三窗触发器</h2>')
cy.append('<div class="card"><table class="p2"><tr><th class="l">先行窗</th><th>读数</th><th>触发</th></tr>'
          '<tr><td class="l">晋级窗：一进二率</td><td>18.2%%（6/33）</td><td class="chip2 c-hit">过 0.15 门，腰部回暖</td></tr>'
          '<tr><td class="l">晋级窗：二进三率</td><td>50.0%%（6/12）</td><td class="chip2 c-hot">高位格仍在，但样本仅 12</td></tr>'
          '<tr><td class="l">高度窗：高度晋级率</td><td>40.0%%</td><td class="chip2 c-warn">未过 0.5，天花板没破</td></tr>'
          '<tr><td class="l">承接窗：昨停溢价</td><td>—</td><td class="chip2 c-warn">标准源取数失败，禁用估算</td></tr>'
          '<tr><td class="l">风险窗：核按钮率</td><td>8.3%%（4/48）</td><td class="chip2 c-warn">从 0 回升，接力端有断层</td></tr>'
          '</table><div class="hint">源：_学习/_情绪先行指标.json#%s。昨停溢价缺失＝取数缺口，非零值。</div></div>' % D)

cy.append('<h2>三 情绪五阶段 · 五路周期投票</h2>')
cy.append('<div class="card"><div class="stages">'
          '<div class="st"><b>冰点</b><div class="mut">10-29/10-30/11-03（11.0/15.2/20.3）</div></div>'
          '<div class="st"><b>启动 ← 今日</b><div class="mut">温度 49.0、涨停 118、炸板率 22.0%</div></div>'
          '<div class="st"><b>发酵</b><div class="mut">未达：最高板仅 3、封单比 0.35%</div></div>'
          '<div class="st"><b>高潮</b><div class="mut">未达</div></div>'
          '<div class="st"><b>退潮</b><div class="mut">未达（炸板率已回落）</div></div></div>'
          '<table class="p2"><tr><th class="l">路</th><th>方向票</th><th>依据（原文数字）</th></tr>'
          '<tr><td class="l">①竞价</td><td>降</td><td>中档 20 池日 −0.51%、中档+涨停≥90 七池日 −1.53%，基准仓 0</td></tr>'
          '<tr><td class="l">②席位</td><td>降</td><td>榜票级净买 −22.21 亿、真实率 −21.11% 连续第二日为负</td></tr>'
          '<tr><td class="l">③题材</td><td>平</td><td>无主流，半导体 34 只为午后扩散（≥13:00 封 91.2%）</td></tr>'
          '<tr><td class="l">④产逻</td><td>平</td><td>真增长 52.5% 但首封≥13:00 占 72.0%</td></tr>'
          '<tr><td class="l">⑤质量</td><td>升</td><td>宽度与封板质量同日修复，机械触发上调 B</td></tr>'
          '</table><div class="hint">主判（宿主合成）：启动 · 升。tally 反对路 2/5、加权反对 0.35＜0.60，不触发复议；连续 3 日 ≥2 路同向亦未达。</div></div>')

cy.append('<h2>四 连板梯队 · 3 板封顶</h2>')
cy.append('<div class="card"><div class="ladder">'
          '<div class="rung high"><span class="lv">3 板 × 6</span><span class="mut">002827/600892/601599/605577/002058/002578</span></div>'
          '<div class="rung"><span class="lv">2 板 × 6</span><span class="mut">二板加 12</span></div>'
          '<div class="rung"><span class="lv">1 板 × 106</span><span class="mut">占 89.8%，首封≥13:00 的 85 只（72.0%）</span></div>'
          '</div><p>梯队结构是「宽底薄顶」：106 只首板撑出宽度，3 板以上一只没有。二板加 12（昨 15）、一进二 18.2%、高度晋级 40.0%——'
          '腰部没断，但向上的每一格都在丢人。历史上 3 板进 4 板封板率 39.4%（n=198），今日 6 只 3 板按独立近似至少 1 只晋级的概率约 95%。</p></div>')

cy.append('<h2>五 攻防 · 仓位总开关</h2>')
cy.append('<div class="card"><div class="posmeter"><div class="lab">名义仓位 1.5%（上限 6%）</div></div>'
          '<p><b>C 档 68 分</b>：002992 宝明科技 1.0% + 688809 强一股份 0.5%，gap 闸门 [−3.0%, +1.5%]，不成交即 0 仓、不递补、不换票；3 板及以上一律 0 权重。</p>'
          '<p>降档依据（环境加权）：中 40~65 档各路历史胜率 limitup 35.0%（8 日 n=40）、auction 35.1%（20 日 n=285）、lhb 38.2%（9 日 n=34）——中档是全员低胜率档。'
          'limitup 的 B 档由自设条款「涨停≥70 且 二板加≥12」机械触发，与其自述「不是接力修复」冲突，故 B→C、2.2%→1.5%。'
          '688809 炸板 6 次（其荐票卡曾记 0）且整手 200 股×223.91≈4.48 万元＝nav 4.49%，超单票 1.0% 上限 → 记「不可执行」，额度不得挪用。</p></div>')

cy.append('<h2>六 自主深挖 · 三条可结算</h2>')
cy.append('<div class="card"><p>①<b>桶冲突规则</b>（theme 承接 MA-20261103-01）：walk-forward n=41，「取正桶」37.8%/−0.07pp、「取最贴合」13.3%/−0.91pp、「取样本量最大」0 次买入 → 立规则「同一票同时落正桶与负桶即不参与」，明日以 002992/688809 是否成交验证。'
          '②<b>形态格与标签正交</b>（limitup 承接 MA-20261103-02）：002652 剔除谐音标签后 n=28/64.3%/+2.229%＞+1%，判形态格不受名称噪声影响；反向条件下次遇「冰点×尾盘首板×换手≥10」需再验。'
          '③<b>低开档下界</b>（自主拓展立项 topic-auction-lowgap-depth-20261104）：低开≤0 档全窗 n=947/45.9%/+0.51%，但近 3 日 3/3 为负，按 ≤−7/−7~−5/−5~−3/−3~0 四段重算，20 交易日内结算。</p></div>')

cy.append('<h2>七 我的认知迭代 · 最新在上</h2>')
cy.append('<div class="card"><div class="tli"><div class="d">%s</div><div class="h">温度跳档不等于环境转好</div>'
          '<div class="b">温度 20.3→49.0 单日 +28.7，落地是「中档」而中档三路历史胜率 35.0%%~38.2%%——比冰点档（−1.21%%/池日）好不了多少。今日 118 涨停落在我最差的交叉（涨停≥90 的 7 池日 −1.53%%），所以基准仓必须是 0 而不是「最小仓」。教训：环境档要用历史档位胜率校准，不要用温度变化方向当进攻信号。</div></div>'
          '<details class="chain"><summary><b>完整时间线</b></summary><div class="inner"><p class="mut">见 _学习/认知迭代全量.json（最新在上）</p></div></details></div>' % D)
cycle_body = "\n".join(cy)

w(os.path.join(L, "index_body_%s.html" % D), index_body)
w(os.path.join(L, "cycle_body_%s.html" % D), cycle_body)

# ---------- 注入 judgment ----------
jp = os.path.join(L, "judgment_%s.json" % D)
j = jl(jp)
bodies = j.get("bodies") or {}
for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    fp = os.path.join(L, "%s_body_%s.html" % (r, D))
    bodies[r] = io.open(fp, encoding="utf-8").read()
bodies["index"] = index_body
bodies["cycle"] = cycle_body
j["bodies"] = bodies
tj = jl(os.path.join(L, "_市场温度表.json"))[D]
j["date"] = D
j["更新label"] = D + " 复盘 · 温度 %.1f · 总裁决 %s 档" % (tj.get("温度", 0), verdict.get("档位", "C"))
j["一句话"] = ("温度49.0（昨20.3）自冰点直跳中性档、涨停118（昨48）炸板率22.0%，但最高仅3板、首封≥13:00占72.0%、"
               "昨停次日执1 −1.99%，宽度换血未回到接力；五路四C一B、总裁决C档68分，明日名义1.5%只做窄口径试探")
j["ticker"] = ("量能 2.04万亿 · 涨停 118 跌停 10 · 炸板率 22.0% · 最高 3 板 · 温度 49.0(昨20.3) · 一进二 18.2% · 二进三 50.0% · "
               "总裁决 C档 名义1.5%")
j["archive_body"] = j.get("archive_body") or ""
with io.open(jp + ".tmp", "w", encoding="utf-8") as f:
    json.dump(j, f, ensure_ascii=False, indent=1)
os.replace(jp + ".tmp", jp)

print("注入完成 bodies:", list(bodies.keys()))
print("index len", len(index_body), "cycle len", len(cycle_body))
print("一句话:", j["一句话"])
