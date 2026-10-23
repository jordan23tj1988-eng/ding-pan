# -*- coding: utf-8 -*-
"""生成 _学习/logic_body_20261023.html（六板块，h2 延续 20261021/20261022 锚点）"""
import json
import os

BASE = r"D:/股票数据/市场数据"
D = "20261023"
J = json.load(open(os.path.join(BASE, "_学习", "logic判断_%s.json" % D), encoding="utf-8"))
P = J["判断"]
R = J["荐票"]
pur = json.load(open(os.path.join(BASE, "_学习", "卡位纯度_%s.json" % D), encoding="utf-8"))
bkt = {b["桶"]: b for b in json.load(open(os.path.join(BASE, "_学习", "身位分桶_%s.json" % D), encoding="utf-8"))["分桶"]}
pos = json.load(open(os.path.join(BASE, "_学习", "_位置37_%s.json" % D), encoding="utf-8"))
rows = pur["机器人涨停"]
S = pur["汇总"]

NODE_ORDER = ["谐波减速器", "行星滚柱丝杠", "无框力矩/空心杯电机", "灵巧手传动", "六维力传感器",
              "本体/集成", "具身大模型", "伺服驱动/运动控制(相邻)", "微特电机/电机组件(相邻)", "机器视觉(相邻)"]
node_hits = {n: [] for n in NODE_ORDER}
for r in rows:
    for n in (r["链上节点"] or []):
        node_hits.setdefault(n, []).append(r)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def node_row(n):
    lst = node_hits.get(n, [])
    real = [r for r in lst if (r["purity"] or 0) >= 50]
    names = "、".join("%s%s%%" % (r["名称"], r["purity"]) for r in sorted(lst, key=lambda x: -(x["purity"] or 0))) or "—"
    strict = "模板" if not n.endswith("(相邻)") and lst else ("相邻" if n.endswith("(相邻)") else "模板")
    if not lst:
        verdict = "零票（连续第3日）" if n in ("谐波减速器", "行星滚柱丝杠", "六维力传感器") else "零票"
    elif len(real) >= 2:
        verdict = "★同节点≥2只纯度≥50%"
    elif real:
        verdict = "单只卡位"
    else:
        verdict = "仅零星收入"
    return ("<tr><td>%s <span class=\"chip\">%s</span></td><td class=\"num\">%d</td><td class=\"num\"><b>%d</b></td>"
            "<td>%s</td><td class=\"mut\">%s</td></tr>" % (esc(n), strict, len(lst), len(real), esc(names), esc(verdict)))


def stock_row(r):
    top = ""
    if r.get("items"):
        it = sorted(r["items"], key=lambda x: -(x.get("占比pct") or 0))[0]
        top = "%s %s%%" % (it["分项"], it.get("占比pct"))
    pur_v = r["purity"]
    chip = "真卡位" if r["真卡位"] else ("部分" if pur_v else "贴标")
    p = pos.get(r["代码"]) or {}
    r20 = p.get("r20")
    r20s = "%+.1f%%" % r20 if isinstance(r20, (int, float)) else "—"
    return ("<tr><td>%s<br><span class=\"mut\">%s</span></td><td>%s</td><td class=\"num\"><b>%.2f%%</b></td>"
            "<td class=\"num\">%s</td><td class=\"num\">%s板</td><td class=\"num\">%s%%</td><td class=\"num\">%s</td>"
            "<td class=\"num\">%s</td><td><span class=\"chip\">%s</span></td></tr>"
            % (esc(r["名称"]), esc(r["代码"]), esc(top), pur_v, "模板" if r.get("strict_template") else ("相邻" if pur_v else "链外"),
               r.get("连板数"), r.get("封单比pct"), r.get("炸板"), r20s, chip))


def kpi(v, k, s):
    return "<div class=\"kpi-card\"><div class=\"num\"><b>%s</b></div><div>%s</div><div class=\"mut\">%s</div></div>" % (v, k, s)


