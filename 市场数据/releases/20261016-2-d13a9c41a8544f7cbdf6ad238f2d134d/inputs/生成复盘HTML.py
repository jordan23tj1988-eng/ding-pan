# -*- coding: utf-8 -*-
"""生成复盘HTML.py —— 首页(当日复盘+竞价/龙虎榜候选结果)。自包含离线。
用法: python 生成复盘HTML.py [YYYYMMDD]"""
import sys, os, json, glob, datetime, re, html
BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

def latest(guess):
    for dd in range(0, 10):
        d = (guess - datetime.timedelta(days=dd)).strftime("%Y%m%d")
        if os.path.isfile(os.path.join(BASE, d, "summary.json")): return d
    return None

def score_env(s):
    amt = s.get("两市成交额_亿") or 0; zt = s.get("涨停家数") or 0; dt = s.get("跌停家数") or 0; zb = s.get("炸板率") or 0
    lad = s.get("连板梯队") or {}; b1 = int(lad.get("1", lad.get(1, 0)) or 0); tot = sum(int(v) for v in lad.values()) or 1
    sc = 0; det = []
    if amt >= 35000: sc += 2; det.append(("量能%.0f亿(主升线上)" % amt, 2))
    elif amt >= 32000: det.append(("量能%.0f亿(震荡)" % amt, 0))
    elif amt >= 30000: sc -= 1; det.append(("量能%.0f亿(滞涨)" % amt, -1))
    else: sc -= 2; det.append(("量能%.0f亿(退潮线下)" % amt, -2))
    if zt > 100 and dt < 15: sc += 2; det.append(("涨停%d/跌停%d(强)" % (zt, dt), 2))
    elif dt > 30 or zb > 0.5: sc -= 2; det.append(("涨停%d/跌停%d 炸板率%.0f%%(弱)" % (zt, dt, zb*100), -2))
    else: det.append(("涨停%d/跌停%d(常态)" % (zt, dt), 0))
    if b1/tot > 0.85: sc -= 1; det.append(("1板占%.0f%%(梯队断层)" % (b1/tot*100), -1))
    else: det.append(("连板梯队完整度尚可", 0))
    themes = s.get("涨停行业扎堆Top12") or s.get("涨停行业扎堆Top10") or []
    if themes and themes[0][1] >= 5: sc += 1; det.append(("主线扎堆%s%d家" % (themes[0][0], themes[0][1]), 1))
    else: sc -= 1; det.append(("扎堆分散(混沌)", -1))
    scen = "A·主升" if sc >= 4 else ("C·退潮" if sc <= -3 else "B·震荡")
    return sc, scen, det

def md_light(txt):
    out = []
    for ln in txt.splitlines():
        s = ln.rstrip()
        if not s: out.append("<br>"); continue
        if s.startswith("## "): out.append("<h3>%s</h3>" % html.escape(s[3:]))
        elif s.startswith("# "): continue
        elif s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "): continue
            out.append("<table class=mini><tr>%s</tr></table>" % "".join("<td>%s</td>" % html.escape(c) for c in cells))
        else:
            out.append("<p>%s</p>" % re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(s).replace("&lt;b&gt;","").replace("&lt;/b&gt;","")))
    return "\n".join(out)

def bar(pct, color):
    return "<div class=barwrap><div class=bar style='width:%d%%;background:%s'></div></div>" % (int(pct), color)

def nav():
    it = [("latest.html","🏠 首页"),("学习日记.html","📓 学习笔记"),("集合竞价训练.html","⚡ 集合竞价训练"),("龙虎榜训练.html","🐯 龙虎榜训练")]
    return "<div class=nav>" + "".join("<a class='%s' href='%s'>%s</a>" % ("on" if i==0 else "", h, t) for i,(h,t) in enumerate(it)) + "</div>"

