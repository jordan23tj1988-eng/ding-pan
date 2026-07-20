# -*- coding: utf-8 -*-
"""生成作战台.py — 盘中作战台页面渲染器 v2(总表式, 2026-07-18 #024, 设计=升级设计稿v1.8 §2.2)
v2: 大卡平铺→作战总表(每票一行,可展开五要素卡)——按用户实测规模(入册20-25只)重构;
    竞价盘点并入行内chip+顶部小结,不再单列重复。
输入: 盘中/{d}/warboard.json  输出: 复盘/盯盘台/intraday.html (60秒自刷)
用法: python 生成作战台.py {YYYYMMDD} [--src path]
"""
import os, sys, json, glob, html, datetime

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE
E = lambda x: html.escape(str(x if x is not None else ""))

ST = {"待触发": ("待触发", "pend"), "已成交": ("已成交", "fill"), "已放弃": ("已放弃", "drop"),
      "持有中": ("持有中", "hold"), "已卖出": ("已卖出", "sold"), "卖出顺延": ("顺延", "defer"),
      "观察": ("观察", "watch")}
OPEN_ST = {"已成交", "持有中", "卖出顺延", "观察"}   # 默认展开
SRC_CLS = {"竞价": "b-auc", "席位": "b-lhb", "题材": "b-thm", "逻辑": "b-lgc", "质量": "b-qlt",
           "总": "b-mst", "竞价场新增": "b-new", "心跳新增": "b-new"}
VD = {"符合预案": ("符合", "v-ok"), "恶化": ("恶化", "v-bad"), "超预期": ("超预期", "v-good")}

def chg_cls(v):
    try: v = float(v)
    except Exception: return "mut"
    return "up" if v > 0 else ("dn" if v < 0 else "mut")

def fpct(v):
    try: return "%+.2f%%" % float(v)
    except Exception: return "—"

def next_action(c):
    st = c.get("status")
    if st == "待触发": return "等: " + (c.get("trigger") or "—")
    if st == "观察": return "等: " + (c.get("trigger") or "观察条件未设")
    if st == "已成交":
        f = c.get("fill") or {}
        return "✓%s ¥%s · 盯卖: %s" % (f.get("time", ""), f.get("px", ""), (c.get("sell") or "晚间表态"))
    if st == "持有中": return "盯卖: " + (c.get("sell") or "晚间表态")
    if st == "卖出顺延": return "⏸ " + ((c.get("fill") or {}).get("rule") or "跌停封死,挂单顺延")
    if st == "已卖出":
        f = c.get("fill") or {}
        return "✓%s 卖 ¥%s · %s" % (f.get("time", ""), f.get("px", ""), f.get("rule", ""))
    if st == "已放弃": return "✕ " + ((c.get("fill") or {}).get("rule") or c.get("abort") or "")
    return ""