def bkt_line(key):
    b = bkt.get(key) or {}
    if not b.get("n"):
        return "n=0"
    return "n=%d、胜率%.1f%%、均收%+.2f%%" % (b["n"], b["胜率pct"], b["均收pct"])


H = []
H.append('<div class="logic-body">')
H.append("")
H.append(
    '<div class="hero"><div class="kick">产业逻辑路｜目标日 20261023｜独立判断</div>'
    "<h1>宽度真扩散、纯度反向稀释：机器人涨停 13→37 只、6/6 主流候选，但主营真在链上的只有 6 只＝16.22%（昨 23.1%）——"
    "档位 B（63）、荐票 2 只合计 5.16%、在持 600487 持有不动</h1>"
    "<p>今日最容易被误读的一天：37 只机器人涨停、占涨停池 45.1%、主流题材6有第一次满分，表面是主线确立；"
    "但把 37 只逐只拉东财F10主营构成（37/37覆盖）后，86.5% 的票主营与机器人链零交集，收钱环节从昨日的『电机』移到『本体/集成』，"
    "而卡位最深的减速器/丝杠/六维力三节点连续第3日零票。业绩腿同时开张（三季报池∩涨停 0→3），但三交叉（∩模板）仍是 0 —— 宽度给了分，纯度与交叉拿走了分。</p></div>"
)

H.append(
    '<div class="card insight-card"><b>洞察(agent)：</b>'
    "①<b>纯度被宽度稀释，不是被宽度证实</b>：真卡位从 3 只涨到 6 只（分子翻倍），但分母从 13 涨到 37，占比 23.08%→16.22%（-6.86pp）；"
    "我昨日写的可证伪条件用『≥2只主营在链上』这种计数写法，今日被小分母击穿而字面触发——这是口径缺陷，已写进认知迭代①（此后一律『占比∧绝对数』双阈值）。"
    "②<b>收钱环节第一次换到本体</b>：本体/集成 3 只（宇树98.23%、埃斯顿82.96%、科远3.18%）是本日唯一同节点≥2只且2只≥50%的节点，"
    "毛利也说明问题——宇树本体毛利 63.18% 是全链最高，而华阳微特电机只有 16.26%、雷赛伺服 28.97%，"
    "资金今天买的是『卖整机的』，不是『做零件的』。"
    "③<b>业绩腿开张但没接上链条</b>：三季报池 124 只∩涨停 3 只（理工能科/雷赛/恩捷），全部公告日≥20261001＝新窗口（日龄8~10天），"
    "这是连续两日归零后第一次开张；但三只都不在模板155只内，三交叉＝0，按 20261019 的纪律不能写『业绩驱动主线』，档位不上A。"
    "④<b>纯度门槛第一次拿到真实结算</b>：纯度≥50%∧涨停 子集 n=16、胜率50.0%、执1均收+1.28%，全池同期 -0.47%（+1.75pp）；"
    "更硬的是昨日判真卡位3只今日执1 +7.92%/+11.72%/+12.17%——但资金封单仍不区分纯度（真卡位封单比中位0.871% ≈ 非真卡位0.895%），"
    "所以纯度只用来选票、不用来加权。</div>"
)

H.append('<div class="card kpis">')
H.append(kpi("37 / 82", "机器人涨停 ÷ 涨停池", "45.1%（昨 13/33＝39.4%）；5日宽度 9→18→4→13→37"))
H.append(kpi("%.2f%%" % S["真卡位占比pct"], "卡位纯度（主营占比≥50%）", "6 / 37 只；昨 3/13＝23.08%，-6.86pp；严格模板 3/37＝8.11%"))
H.append(kpi("3 只", "三季报池 ∩ 涨停", "序列 2/2/0/0→3；但∩模板＝0（三交叉）"))
H.append(kpi("B · 63", "档位 · 置信度", "昨 B·58；宽度+业绩腿给分，纯度稀释+三交叉0 压档"))
H.append("</div>")

