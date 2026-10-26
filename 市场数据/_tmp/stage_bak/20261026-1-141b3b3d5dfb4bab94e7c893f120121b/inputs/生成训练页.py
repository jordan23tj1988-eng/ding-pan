# -*- coding: utf-8 -*-
"""生成训练页.py —— 第三页(集合竞价训练)+第四页(龙虎榜训练),自包含离线HTML。
读 _竞价训练结果.json / _席位胜率库.json。用法: python 生成训练页.py"""
import os, json, glob, html, datetime
BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE
OUT = os.path.join(BASE, "复盘"); os.makedirs(OUT, exist_ok=True)

CSS = ("<style>:root{color-scheme:light}"
 "body{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#f5f6f8;color:#1a1a2e;margin:0;padding:16px;font-size:14px}"
 ".wrap{max-width:1000px;margin:0 auto}"
 ".card{background:#fff;border-radius:12px;padding:16px 20px;margin:12px 0;box-shadow:0 1px 4px rgba(0,0,0,.06)}"
 "h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;border-left:4px solid #4361ee;padding-left:8px;margin:6px 0 12px}h3{font-size:14px;margin:10px 0 4px;color:#333}"
 "table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #eee}th{color:#666;background:#fafafa}"
 ".pos{color:#e63946;font-weight:600}.mut{color:#888;font-size:12px}"
 ".barwrap{background:#eee;border-radius:4px;height:9px;width:80px;display:inline-block;vertical-align:middle}.bar{height:9px;border-radius:4px}"
 ".tag{padding:1px 7px;border-radius:6px;font-size:12px;color:#fff}.s{background:#e63946}.a{background:#e9a23b}.b{background:#6c8}.c{background:#9aa0a6}"
 ".nav{display:flex;gap:8px;margin:0 0 12px;flex-wrap:wrap}.nav a{padding:6px 14px;background:#fff;border:1px solid #dde;border-radius:8px;text-decoration:none;color:#345;font-size:13px;font-weight:600}.nav a.on{background:#4361ee;color:#fff;border-color:#4361ee}"
 "</style>")

def nav(active):
    items = [("latest.html","🏠 首页"),("学习日记.html","📓 学习笔记"),
             ("集合竞价训练.html","⚡ 集合竞价训练"),("龙虎榜训练.html","🐯 龙虎榜训练")]
    s = "<div class=nav>"
    for href,txt in items:
        s += "<a class='%s' href='%s'>%s</a>" % ("on" if active in href else "", href, txt)
    return s + "</div>"

def bar(pct, color):
    return "<div class=barwrap><div class=bar style='width:%d%%;background:%s'></div></div>" % (min(int(pct),100), color)