def row_html(c):
    st, cls = ST.get(c.get("status", "待触发"), ("?", "pend"))
    au = c.get("auction") or {}
    vtxt, vcls = VD.get(au.get("verdict"), ("—", "v-na"))
    auc = '<span class="mono %s">%s</span><b class="vch %s">%s</b>' % (
        chg_cls(au.get("gap_pct")), fpct(au.get("gap_pct")) if au else "—", vcls, vtxt)
    srcs = "".join('<b class="src %s">%s</b>' % (SRC_CLS.get(s, "b-mst"), E(s)) for s in (c.get("sources") or ["?"]))
    hold = c.get("hold") or {}
    pnl = '<span class="mono %s">%s</span>' % (chg_cls(hold.get("pnl_pct")), fpct(hold.get("pnl_pct"))) if hold else '<span class="mut">—</span>'
    # 展开体: 五要素+盖章+时间线
    fill = c.get("fill") or {}
    stamp = ""
    if c.get("status") in ("已成交", "已卖出") and fill:
        verb = "成交" if c["status"] == "已成交" else "卖出"
        scls = "s-fill" if c["status"] == "已成交" else "s-sold"
        bt = ("·分%s批" % fill["batches"]) if fill.get("batches", 1) > 1 else ""
        stamp = '<div class="stamp %s">✓ %s %s ¥%s <span>· %s%s</span></div>' % (scls, E(fill.get("time")), verb, E(fill.get("px")), E(fill.get("rule")), bt)
    elif c.get("status") == "卖出顺延" and fill:
        stamp = '<div class="stamp s-defer">⏸ %s %s</div>' % (E(fill.get("time")), E(fill.get("rule") or "跌停封死·顺延"))
    elif c.get("status") == "已放弃" and fill:
        stamp = '<div class="stamp s-drop">✕ %s 弃单 <span>· %s</span></div>' % (E(fill.get("time")), E(fill.get("rule")))
    plan = "".join('<div class="pr"><span class="prl">%s</span><span class="prv%s">%s</span></div>' % (
        lab, "" if c.get(k) else " mut", E(c.get(k) or "—"))
        for lab, k in (("为什么选", "why"), ("成交条件", "trigger"), ("不成交条件", "abort"), ("卖出条件", "sell")))
    if au.get("note"):
        plan = '<div class="pr"><span class="prl">竞价盘点</span><span class="prv">%s</span></div>' % E(au["note"]) + plan
    tl = "".join('<div class="tli"><span class="tlt">%s</span><span class="tld">%s</span></div>' % (E(t), E(x))
                 for t, x in (c.get("timeline") or [])[-6:])
    dayage = (" <i class='age'>⚠%s日</i>" % hold["days"]) if (hold.get("days") or 0) >= 3 else ""
    return ('<details class="trw st-%s"%s data-k="%s"><summary><span class="dot %s"></span>'
            '<span class="nm"><b>%s</b> <span class="mut mono">%s</span></span>'
            '<span class="thmc">%s</span>'
            '<span class="srcs">%s</span>'
            '<span class="pxc mono %s">%s</span><span class="mono %s chgc">%s</span>'
            '<span class="aucc">%s</span><span class="pnlc">%s%s</span>'
            '<b class="stb %s">%s</b><span class="nxt">%s</span></summary>'
            '<div class="body">%s%s<div class="tlbox"><div class="tlh">时间线</div>%s</div></div></details>') % (
        cls, " open" if c.get("status") in OPEN_ST else "", E(str(c.get("code", "")) + "|" + str(c.get("status", ""))), cls,
        E(c.get("name")), E(c.get("code")),
        ('<i class="thm">%s</i>' % E(c["theme"])) if c.get("theme") else '<i class="thm mutth">—</i>', srcs,
        chg_cls(c.get("chg_pct")), E(c.get("px", "—")), chg_cls(c.get("chg_pct")), fpct(c.get("chg_pct")),
        auc, pnl, dayage, cls, st, E(next_action(c)), stamp, plan, tl or '<div class="mut">—</div>')

def hero_html(j):
    """昨夜判断→盘中回应 横幅。j=warboard['judgment']"""
    if not j: return ""
    VC = {"成立": "j-ok", "部分成立": "j-mid", "存疑": "j-mid", "背离预警": "j-bad", "验证中": "j-wait"}
    checks = ""
    for c in (j.get("checks") or [])[:4]:
        ok = c.get("ok")
        ic, cls = ("✓", "c-ok") if ok else (("✕", "c-bad") if ok is False else ("…", "c-wait"))
        checks += ('<div class="jck"><span class="%s">%s</span><span class="jcn">%s</span>'
                   '<span class="mono jcv">%s</span><span class="mut jce">预期%s</span></div>') % (
            cls, ic, E(c.get("name")), E(c.get("now", "—")), E(c.get("expect", "")))
    r = j.get("response") or {}
    vcls = VC.get(r.get("verdict"), "j-wait")
    return ('<div class="jband"><div class="jl"><div class="jlh">昨夜判断 <span class="mut mono">%s</span></div>'
            '<div class="jstage"><b class="stchip">%s</b><b class="poschip">%s仓</b></div><div class="jline">%s</div></div>'
            '<div class="jm"><div class="jlh">可证伪检查(A档指标·实时)</div>%s</div>'
            '<div class="jr %s"><div class="jlh">盘中回应 <span class="mut mono">%s</span></div>'
            '<b class="jverdict">%s</b><div class="jnote">%s</div></div></div>') % (
        E(j.get("date", "")), E(j.get("stage", "—")), E(j.get("pos_band", "—")), E(j.get("line", "")),
        checks or '<div class="mut">—</div>', vcls, E(r.get("ts", "")),
        E(r.get("verdict", "验证中")), E(r.get("note", "等待首个心跳场回应")))