# ---------------- 一 ----------------
H.append("<h2>一 产业逻辑总判 · 档位B与荐票2</h2>")
H.append('<div class="card"><p>%s</p></div>' % esc(P["结论"]))

H.append('<div class="card"><table>')
H.append("<tr><th>标的</th><th>类型</th><th>环节 / 纯度</th><th>权重</th><th>一句话依据</th></tr>")
H.append(
    "<tr><td><b>002979 雷赛智能</b></td><td><span class=\"chip\">荐票</span></td>"
    "<td>伺服驱动/运动控制（相邻）· <b>53.02%</b></td><td class=\"num\">2.13%（400股）</td>"
    "<td>三季报预增70~90%（公告10-15、日龄8天、订单量增型）＋伺服主营53.02%＋首板14:15炸0；r20 -0.2% 洼地；"
    "纯度子集 n=16/50.0%/+1.28%、首板子集 57.1%/+1.97%；扣分：自身同型 n=3 均值为负</td></tr>"
)
H.append(
    "<tr><td><b>688836 宇树科技-W</b></td><td><span class=\"chip\">荐票</span></td>"
    "<td>本体/集成（模板）· <b>98.23%</b></td><td class=\"num\">3.02%（200股·科创板最小）</td>"
    "<td>全池唯一『收入就是机器人』（人形51.07%+四足41.05%+组件6.10%），本体毛利63.18%全链最高；"
    "20cm首板∧晚封 n=44/65.9%/+3.21%；扣分：换手28.08%（换手≥25桶 47.8%/+0.17）、中报业绩70天旧窗口</td></tr>"
)
H.append(
    "<tr><td><b>002747 埃斯顿</b></td><td><span class=\"chip\">观察</span></td>"
    "<td>本体/集成（模板）· <b>100.00%</b></td><td class=\"num\">0%（不进结算）</td>"
    "<td>唯一100%纯度且在模板内；但中报公告100天旧窗口、原因为降本而非订单、封单比0.417%（第32/37）、流通228.87亿最大 → 只观察</td></tr>"
)
H.append("</table></div>")

H.append('<div class="card"><table>')
H.append("<tr><th>仓位与纪律</th><th>数值</th><th>说明</th></tr>")
H.append("<tr><td>今日新仓</td><td class=\"num\"><b>5.16%</b></td><td>52,300 元（雷赛21,660＋宇树30,640），现金余 909,855.37 元</td></tr>")
H.append("<tr><td>在持仓位</td><td class=\"num\">5.00%</td><td>600487 亨通光电 1000股、成本50.00、今收52.32（+4.64%）→ 持有不动</td></tr>")
H.append("<tr><td>总仓位</td><td class=\"num\">≈10.2%</td><td>B档上限：单票≤3%、总额≤11%；本路历史 n=17笔/胜率29.4%/均收-1.37% ＝不满额</td></tr>")
H.append("<tr><td>弃单纪律</td><td class=\"num\">硬闸门</td><td>雷赛 gap∈[0,+4]%∧30分钟额≥2.0亿∧最低≥52.53；宇树 gap∈[0,+6]%∧30分钟额≥8.0亿∧最低≥148.60；不过闸门＝不执行、不回填</td></tr>")
H.append("</table></div>")