def page_auction():
    H = ["<!doctype html><html lang=zh><head><meta charset=utf-8><title>集合竞价训练</title>", CSS,
         "</head><body><div class=wrap>", nav("集合竞价训练"), "<h1>⚡ 集合竞价训练</h1>"]
    tp = os.path.join(BASE, "_竞价训练结果.json")
    if os.path.isfile(tp):
        tr = json.load(open(tp, encoding="utf-8"))
        H.append("<div class=card><div class=mut>窗口 %s · %s样本 · 基准次日封板率 %.1f%% · 条件=T日特征→T+1封板概率</div></div>" % (
            tr.get("窗口"), tr.get("总样本"), (tr.get("基准次日封板率") or 0)*100))
        def rt(title, dd, note=""):
            H.append("<div class=card><h2>%s</h2>" % title)
            if note: H.append("<div class=mut>%s</div>" % note)
            H.append("<table><tr><th>分档</th><th>次日封板率</th><th>样本</th></tr>")
            for k, v in dd.items():
                w = v[0]*100
                col = "#e63946" if w>=35 else ("#e9a23b" if w>=20 else "#9aa0a6")
                H.append("<tr><td>%s</td><td>%s <b>%.1f%%</b></td><td class=mut>%d</td></tr>" % (html.escape(k), bar(w*2 if w<50 else 100, col), w, v[1]))
            H.append("</table></div>")
        rt("按封板时间（越早越强）", tr.get("按封板时间", {}), "竞价一字/秒封=次日封板概率最高")
        rt("按封单强度（封成比=封单/流通市值）", tr.get("按封单强度", {}))
        rt("按连板层", tr.get("按连板层", {}))
        rt("按题材", tr.get("按题材", {}), "反直觉:主线内涨停多、分歧大，次日反易分化")
        # 黄金组合
        H.append("<div class=card><h2>黄金组合 Top（多因子叠加，样本≥8）</h2>")
        H.append("<div class=mut>%s 符合组合的涨停股=明日封板候选(带龙头分/席位)</div>" % tr.get("最新交易日",""))
        H.append("<table><tr><th>T+1封板率</th><th>样本</th><th>T日条件</th><th>今日符合票</th></tr>")
        for g in (tr.get("黄金组合Top") or [])[:12]:
            cells = []
            for p in (g.get("今日符合票") or []):
                if isinstance(p, dict):
                    seat = (" · "+html.escape(p["席位"])) if p.get("席位") else ""
                    cells.append("<b>%s</b><span class=mut>(%s)龙头分%.0f%s</span>" % (html.escape(str(p.get("名称"))), html.escape(str(p.get("题材"))), p.get("龙头分") or 0, seat))
            picks = "<br>".join(cells) or "<span class=mut>无</span>"
            H.append("<tr><td class=pos><b>%.0f%%</b></td><td>%d</td><td class=mut>%s</td><td>%s</td></tr>" % (g["次日封板率"]*100, g["样本"], html.escape(g["条件"]), picks))
        H.append("</table></div>")
    # 深度竞价(9:25前动态)——诚实说明+累积
    H.append("<div class=card><h2>★竞价盘口深度（9:25前 涨幅/量比 → T日涨停+隔日溢价）</h2>")
    H.append("<div class=mut>免费源(akshare)无历史竞价tick，此维度靠早盘9:40任务每天抓竞价快照<b>逐日累积</b>，样本够(≥60天)后自动出'竞价高开/量比→当日涨停率、隔日溢价率'的分档统计。当前累积中，未够不硬编。</div>")
    # 列出已累积的竞价快照天数
    snaps = sorted(glob.glob(os.path.join(BASE, "*", "竞价快照.csv")))
    H.append("<div class=mut style='margin-top:6px'>已累积竞价快照：<b>%d</b> 个交易日</div>" % len(snaps))
    H.append("</div>")
    H.append("<div class=mut style='text-align:center;margin:16px'>数据源 akshare · 非买卖指令 · 生成于 %s</div>" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    H.append("</div></body></html>")
    open(os.path.join(OUT, "集合竞价训练.html"), "w", encoding="utf-8").write("\n".join(H))
    print("生成 集合竞价训练.html")

def page_lhb():
    H = ["<!doctype html><html lang=zh><head><meta charset=utf-8><title>龙虎榜训练</title>", CSS,
         "</head><body><div class=wrap>", nav("龙虎榜训练"), "<h1>🐯 龙虎榜训练</h1>"]
    lp = os.path.join(BASE, "_席位胜率库.json")
    if os.path.isfile(lp):
        lib = json.load(open(lp, encoding="utf-8"))
        for win in ("近三月", "近一月"):
            d = lib.get(win, {})
            if not d: continue
            rows = [dict(名称=k, **v) for k, v in d.items()]
            # 米氏席位
            mi = sorted([r for r in rows if r.get("米氏")], key=lambda x: -(x["涨幅"]*x["胜率"]))
            H.append("<div class=card><h2>米氏手册席位 · 实测表现（%s，上榜后1天）</h2>" % win)
            H.append("<table><tr><th>席位</th><th>营业部</th><th>涨幅</th><th>胜率</th><th>次数</th><th>档</th></tr>")
            for r in mi:
                dc = {"S":"s","A":"a","B":"b"}.get(str(r.get("档","")).replace("(慎跟)",""), "c")
                H.append("<tr><td><b>%s</b></td><td class=mut>%s</td><td class=pos>%+.2f%%</td><td>%.0f%%</td><td class=mut>%d</td><td><span class='tag %s'>%s</span></td></tr>" % (
                    html.escape(str(r["米氏"])), html.escape(str(r["名称"])), r["涨幅"], r["胜率"], r["次数"], dc, r.get("档","")))
            H.append("</table></div>")
            if win == "近三月":
                top = sorted([r for r in rows if r.get("档") in ("S","A")], key=lambda x: -(x["涨幅"]*x["胜率"]))[:20]
                H.append("<div class=card><h2>经验最强席位 S/A档 Top20（数据发现，手册外）</h2>")
                H.append("<table><tr><th>营业部</th><th>涨幅</th><th>胜率</th><th>次数</th><th>档</th></tr>")
                for r in top:
                    dc = {"S":"s","A":"a"}.get(str(r.get("档","")), "b")
                    H.append("<tr><td>%s</td><td class=pos>%+.2f%%</td><td>%.0f%%</td><td class=mut>%d</td><td><span class='tag %s'>%s</span></td></tr>" % (
                        html.escape(str(r["名称"])), r["涨幅"], r["胜率"], r["次数"], dc, r["档"]))
                H.append("</table></div>")
    H.append("<div class=card><h2>资金五性质 + 跟法</h2><div class=mut>"
             "①机构专用(证金/社保/公募,价投趋势) ②北向(外资/GJD,价投) ③量化席位(开源系太华路/成章路等,套利,1字板不接) "
             "④游资(章盟主/欢乐海岸等,造龙) ⑤散户(家人榜,东财)。<br>跟法:S/A档净买入=加分信号;C档(西大街48%≈抛硬币)别当强信号;"
             "异动红线(10天100%/30天200%)外无量化身影→主控是游资。买力卖力净差>最大值一半、五档均匀、家人越少越好。</div></div>")
    H.append("<div class=mut style='text-align:center;margin:16px'>数据源 akshare 营业部上榜后表现 · 每日刷新 · 生成于 %s</div>" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    H.append("</div></body></html>")
    open(os.path.join(OUT, "龙虎榜训练.html"), "w", encoding="utf-8").write("\n".join(H))
    print("生成 龙虎榜训练.html")

if __name__ == "__main__":
    page_auction(); page_lhb()