def account_html(a):
    """账户面板(与总agent共用master账)。a=warboard['account']"""
    if not a: return ""
    curve = a.get("curve") or []
    spark = ""
    if len(curve) >= 2:
        vals = [float(v) for _, v in curve]
        lo, hi = min(vals + [1.0]), max(vals + [1.0])
        rng = (hi - lo) or 1e-9
        W_, H_ = 252, 44
        pts = " ".join("%.1f,%.1f" % (4 + i * (W_ - 8) / (len(vals) - 1), 4 + (H_ - 8) * (1 - (v - lo) / rng))
                       for i, v in enumerate(vals))
        y1 = 4 + (H_ - 8) * (1 - (1.0 - lo) / rng)
        spark = ('<svg width="%d" height="%d" class="spark"><line x1="4" y1="%.1f" x2="%d" y2="%.1f" class="sp-base"/>'
                 '<polyline points="%s" class="sp-line"/><circle cx="%.1f" cy="%.1f" r="2.5" class="sp-dot"/></svg>') % (
            W_, H_, y1, W_ - 4, y1, pts,
            4 + (W_ - 8), 4 + (H_ - 8) * (1 - (vals[-1] - lo) / rng))
    wk, bwk = a.get("week_pct"), a.get("bench_week_pct")
    edge = None
    try: edge = float(wk) - float(bwk)
    except Exception: pass
    return ('<div class="side-h">账户 · 总agent共用</div>'
            '<div class="acck"><span class="mono nav">%s</span><span class="mut">净值</span>'
            '<span class="mono %s">%s</span><span class="mut">本周</span>'
            '<span class="mono %s">%s</span><span class="mut">vs基准</span></div>%s'
            '<div class="accr"><span>仓位 <b class="mono">%s%%</b></span><span>现金 <b class="mono">%s%%</b></span>'
            '<span>持仓 <b class="mono">%s</b>只</span></div><div class="side-h2" style="margin-top:10px"></div>') % (
        E("%.4f" % a.get("nav", 1.0)), chg_cls(wk), fpct(wk),
        chg_cls(edge), (("%+.1fpp" % edge) if edge is not None else "—"), spark,
        E(a.get("pos_pct", "—")), E(a.get("cash_pct", "—")), E(a.get("n_pos", "—")))

def pulse_html(p, pl):
    q = (pl or {}).get("quota") or {}
    qrows = ""
    for k, v in q.items():
        try: pct = 100.0 * float(v.get("used", 0)) / float(v.get("cap", 1))
        except Exception: pct = 0
        lv = "q-red" if pct >= 95 else ("q-yel" if pct >= 80 else "q-ok")
        qrows += ('<div class="qr"><span class="qn">%s</span><div class="qt"><i class="%s" style="width:%.0f%%"></i></div>'
                  '<span class="mono mut">%.0f%%</span></div>') % (E(k), lv, min(pct, 100), pct)
    ct = "".join('<div class="crow"><span>%s</span><b class="mono %s">%s</b></div>' % (
        E(n), chg_cls(v), fpct(v)) for n, v in (p.get("concept_top") or [])[:6])
    fresh = (pl or {}).get("fresh_sec")
    hcls, htxt = ("h-ok", "管道正常") if (fresh is not None and fresh <= 180) else ("h-bad", "断更>3分钟")
    kv = "".join('<div class="pk"><b class="mono %s">%s</b><span>%s</span></div>' % (c_, E(v_), l_) for v_, l_, c_ in (
        (p.get("zt", "—"), "涨停", "up"), (p.get("dt", "—"), "跌停", "dn"), (p.get("zb", "—"), "炸板", ""),
        (str(p.get("zb_rate", "—")) + "%", "炸板率", "up" if (p.get("zb_rate") or 0) < 30 else "dn"),
        (p.get("top_lb", "—"), "最高板", "")))
    return ('<div class="side-h">全场脉搏 <span class="%s">%s · tick %s</span></div><div class="pks">%s</div>'
            '<div class="side-h2">概念异动Top</div>%s<div class="side-h2">iFind配额水位</div>%s' % (
        hcls, htxt, E((pl or {}).get("last_tick", "—")), kv, ct, qrows))