# ---------------- 二 ----------------
H.append("<h2>二 链条纵深 · 模板∩涨停4只 与 37只卡位纯度重排</h2>")
H.append(
    '<div class="card"><p>产业链模板155只 ∩ 82只涨停＝<b>4 只</b>（002747埃斯顿·本体、003021兆威·灵巧手传动、002241歌尔·声学器件[AI硬件链]、'
    "300369·AI算力末端）；机器人链内模板∩37＝3只；模板覆盖 4/82＝4.9%。"
    "节点分布见下表——<b>本体/集成是唯一『同节点≥2只且2只纯度≥50%』的节点</b>，"
    "而谐波减速器、行星滚柱丝杠、六维力传感器连续第3日零票：资金在本体端付钱，不在最深的零件端付钱。</p></div>"
)
H.append('<div class="card"><table>')
H.append("<tr><th>链条节点</th><th>今日涨停</th><th>其中纯度≥50%</th><th>代表票（纯度%）</th><th>判读</th></tr>")
for n in NODE_ORDER:
    H.append(node_row(n))
H.append('<tr><td>链外（主营与机器人无关）</td><td class="num">30</td><td class="num"><b>0</b></td>'
         '<td class="mut">赛福天(光伏电池片50.52%)、林州重机(煤炭机械86.69%)、正裕工业(汽车悬架72.43%)、襄阳轴承(轴承83.68%)、大业股份(钢帘线48.26%)…</td>'
         '<td class="mut">81.1%＝贴标；6板龙头大业股份就在这里</td></tr>')
H.append("</table></div>")

H.append('<div class="card"><details><summary><b>37 只逐只卡位纯度重排（点开）</b>　'
         "口径：纯度＝F10主营构成中机器人链节点收入占比合计；填≥50% 判『真卡位』</summary>"
         '<table><tr><th>名称 / 代码</th><th>主营第一项</th><th>纯度</th><th>节点</th><th>连板</th><th>封单比</th><th>炸板</th><th>r20</th><th>判定</th></tr>')
for r in sorted(rows, key=lambda x: (-(x["purity"] or 0), -(x.get("封单比pct") or 0))):
    H.append(stock_row(r))
H.append("</table></details></div>")

H.append('<div class="card"><table>')
H.append("<tr><th>真卡位 6 只 · 主营构成逐项</th><th>链条节点</th><th>纯度</th><th>四维（板/封单比/炸/换手）</th></tr>")
for r in sorted([x for x in rows if x["真卡位"]], key=lambda x: -x["purity"]):
    items = "＋".join("%s %.2f%%(毛利%s)" % (i["分项"], i["占比pct"], i.get("毛利率pct")) for i in r["items"][:3] if (i.get("占比pct") or 0) > 0.5)
    H.append("<tr><td><b>%s</b> %s</td><td>%s</td><td class=\"num\"><b>%.2f%%</b></td><td class=\"mut\">%s板 / %s%% / %s / %s%%</td></tr>"
             % (esc(r["名称"]), items, esc("、".join(r["链上节点"])), r["purity"], r.get("连板数"), r.get("封单比pct"), r.get("炸板"), r.get("换手pct")))
H.append("</table></div>")

# ---------------- 三 ----------------
H.append("<h2>三 中报与三季报双窗口 · 业绩腿</h2>")
H.append('<div class="card"><table>')
H.append("<tr><th>窗口（报告期）</th><th>池大小</th><th>∩82只涨停</th><th>∩模板155</th><th>三交叉</th><th>判读</th></tr>")
H.append("<tr><td>中报 20260630（雷达）</td><td class=\"num\">800</td><td class=\"num\">A共振0 / 概念叠加0 / 纯增0 / 刚点火<b>8</b></td><td class=\"num\">—</td>"
         "<td class=\"num\">0</td><td class=\"mut\">雷达『机器人/人形类』99只∩37只机器人涨停＝0：今日37只全不是中报预增票</td></tr>")
H.append("<tr><td>三季报 20260930（新窗口）</td><td class=\"num\">124</td><td class=\"num\"><b>3</b></td><td class=\"num\">0</td><td class=\"num\"><b>0</b></td>"
         "<td class=\"mut\">理工能科(10-13)、雷赛(10-15)、恩捷(10-14)：公告日均≥20261001＝新窗口，但全在模板外</td></tr>")
H.append("</table></div>")