def main():
    guess = datetime.date.today()
    if len(sys.argv) > 1: guess = datetime.datetime.strptime(sys.argv[1], "%Y%m%d").date()
    d = latest(guess)
    if not d: print("无数据"); return
    D = os.path.join(BASE, d)
    s = json.load(open(os.path.join(D, "summary.json"), encoding="utf-8"))
    ana = {}
    if os.path.isfile(os.path.join(D, "analysis.json")):
        try: ana = json.load(open(os.path.join(D, "analysis.json"), encoding="utf-8"))
        except Exception: ana = {}
    gg = {}
    _gp = os.path.join(BASE, "_学习", "公告_%s.json" % d)
    if os.path.isfile(_gp):
        try: gg = json.load(open(_gp, encoding="utf-8"))
        except Exception: gg = {}
    def gtag(code):
        v = gg.get(str(code).zfill(6))
        if not v: return ""
        cls = "t-hi" if v.get("标签")=="利空" else ("t-lo" if v.get("标签")=="存疑" else "t-mid")
        return " <span class='tag %s'>%s</span>" % (cls, v.get("标签",""))
    sc, scen, det = score_env(s)

    H = ["<!doctype html><html lang=zh><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"]
    H.append("<title>复盘 %s</title><style>:root{color-scheme:light}" % d)
    H.append("body{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#f5f6f8;color:#1a1a2e;margin:0;padding:16px;font-size:14px}")
    H.append(".wrap{max-width:1000px;margin:0 auto}.card{background:#fff;border-radius:12px;padding:16px 20px;margin:12px 0;box-shadow:0 1px 4px rgba(0,0,0,.06)}")
    H.append("h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;border-left:4px solid #4361ee;padding-left:8px;margin:6px 0 12px}h3{font-size:14px;margin:10px 0 4px}")
    H.append(".hd{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.badge{padding:3px 10px;border-radius:20px;font-weight:700;color:#fff;font-size:13px}")
    H.append(".b-A{background:#e63946}.b-B{background:#f4a261}.b-C{background:#457b9d}.sc{font-size:30px;font-weight:800}")
    H.append("table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #eee}th{color:#666;background:#fafafa}")
    H.append(".tag{padding:1px 7px;border-radius:6px;font-size:12px;color:#fff}.t-hi{background:#e63946}.t-mid{background:#e9a23b}.t-lo{background:#9aa0a6}")
    H.append(".ty1{color:#e63946;font-weight:600}.ty2{color:#457b9d;font-weight:600}")
    H.append(".barwrap{background:#eee;border-radius:4px;height:9px;width:80px;display:inline-block;vertical-align:middle}.bar{height:9px;border-radius:4px}")
    H.append(".ladder span{display:inline-block;margin:2px 4px;padding:2px 8px;background:#eef;border-radius:6px}.pos{color:#e63946}.neg{color:#2a9d8f}.mut{color:#888;font-size:12px}")
    H.append(".nav{display:flex;gap:8px;margin:0 0 12px;flex-wrap:wrap}.nav a{padding:6px 14px;background:#fff;border:1px solid #dde;border-radius:8px;text-decoration:none;color:#345;font-size:13px;font-weight:600}.nav a.on{background:#4361ee;color:#fff;border-color:#4361ee}")
    H.append("</style></head><body><div class=wrap>")
    H.append(nav())
    H.append("<div class=card><div class=hd><h1>短线复盘 · %s</h1><span class='badge b-%s'>情景 %s</span><span class=sc>%+d</span><span class=mut>环境总分</span></div>" % (d, scen[0], scen, sc))
    H.append("<div class=mut style='margin-top:6px'>" + " ｜ ".join("%s(%+d)" % (t, v) for t, v in det) + "</div></div>")

    # 一 环境
    lad = s.get("连板梯队") or {}
    ladhtml = "".join("<span>%s板×%s</span>" % (k, v) for k, v in sorted(lad.items(), key=lambda x: -int(x[0])))
    H.append("<div class=card><h2>一、环境</h2><table><tr><th>两市量能</th><th>涨停</th><th>跌停</th><th>炸板率</th><th>最高连板</th></tr>")
    H.append("<tr><td><b>%s亿</b></td><td class=pos>%s</td><td class=neg>%s</td><td>%s</td><td>%s</td></tr></table>" % (
        s.get("两市成交额_亿"), s.get("涨停家数"), s.get("跌停家数"), ("%.0f%%" % (s.get("炸板率")*100)) if s.get("炸板率") else "-", s.get("最高连板")))
    H.append("<div class=ladder style='margin-top:8px'><b>连板梯队：</b>%s</div></div>" % ladhtml)

    # 二 题材树
    H.append("<div class=card><h2>二、题材树（核心题材→核心标的）</h2><table><tr><th>题材</th><th>涨停数</th><th>最高板</th><th>连板≥2</th><th>核心标的</th></tr>")
    for t in (ana.get("题材树") or [])[:10]:
        H.append("<tr><td><b>%s</b></td><td>%s</td><td>%s板</td><td>%s</td><td>%s(%s板)</td></tr>" % (
            html.escape(str(t["题材"])), t["涨停数"], t["最高板"], t["连板2plus"], html.escape(str(t["核心标的"])), t["核心连板"]))
    H.append("</table></div>")

    # 三 龙头分
    H.append("<div class=card><h2>三、核心标的 · 龙头分（量化打分，档非真实概率）</h2><table><tr><th>名称</th><th>题材</th><th>类型</th><th>连板</th><th>涨停统计</th><th>龙头分</th><th>档</th></tr>")
    for c in (ana.get("核心标的") or [])[:12]:
        dang = str(c.get("龙头档", "")); tg = "t-hi" if dang == "高" else ("t-mid" if dang == "中" else "t-lo")
        ty = str(c.get("类型", "")); tyc = "ty1" if "情绪" in ty else "ty2"; sco = float(c.get("龙头分", 0))
        col = "#e63946" if dang == "高" else ("#e9a23b" if dang == "中" else "#9aa0a6")
        H.append("<tr><td><b>%s</b></td><td class=mut>%s</td><td class=%s>%s</td><td>%s</td><td>%s</td><td>%.1f %s</td><td><span class='tag %s'>%s</span></td></tr>" % (
            html.escape(str(c.get("名称"))), html.escape(str(c.get("所属行业",""))), tyc, ty, c.get("连板数"), c.get("涨停统计"), sco, bar(sco, col), tg, dang))
    H.append("</table><div class=mut>龙头分=身位30+封单质量25+资金20+题材地位15+席位加成(按胜率库加权)</div></div>")

    # 四 席位动向
    seats = sorted(ana.get("席位动向") or [], key=lambda x: -abs(x.get("净额", 0)))
    H.append("<div class=card><h2>四、席位动向（游资/量化扫描）</h2><table><tr><th>个股</th><th>席位/游资</th><th>类型</th><th>档</th><th>净额万</th></tr>")
    for r in seats[:16]:
        if not (r.get("游资") or r.get("类型") != "其他/未知"): continue
        net = r.get("净额", 0)/1e4; cls = "pos" if net > 0 else "neg"; who = r.get("游资") or str(r.get("营业部", ""))[:14]
        H.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class=%s>%+.0f</td></tr>" % (
            html.escape(str(r.get("名称"))), html.escape(str(who)), html.escape(str(r.get("类型", ""))), r.get("席位档") or "", cls, net))
    H.append("</table></div>")

    # 五 推演
    mdp = os.path.join(BASE, "复盘", d + ".md")
    if os.path.isfile(mdp):
        m = re.search(r"(##[^\n]*推演.*)", open(mdp, encoding="utf-8").read(), re.S)
        if m: H.append("<div class=card><h2>五、推演 & 关注方向</h2>%s</div>" % md_light(m.group(1)))

    # 六 竞价封板候选(结果) —— 训练全表在集合竞价训练页
    tp = os.path.join(BASE, "_竞价训练结果.json")
    if os.path.isfile(tp):
        try: tr = json.load(open(tp, encoding="utf-8"))
        except Exception: tr = {}
        withc = [g for g in (tr.get("黄金组合Top") or []) if g.get("今日符合票")]
        H.append("<div class=card><h2>六、竞价封板候选（明日）</h2>")
        H.append("<div class=mut>条件=T日特征→T+1封板概率(样本≥8)。%s符合组合涨停股=明日候选。训练全表见 <a href='集合竞价训练.html'>⚡集合竞价训练页</a></div>" % tr.get("最新交易日",""))
        H.append("<table><tr><th>T+1封板率</th><th>T日条件</th><th>今日符合票(明日候选)</th></tr>")
        for g in withc[:8]:
            cells = []
            for p in g["今日符合票"]:
                seat = (" · " + html.escape(p["席位"])) if p.get("席位") else ""
                cells.append("<b>%s</b><span class=mut>(%s)龙头分%.0f%s</span>%s" % (html.escape(str(p.get("名称"))), html.escape(str(p.get("题材"))), p.get("龙头分") or 0, seat, gtag(p.get("代码"))))
            H.append("<tr><td class=pos><b>%.0f%%</b></td><td class=mut>%s</td><td>%s</td></tr>" % (g["次日封板率"]*100, html.escape(g["条件"]), "<br>".join(cells)))
        if not withc: H.append("<tr><td colspan=3 class=mut>今日无符合黄金组合的候选</td></tr>")
        H.append("</table></div>")

    # 七 公告面
    if gg:
        H.append("<div class=card><h2>七、公告面异动（候选/龙头近1-2日公告）</h2><table><tr><th>股票</th><th>标签</th><th>公告标题</th></tr>")
        order = {"利空":0,"存疑":1,"利好":2,"中性":3}
        for code, v in sorted(gg.items(), key=lambda kv: order.get(kv[1].get("标签",""),9)):
            cls = "t-hi" if v.get("标签")=="利空" else ("t-lo" if v.get("标签")=="存疑" else "t-mid")
            ttl = (v.get("标题") or [""])[0][:44] if isinstance(v.get("标题"), list) else str(v.get("标题",""))[:44]
            H.append("<tr><td><b>%s</b></td><td><span class='tag %s'>%s</span></td><td class=mut>%s</td></tr>" % (html.escape(str(v.get("名称",""))), cls, v.get("标签",""), html.escape(ttl)))
        H.append("</table></div>")

    H.append("<div class=mut style='text-align:center;margin:16px'>数据源 akshare 免费源 · 本质多头beta，非买卖指令 · 生成于 %s</div>" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    H.append("</div></body></html>")
    OUT = os.path.join(BASE, "复盘"); os.makedirs(OUT, exist_ok=True)
    txt = "\n".join(H)
    for fn in (d + ".html", "latest.html"):
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f: f.write(txt); f.truncate()
    print("生成首页:", d)

if __name__ == "__main__":
    main()