CSS = """
:root{color-scheme:dark}*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0f14;color:#cfd8e3;font:13.5px/1.5 -apple-system,'Microsoft YaHei',sans-serif;padding:16px 20px 40px}
.mono{font-family:ui-monospace,'JetBrains Mono',Consolas,monospace;font-variant-numeric:tabular-nums}
.up{color:#e05a4e}.dn{color:#3fa66a}.mut{color:#5d6b7d}
h1{font-size:18px;color:#e8eef6;letter-spacing:1px;display:inline}
.hd{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid #1f2733;padding-bottom:9px;margin-bottom:12px;flex-wrap:wrap}
.amber{color:#d9a441;font-weight:700}
.tag{font-size:11px;color:#5d6b7d;border:1px solid #2a3444;border-radius:3px;padding:1px 7px}
.tag.sample{color:#d9a441;border-color:#d9a441}
.layout{display:grid;grid-template-columns:1fr 288px;gap:14px;align-items:start}
.sec-h{font-size:12px;color:#d9a441;letter-spacing:2px;margin:4px 0 6px;border-left:3px solid #d9a441;padding-left:8px}
.aucsum{font-size:12px;color:#8fa0b5;background:#10151d;border:1px solid #1f2733;border-radius:6px;padding:6px 12px;margin-bottom:10px}
.aucsum b{color:#d9a441}
/* 总表行 */
.thead,.trw summary{display:grid;grid-template-columns:14px 122px 84px 112px 56px 60px 90px 92px 56px 1fr;gap:7px;align-items:center}
.thead{font-size:10px;color:#3d4a5c;letter-spacing:1px;padding:2px 12px 4px}
.trw{background:#11161d;border:1px solid #1c2430;border-radius:6px;margin-bottom:5px}
.trw summary{cursor:pointer;list-style:none;padding:7px 12px;font-size:13px}
.trw summary::-webkit-details-marker{display:none}
.trw[open]{border-color:#2a3444}
.trw.st-fill{border-left:3px solid #e05a4e}.trw.st-hold{border-left:3px solid #d9a441}
.trw.st-sold{border-left:3px solid #3fa66a}.trw.st-defer{border-left:3px solid #b8742c}
.trw.st-watch{border-left:3px solid #8fb8e0}.trw.st-drop{opacity:.55}.trw.st-pend{border-left:3px solid #2a3444}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.dot.fill{background:#e05a4e}.dot.hold{background:#d9a441}.dot.sold{background:#3fa66a}
.dot.defer{background:#b8742c}.dot.watch{background:#8fb8e0}.dot.pend{background:#3d4a5c}.dot.drop{background:#2a3444}
.nm b{color:#e8eef6;font-size:14px}.nm .mut{font-size:11px}
.thmc{overflow:hidden}
.thm{font-style:normal;font-size:10.5px;color:#d9a441;background:#33261440;border:1px solid #d9a44133;border-radius:3px;padding:0 6px;white-space:nowrap}
.thm.mutth{color:#3d4a5c;background:none;border-color:#1c2430}
.srcs{display:flex;gap:3px;flex-wrap:wrap}
.src{font-size:9.5px;border-radius:3px;padding:0 5px;font-weight:500;white-space:nowrap}
.b-auc{background:#1d2a38;color:#8fb8e0}.b-lhb{background:#2a2338;color:#b39ddb}.b-thm{background:#33261480;color:#d9a441}
.b-lgc{background:#173026;color:#69b39a}.b-qlt{background:#2b2430;color:#d190b6}.b-mst{background:#252c38;color:#aeb9c8}
.b-new{background:#3a2c12;color:#ffb84d;border:1px solid #d9a441}
.pxc{font-size:14px;font-weight:700;text-align:right}.chgc{font-size:12px;text-align:right}
.aucc{display:flex;gap:5px;align-items:center;font-size:12px}
.vch{font-size:10px;border-radius:3px;padding:0 4px}
.v-ok{background:#1d2a38;color:#8fb8e0}.v-bad{background:#3a1d1d;color:#e05a4e}
.v-good{background:#173026;color:#d9a441;border:1px solid #d9a441}.v-na{color:#3d4a5c}
.pnlc{font-size:12px;text-align:right}.age{color:#e0a04e;font-style:normal;font-size:10px}
.stb{font-size:10.5px;border-radius:3px;padding:1.5px 7px;letter-spacing:1px;text-align:center;white-space:nowrap}
.stb.pend{background:#1c2430;color:#8395aa}.stb.fill{background:#e05a4e;color:#fff}
.stb.drop{background:#1c2430;color:#5d6b7d;text-decoration:line-through}
.stb.hold{background:#d9a441;color:#171207}.stb.sold{background:#3fa66a;color:#06130c}
.stb.defer{background:#b8742c;color:#fff}.stb.watch{background:#1d2a38;color:#8fb8e0}
.nxt{font-size:11.5px;color:#8fa0b5;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
/* 展开体 */
.body{border-top:1px dashed #1c2430;padding:8px 14px 10px 34px}
.stamp{margin:2px 0 6px;font-size:14px;font-weight:700}
.stamp span{font-size:11px;font-weight:400;color:#8fa0b5}
.s-fill{color:#e05a4e}.s-sold{color:#3fa66a}.s-defer{color:#e0a04e}.s-drop{color:#5d6b7d}
.pr{display:flex;gap:8px;padding:2px 0;font-size:12.5px}
.prl{flex:0 0 76px;color:#5d6b7d;letter-spacing:1px;white-space:nowrap}
.prv{color:#b9c6d6}.prv.mut{color:#3d4a5c}
.tlbox{margin-top:6px;font-size:12px}.tlh{font-size:10px;color:#3d4a5c;letter-spacing:2px;margin-bottom:2px}
.tli{display:flex;gap:10px;padding:2px 0 2px 8px;border-left:2px solid #2a3444;margin-left:2px}
.tlt{color:#d9a441;flex:0 0 58px}.tld{color:#8fa0b5}
/* 侧栏 */
.side{background:#10151d;border:1px solid #1f2733;border-radius:8px;padding:12px 14px;position:sticky;top:12px}
.side-h{font-size:12px;color:#d9a441;letter-spacing:2px;margin-bottom:8px}
.side-h span{float:right;font-size:10px;letter-spacing:0}
.h-ok{color:#3fa66a}.h-bad{color:#e05a4e;font-weight:700}
.side-h2{font-size:11px;color:#5d6b7d;letter-spacing:2px;margin:13px 0 6px;border-top:1px solid #1c2430;padding-top:9px}
.pks{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;text-align:center}
.pk b{display:block;font-size:16px}.pk span{font-size:10px;color:#5d6b7d}
.crow{display:flex;justify-content:space-between;font-size:12px;padding:2.5px 0}
.qr{display:flex;align-items:center;gap:7px;padding:3px 0;font-size:11px}
.qn{flex:0 0 58px;color:#8fa0b5}.qt{flex:1;height:6px;background:#1c2430;border-radius:3px;overflow:hidden}
.qt i{display:block;height:100%}.q-ok{background:#3fa66a}.q-yel{background:#d9a441}.q-red{background:#e05a4e}
.ft{margin-top:16px;font-size:11px;color:#3d4a5c;border-top:1px solid #1c2430;padding-top:8px}
/* 判断横幅 */
.jband{display:grid;grid-template-columns:1.1fr 1.3fr 1fr;gap:14px;background:#10151d;border:1px solid #2a3444;border-radius:8px;padding:11px 16px;margin-bottom:13px}
.jlh{font-size:10px;color:#5d6b7d;letter-spacing:2px;margin-bottom:5px}
.jstage{display:flex;gap:7px;margin-bottom:4px}
.stchip{background:#3a1d1d;color:#e05a4e;border:1px solid #e05a4e88;border-radius:4px;padding:2px 10px;font-size:14px;letter-spacing:2px}
.poschip{background:#33261480;color:#d9a441;border:1px solid #d9a44166;border-radius:4px;padding:2px 10px;font-size:14px}
.jline{font-size:12.5px;color:#b9c6d6}
.jck{display:flex;gap:7px;align-items:baseline;font-size:12px;padding:2px 0}
.c-ok{color:#3fa66a;font-weight:700}.c-bad{color:#e05a4e;font-weight:700}.c-wait{color:#5d6b7d}
.jcn{color:#8fa0b5;flex:0 0 66px}.jcv{color:#e8eef6;font-weight:600}.jce{font-size:10.5px}
.jr{border-left:1px solid #1f2733;padding-left:14px}
.jverdict{font-size:17px;letter-spacing:2px}
.j-ok .jverdict{color:#3fa66a}.j-mid .jverdict{color:#d9a441}.j-bad .jverdict{color:#e05a4e}
.j-bad{background:#1a0f0f;border-radius:0 8px 8px 0}.j-wait .jverdict{color:#8395aa}
.jnote{font-size:12px;color:#8fa0b5;margin-top:3px}
/* 账户面板 */
.acck{display:grid;grid-template-columns:auto auto auto auto auto auto;gap:2px 10px;align-items:baseline;font-size:11px;margin-bottom:4px}
.acck .nav{font-size:18px;font-weight:700;color:#e8eef6}
.acck .mono:not(.nav){font-size:13px;font-weight:600}
.spark{display:block;margin:2px 0}
.sp-line{fill:none;stroke:#d9a441;stroke-width:1.6}
.sp-base{stroke:#2a3444;stroke-dasharray:3 3;stroke-width:1}
.sp-dot{fill:#d9a441}
.accr{display:flex;gap:14px;font-size:11px;color:#8fa0b5}
.accr b{color:#e8eef6}
@media(max-width:1150px){.layout{grid-template-columns:1fr}.side{position:static}.jband{grid-template-columns:1fr}}
"""

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
    src = None
    if "--src" in sys.argv: src = sys.argv[sys.argv.index("--src") + 1]
    src = src or os.path.join(BASE, "盘中", d, "warboard.json")
    if not os.path.isfile(src):
        print("缺 warboard.json:", src); sys.exit(1)
    w = json.load(open(src, encoding="utf-8"))
    cards = w.get("cards") or []
    order = {"已成交": 0, "持有中": 1, "卖出顺延": 2, "观察": 3, "待触发": 4, "已卖出": 5, "已放弃": 6}
    cards.sort(key=lambda c: order.get(c.get("status"), 9))
    n_st = {}
    for c in cards: n_st[c.get("status", "?")] = n_st.get(c.get("status", "?"), 0) + 1
    stat = " · ".join("%s%d" % (k, v) for k, v in sorted(n_st.items(), key=lambda x: order.get(x[0], 9)))
    a = w.get("auction_review") or {}
    vs = {}
    for c in cards:
        v = (c.get("auction") or {}).get("verdict")
        if v: vs[v] = vs.get(v, 0) + 1
    aucsum = ('<div class="aucsum">竞价盘点 <b>%s</b> · 覆盖%d/%d只: %s · 竞价新增<b>%d</b>只 %s</div>' % (
        E(a.get("ts", "09:25")), sum(vs.values()), len(cards),
        " / ".join("%s%d" % (k, v) for k, v in vs.items()) or "未产出",
        sum(1 for c in cards if "竞价场新增" in (c.get("sources") or [])),
        E(a.get("summary", ""))))
    sample = '<span class="tag sample">样例数据 SAMPLE·供页面调样,非真实决策</span>' if w.get("mode") == "sample" else ""
    thead = ('<div class="thead"><span></span><span>股票</span><span>题材</span><span>来源</span><span style="text-align:right">现价</span>'
             '<span style="text-align:right">涨跌</span><span>竞价判定</span><span style="text-align:right">浮盈/日龄</span>'
             '<span>状态</span><span>下一动作 / 成交记录</span></div>')
    doc = ('<!doctype html><html lang="zh"><head><meta charset="utf-8">'
           '<meta http-equiv="refresh" content="60"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>盘中作战台 %s</title><style>%s</style></head><body>'
           '<div class="hd"><h1>盘中作战台 <span class="amber">WAR BOARD</span></h1>'
           '<span class="mono mut">%s · 更新 %s</span><span class="tag">60s自刷新</span>%s</div>'
           '%s<div class="layout"><div>%s'
           '<div class="sec-h">作战总表 · %d只(%s) — 点行展开五要素与时间线</div>%s%s'
           '</div><div class="side">%s</div></div>'
           '<div class="ft">口径:成交=触发后下一tick·流动性帽20%%·盘中滑点0.10%%(v1.8§3.3.1);无reason禁入册;决断json落盘即上墙;行序=成交>持有>顺延>观察>待触发>已了结。</div>'
           '<script>(function(){var k="wb_fold_"+document.title.slice(-8);var st={};'
           'try{st=JSON.parse(localStorage.getItem(k)||"{}")}catch(e){}'
           'document.querySelectorAll("details.trw[data-k]").forEach(function(d){var id=d.getAttribute("data-k");'
           'if(id in st){if(st[id]){d.setAttribute("open","")}else{d.removeAttribute("open")}}'
           'd.addEventListener("toggle",function(){st[id]=d.open;try{localStorage.setItem(k,JSON.stringify(st))}catch(e){}})});'
           '})()</script></body></html>') % (
        E(d), CSS, E(d), E(w.get("ts", "")), sample, hero_html(w.get("judgment")), aucsum,
        len(cards), stat, thead, "".join(row_html(c) for c in cards),
        account_html(w.get("account")) + pulse_html(w.get("pulse") or {}, w.get("pipeline") or {}))
    out = os.path.join(BASE, "复盘", "盯盘台", "intraday.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("[√] intraday.html", len(doc), "bytes,", len(cards), "只 ->", out)

if __name__ == "__main__":
    main()