H.append('<div class="card"><p><b>三季报池日序列（MA-20261022-04③ 已补至5日）</b>：20261019→20261023 ＝ 2 / 2 / 0 / 0 / <b>3</b>；'
         "池大小 110→113→122→124（公告累计），主营驱动只数 86/124＝69.4%、含非经常词 21 只（17%）。"
         "今日三只命中："
         "<b>002322 理工能科</b>（软件开发，公告2026-10-13）＝软件与信息化板块增长；"
         "<b>002979 雷赛智能</b>（自动化设备，2026-10-15）＝预增70%~90%，营收18.86~19.51亿(+45%~50%)、Q3单季6.34~6.75亿(+55%~65%)，原因原文『订单情况有较大好转』＋『半导体、高端机床、<b>泛人形机器人</b>等重点战略性行业…收入贡献逐步提升』＝订单量增型；"
         "<b>002812 恩捷股份</b>（电池，2026-10-14）＝隔膜量价齐升、扭亏。"
         "★纪律：三只均不在产业链模板155只内，<b>三交叉＝0</b>，按本路 20261019 认知只能记『公告级孤点＋题材线』，不得写『业绩驱动主线』，档位不上A。</p></div>")

H.append('<div class="card"><p><b>为什么业绩腿只给了分、没给档位</b>：三季报∩涨停从 0→3 是真进步（序列首次出现非零），'
         "但三条腿要同时立住才算业绩腿回归——①命中只数 ②公告日龄中位数 ③当期主营驱动只数。今日②日龄中位 8.5 天（三只 8/10/13 天）达标、③三只里主营驱动 3/3 达标，"
         "唯独『业绩→链条→同环节第二只』这条路一次没走通（∩模板＝0、无同环节第二只）。"
         "所以记『业绩开张、链条未承载』，档位停在B。</p></div>")

# ---------------- 四 ----------------
H.append("<h2>四 风险日历 · 踩窗与可执行性过滤</h2>")
H.append('<div class="card"><table>')
H.append("<tr><th>负面项</th><th>口径/规模</th><th>对今日候选的结果</th></tr>")
H.append("<tr><td>风险日历 20261023</td><td class=\"num\">status=pass · <b>774</b> 事件</td>"
         "<td>限售解禁8／分红除权42／股东减持352／高管减持372（减持窗口20260923~20261023）；对 002979/688836/002747/600487 逐码匹配 <b>命中0条</b></td></tr>")
H.append("<tr><td>中报雷达 × 三季报池 交叉冲突</td><td class=\"num\">四池∩82＝8（刚点火）</td>"
         "<td>无冲突票：雷达候选与今日涨停几乎零交集（A共振0/概念0/纯增0），002747只在『刚点火』且在观察不当仓；<b>无一只候选同时出现在两个相反状态桶</b></td></tr>")
H.append("<tr><td>未接入维度（不得声称『无风险』）</td><td class=\"num\">4 类缺失</td>"
         "<td>财报披露日历／股东大会／业绩预告／首发限售解禁；<b>688836 宇树为 2026-08-19 上市次新（bars 42根），其解禁窗口本日历无覆盖＝无法评估，不是无风险</b></td></tr>")
H.append("</table></div>")

H.append('<div class="card"><table>')
H.append("<tr><th>可执行性（身位桶，执1＝T+1开盘买→收盘卖）</th><th>历史 n</th><th>胜率</th><th>均收</th><th>本日对应票</th></tr>")
H.append("<tr><td>20cm首板∧晚封≥14:00</td><td class=\"num\">44</td><td class=\"num\">65.9%</td><td class=\"num\">+3.21%</td><td>688836 宇树（正桶）</td></tr>")
H.append("<tr><td>20cm首板∧换手≥25</td><td class=\"num\">46</td><td class=\"num\">47.8%</td><td class=\"num\">+0.17%</td><td>688836 宇树（换手28.08%＝≈0 edge）</td></tr>")
H.append("<tr><td>首板∧晚封∧封单比≥1.5%</td><td class=\"num\">40</td><td class=\"num\">40.0%</td><td class=\"num\">-1.40%</td><td>688836 宇树（2.154%＝负桶，已如实并列）</td></tr>")
H.append("<tr><td>首板∧换手≥8∧晚封</td><td class=\"num\">146</td><td class=\"num\">51.4%</td><td class=\"num\">+0.30%</td><td>002979 雷赛（换手8.81%）</td></tr>")
H.append("<tr><td>首板∧晚封∧封单比≥1%</td><td class=\"num\">76</td><td class=\"num\">43.4%</td><td class=\"num\">-0.53%</td><td>002979 雷赛（1.081%＝负桶）</td></tr>")
H.append("<tr><td>2板∧封单比≥2%</td><td class=\"num\">138</td><td class=\"num\">21.0%</td><td class=\"num\">-1.57%</td><td>301502 华阳（4.519%）→ 因此不买</td></tr>")
H.append("<tr><td>2板∧早封≤10:00</td><td class=\"num\">447</td><td class=\"num\">34.7%</td><td class=\"num\">-1.18%</td><td>003021 兆威、301502 华阳 → 因此不追</td></tr>")
H.append("<tr><td>全池基准</td><td class=\"num\">4783</td><td class=\"num\">41.5%</td><td class=\"num\">-0.47%</td><td>—</td></tr>")
H.append("</table></div>")

# ---------------- 五 ----------------
H.append("<h2>五 深挖 · 承接Master指派与线索验证</h2>")
for item in J["深挖"]:
    H.append('<div class="card"><p><b>%s｜%s</b></p><p>%s</p></div>'
             % (esc(item["承接"]), esc(item["任务"]), esc(item["结论"])))

# ---------------- 六 ----------------
H.append("<h2>六 认知迭代</h2>")
H.append('<div class="card">')
for i, c in enumerate(J["认知迭代"], 1):
    H.append('<div class="trow"><div class="tr1"><span class="tnm">%d %s</span>'
             '<span class="tjd tj-branch">%s</span><span class="tct">本路认知库 · 待入库</span></div>'
             '<div class="tds">%s</div><div class="hint">可证伪：%s</div></div>'
             % (i, esc(c["标题"]), esc(c["标题"]), esc(c["正文"]), esc(c["可证伪条件"])))
H.append("</div>")

H.append('<div class="card warn"><b>独立盲区声明：</b>%s</div>' % esc(P["独立盲区声明"]))
H.append('<div class="card"><b>可证伪条件（次日机械化验证）：</b><ol>%s</ol></div>'
         % "".join("<li>%s</li>" % esc(x) for x in P["可证伪条件"]))
H.append("<!--LEDGER-->")
H.append('<div class="ledger-note mut">荐票结算锚：本日同时点荐票 002979 雷赛智能（400股/54.15）、688836 宇树科技-W（200股/153.20）与观察票 002747 埃斯顿（0权重、不进结算）；'
         "执1＝T+1开盘买→T+1收盘卖，闸门不过记『不可执行』不计入执行均收。在持 600487 亨通光电 1000股/成本50.00 今日不卖。</div>")
H.append("<!--/LEDGER-->")
H.append("</div>")

html = "\r\n".join(H) + "\r\n"
p = os.path.join(BASE, "_学习", "logic_body_%s.html" % D)
open(p, "w", encoding="utf-8", newline="").write(html)
print("WROTE", p, os.path.getsize(p), "chars", len(html))
print("div open", html.count("<div"), "close", html.count("</div>"))
print("h2", html.count("<h2>"), "table open", html.count("<table"), html.count("</table>"))
print("LEDGER pair", html.count("<!--LEDGER-->"), html.count("<!--/LEDGER-->"))
print("null/None", html.count("null"), html.count("None"))
