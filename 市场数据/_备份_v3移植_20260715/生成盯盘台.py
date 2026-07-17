# -*- coding: utf-8 -*-
"""生成盯盘台.py —— 读 _学习/judgment_YYYYMMDD.json → 渲染7页+存档+自动历史。用法: python 生成盯盘台.py [YYYYMMDD]
v3(2026-07-11 深色操盘终端改版,taste-skill读盘:cockpit密度/单强调色/等宽数字/零依赖图表组件):
- 深色terminal主题(墨黑底+金琥珀accent+A股红涨绿跌语义色),全部旧class向后兼容(存档/脚本段照常渲染)。
- 新图表组件: .routes五路牌 .cols柱状 .ladbar梯队 .hb横向条形(diverging) .gauge温度计 .stages三态开关 .posmeter仓位 .d6六有点 .pool池行——组件写法见 R/_盯盘台组件规范.md
- 内联浅色覆盖: 脚本段(台账/温度卡)自带浅色inline样式,用[style*=]选择器映射到深色,勿改上游脚本。
- 内嵌JS: 进场reveal+条形生长动画(IntersectionObserver,尊重prefers-reduced-motion;无JS时静态完整)。
(铁律:改本文件必须python整读整写/tmp→ast→cp→读回比对,Edit工具会静默截断)"""
import os,sys,json,glob,datetime
BASE='D:\\股票数据\\市场数据'
if not os.path.isdir(BASE):
    g=glob.glob('/sessions/*/mnt/股票数据/市场数据')
    BASE=g[0] if g else BASE
SITE=os.path.join(BASE,'复盘','盯盘台'); ARC=os.path.join(SITE,'archive'); L=os.path.join(BASE,'_学习')
import re as _re
_DIVTAG=_re.compile(r'<div\b|</div>')
def _match_div(s,start):
    depth=0
    for m in _DIVTAG.finditer(s,start):
        if m.group()=='</div>':
            depth-=1
            if depth==0: return m.end()
        else:
            depth+=1
    return len(s)
def _rt(html):
    """时间线条目按日期稳定降序(最新在上);同日保持原相对顺序。"""
    if 'class="tl"' not in html: return html
    res=''; idx=0
    while True:
        p=html.find('<div class="tl">',idx)
        if p<0: res+=html[idx:]; break
        res+=html[idx:p]
        end=_match_div(html,p)
        inner=html[p+len('<div class="tl">'):end-len('</div>')]
        items=[]; j=0; prefix=''; trailing=''
        while True:
            q=inner.find('<div class="tli">',j)
            if q<0:
                trailing=inner[j:]; break
            if not items: prefix=inner[j:q]
            e=_match_div(inner,q)
            items.append(inner[q:e]); j=e
        def _dt(it):
            m=_re.search(r'<div class="d">\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',it)
            return m.group(1) if m else '0000-00-00'
        items=sorted(items,key=_dt,reverse=True)
        res+='<div class="tl">'+prefix+''.join(items)+trailing+'</div>'
        idx=end
    return res

CSS='''
:root{color-scheme:dark;
--bg:#0c0f15;--panel:#131824;--panel2:#0f141d;--line:#222a3a;--line2:#2d3850;
--ink:#dbe2ee;--sub:#8b93a4;--dim:#5d6678;
--accent:#d9a84e;--accent-dim:#8a6d3b;
--up:#e5484d;--down:#2fbc75;
--hit:#39c0a3;--half:#d8a03d;--miss:#e5484d;
--mono:ui-monospace,"Cascadia Mono","SF Mono",Consolas,"Courier New",monospace}
*{box-sizing:border-box;margin:0;padding:0}
html{scrollbar-color:#2d3850 var(--bg)}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.68;-webkit-font-smoothing:antialiased}
::selection{background:rgba(217,168,78,.25)}
/* ── nav ── */
.nav{position:sticky;top:0;z-index:9;background:rgba(12,15,21,.92);backdrop-filter:blur(10px);display:flex;gap:2px;align-items:center;padding:11px 18px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.nav .brand{color:var(--accent);font-size:13px;letter-spacing:3px;font-weight:700;margin-right:14px}
.nav a{color:#9aa3b5;text-decoration:none;font-size:13px;padding:5px 11px;border-radius:7px;transition:.15s;border:1px solid transparent}
.nav a:hover{color:var(--ink);border-color:var(--line2)}
.nav a.on{background:var(--accent);color:#14100a;font-weight:700}
.nav .upd{margin-left:auto;color:var(--dim);font-size:11.5px;font-family:var(--mono)}
.wrap{max-width:960px;margin:0 auto;padding:26px 18px 70px}
/* ── hero ── */
.hero{position:relative;background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:14px;padding:26px 30px;overflow:hidden}
.hero:before{content:"";position:absolute;inset:0;background:radial-gradient(600px 180px at 85% -20%,rgba(217,168,78,.08),transparent);pointer-events:none}
.hero .kick{font-size:11.5px;letter-spacing:3px;color:var(--accent);text-transform:uppercase;font-family:var(--mono)}
.hero h1{font-size:24px;margin:9px 0 7px;font-weight:750;letter-spacing:-.3px}
.hero p{color:var(--sub);font-size:13.6px;max-width:680px}
.stance{display:flex;gap:9px;flex-wrap:wrap;margin-top:16px}
.pill{background:rgba(255,255,255,.04);border:1px solid var(--line2);padding:5px 13px;border-radius:20px;font-size:12.8px;color:#c9cfdc}
.pill b{color:var(--ink)}
.pill.warn{background:rgba(229,72,77,.1);border-color:rgba(229,72,77,.35);color:#f0b6b4}
/* ── section head ── */
h2{font-size:15.5px;margin:34px 0 4px;padding-left:12px;border-left:3px solid var(--accent);font-weight:700;letter-spacing:.3px}
h2.hot{border-left-color:var(--up)}
.hint{color:var(--dim);font-size:12.3px;margin:4px 0 14px;padding-left:15px}
/* ── strips/cards ── */
.strip{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.kv{flex:1;min-width:120px;background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:12px 15px}
.kv .l{font-size:11.8px;color:var(--sub)}.kv .v{font-size:20px;font-weight:800;margin-top:3px;font-family:var(--mono);letter-spacing:-.5px}
.dn{color:var(--down)}.up{color:var(--up)}.mut{color:var(--sub)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:17px 20px;margin-top:13px}
.card p{font-size:13.6px;color:#b9c1d0}
.card.hotcard{border-color:rgba(229,72,77,.35);background:linear-gradient(135deg,var(--panel),rgba(229,72,77,.05))}
.gate{display:flex;gap:10px;flex-wrap:wrap}
.gate .g{flex:1;min-width:110px;text-align:center;border:1px solid var(--line);border-radius:10px;padding:9px;background:var(--panel2)}
.gate .g .t{font-size:12px;color:var(--sub)}.gate .g .s{font-weight:700;margin-top:2px}
.s-weak{color:var(--miss)}.s-mid{color:var(--half)}.s-ok{color:var(--hit)}
.two{display:flex;gap:14px;flex-wrap:wrap;margin-top:14px}
.mith{flex:1;min-width:270px;background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:17px 20px;text-decoration:none;color:inherit;display:block;transition:.18s}
.mith:hover{transform:translateY(-2px);border-color:var(--accent-dim)}
.mith h3{font-size:15px;margin-bottom:8px;display:flex;justify-content:space-between}.mith h3 .arw{color:var(--accent)}
.mith p{font-size:13px;color:var(--sub)}
/* ── tables ── */
table{width:100%;border-collapse:collapse;margin-top:6px;font-size:13px;table-layout:auto}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere;word-break:break-word}
th{color:var(--sub);font-weight:600;font-size:11.8px;letter-spacing:.5px}
td{font-variant-numeric:tabular-nums}
tr:hover td{background:rgba(255,255,255,.02)}
th:first-child,td:first-child{min-width:78px}
table td:first-child{min-width:5em}
table td:first-child b{white-space:nowrap}
.wrap{overflow-x:hidden}
.dS{color:#b18aff;font-weight:700}.dA{color:var(--hit);font-weight:700}.dB{color:var(--sub)}.dC{color:var(--miss)}
.tag2{display:inline-block;font-size:11px;padding:1px 8px;border-radius:9px}
.t-attack{background:rgba(57,192,163,.14);color:var(--hit)}.t-watch{background:rgba(216,160,61,.14);color:var(--half)}.t-avoid{background:rgba(229,72,77,.14);color:var(--miss)}
/* ── timeline ── */
.tl{position:relative;margin-top:10px;padding-left:22px}
.tl:before{content:"";position:absolute;left:6px;top:4px;bottom:4px;width:2px;background:var(--line)}
.tli{position:relative;padding:0 0 18px 8px}
.tli:before{content:"";position:absolute;left:-19px;top:5px;width:10px;height:10px;border-radius:50%;background:var(--accent);border:2px solid var(--bg)}
.tli .d{font-size:12px;color:var(--accent);font-weight:700;font-family:var(--mono)}
.tli .h{font-size:14px;font-weight:650;margin:2px 0 4px}.tli .b{font-size:13px;color:#aab2c2}
.tli .sup{font-size:12px;color:var(--sub);margin-top:6px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:7px 10px}.tli .sup b{color:var(--ink)}
/* ── legacy misc ── */
.qbar{margin:9px 0}.qbar .lab{display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:3px}
.track{height:8px;background:#1b2230;border-radius:5px;overflow:hidden}.track>i{display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,var(--accent-dim),var(--up))}
.track.teal>i{background:linear-gradient(90deg,#1f6a5e,var(--hit))}
.base{font-size:11.5px;color:var(--dim);margin-top:4px}
.ladder{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;align-items:stretch}
.rung{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;text-align:center;min-width:80px;font-size:12.6px}
.rung .lv{font-size:12px;color:var(--sub)}.rung .nm{font-size:12.5px;font-weight:600;margin-top:2px}
.rung.gap{background:rgba(229,72,77,.07);border-style:dashed;border-color:rgba(229,72,77,.4);color:var(--miss)}
.rung.high{border-color:var(--up)}
.rung .tag{display:inline-block;font-size:11px;font-weight:700;color:var(--accent);background:rgba(217,168,78,.12);border-radius:7px;padding:0 7px;margin-right:6px;font-family:var(--mono)}
.foot{margin-top:36px;padding:14px 18px;background:var(--panel2);border:1px solid var(--line);border-radius:11px;font-size:12.2px;color:var(--sub)}.foot b{color:var(--ink)}
.badge{display:inline-block;font-size:11px;padding:1px 8px;border-radius:10px;font-weight:600}
.bA{background:rgba(57,192,163,.14);color:var(--hit)}.bC{background:rgba(216,160,61,.14);color:var(--half)}.bMix{background:rgba(177,138,255,.14);color:#b18aff}
.hlist{list-style:none}.hlist li{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:13px 16px;margin-top:10px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.hlist .dt{font-weight:800;font-size:15px;flex:0 0 96px;font-family:var(--mono)}.hlist .st{flex:1;font-size:13.2px;color:#aab2c2;min-width:200px}
.hlist a.go{color:var(--accent);text-decoration:none;font-size:13px;font-weight:600;white-space:nowrap}
.jjr td{background:rgba(217,168,78,.06);border-bottom:1px solid var(--line);padding:7px 10px 9px;font-size:12.4px;color:#b3a98f}
.jjr .jjtag{display:inline-block;font-size:11px;font-weight:700;color:var(--accent);background:rgba(217,168,78,.14);border-radius:8px;padding:1px 8px;margin-right:8px;white-space:nowrap}
.jpr td{background:rgba(57,192,163,.06);border-bottom:1px solid var(--line);padding:7px 10px 9px;font-size:12.4px;color:#8fbcb0}
.jpr .jptag{display:inline-block;font-size:11px;font-weight:700;color:var(--hit);background:rgba(57,192,163,.14);border-radius:8px;padding:1px 8px;margin-right:8px;white-space:nowrap}
/* ── obs 荐票/观察卡 ── */
.obswrap{margin-top:6px}
.obs{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:0;margin-top:12px;overflow:hidden;transition:border-color .18s}
.obs:hover{border-color:var(--line2)}
.obs-head{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;padding:13px 16px 8px}
.obs-nm{font-weight:800;font-size:14.5px;flex:0 0 auto}.obs-nm .mut{font-weight:400;font-size:12px;margin-left:6px;font-family:var(--mono)}
.obs-pos{flex:1 1 240px;min-width:0;font-size:13px;color:#aab2c2;overflow-wrap:anywhere}
.obs-watch{padding:6px 16px 12px;font-size:13.2px;color:#c4cbd8;overflow-wrap:anywhere;border-bottom:1px solid var(--line)}
.obs-lab,.obs-lab2{display:inline-block;font-size:11px;font-weight:700;border-radius:8px;padding:1px 8px;margin-right:8px;white-space:nowrap}
.obs-lab{color:#f0a5a3;background:rgba(229,72,77,.13)}
.obs-rec{padding:8px 16px;font-size:12.6px;color:#8fbcb0;background:rgba(57,192,163,.05);overflow-wrap:anywhere}
.obs-lab2{color:var(--hit);background:rgba(57,192,163,.14)}
.obs-jj{padding:8px 16px 10px;font-size:12.4px;color:#b3a98f;background:rgba(217,168,78,.05);overflow-wrap:anywhere}
/* ── details 折叠 ── */
details.chain{background:var(--panel);border:1px solid var(--line);border-radius:13px;margin-top:12px;padding:0 18px}
details.chain summary{cursor:pointer;padding:13px 0;font-weight:700;font-size:14px;color:var(--ink);list-style:none;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
details.chain summary::before{content:"\\25B8";color:var(--accent);transition:.15s}
details.chain[open] summary::before{content:"\\25BE"}
details.chain summary .chip{font-size:11.5px;font-weight:600;padding:1px 9px;border-radius:10px;background:rgba(255,255,255,.05);color:var(--sub);border:1px solid var(--line)}
details.chain summary .chip.hot{background:rgba(229,72,77,.13);color:#f0a5a3;border-color:transparent}
details.chain summary .chip.cold{background:rgba(57,192,163,.13);color:var(--hit);border-color:transparent}
details.chain .inner{padding:2px 0 16px}
/* ══ 新图表组件 ══ */
/* 五路牌 */
.routes{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:13px}
.routes .rt{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 14px;text-decoration:none;color:inherit;display:flex;flex-direction:column;gap:5px;transition:.18s}
.routes .rt:hover{transform:translateY(-2px);border-color:var(--accent-dim)}
.rt .rtn{font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:1px}
.rt .rtm{font-size:13.2px;font-weight:700}
.rt .rtt{font-size:15px;font-weight:800}
.rt .rtd{font-size:11.8px;color:var(--sub);line-height:1.5}
@media(max-width:820px){.routes{grid-template-columns:repeat(2,1fr)}}
/* 柱状图 */
.cols{display:flex;gap:8px;align-items:flex-end;height:150px;margin-top:14px;padding:0 4px}
.cols .col{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:5px;height:100%}
.cols .col i{display:block;width:70%;max-width:56px;background:linear-gradient(180deg,var(--accent),var(--accent-dim));border-radius:5px 5px 2px 2px;min-height:3px;transform-origin:bottom}
.cols .col.hotc i{background:linear-gradient(180deg,var(--up),#8a2f32)}
.cols .col b{font-size:11.6px;font-family:var(--mono);color:var(--ink);white-space:nowrap}
.cols .col span{font-size:11px;color:var(--dim);font-family:var(--mono);white-space:nowrap}
.colsub{display:flex;gap:8px;margin-top:8px;padding:0 4px}
.colsub span{flex:1;text-align:center;font-size:11px;color:var(--sub);font-family:var(--mono);white-space:nowrap}
/* 横向条形(diverging,中轴50%) */
.hb{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.hb .hbl{flex:0 0 128px;font-size:12.6px;color:#c4cbd8;text-align:right;overflow-wrap:anywhere}
.hb .hbt{flex:1;position:relative;height:14px;background:rgba(255,255,255,.03);border-radius:3px;overflow:hidden}
.hb .hbt:before{content:"";position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--line2)}
.hb .hbt i{position:absolute;top:2px;bottom:2px;border-radius:2px}
.hb .hbt i.pos{left:50%;background:linear-gradient(90deg,rgba(229,72,77,.75),rgba(229,72,77,.35));transform-origin:left}
.hb .hbt i.neg{right:50%;background:linear-gradient(270deg,rgba(47,188,117,.75),rgba(47,188,117,.35));transform-origin:right}
.hb .hbv{flex:0 0 72px;font-family:var(--mono);font-size:12.6px;font-weight:700;text-align:right}
.hb .hbs{flex:0 0 auto;font-size:11.5px;color:var(--dim);font-family:var(--mono)}
.hb .hbnote{flex:1 1 100%;font-size:11.8px;color:var(--sub);padding-left:138px;margin-top:-2px}
@media(max-width:640px){.hb .hbl{flex-basis:86px}.hb .hbnote{padding-left:0}}
/* 温度计 */
.gauge{margin-top:12px}
.gauge .gtrack{position:relative;height:10px;border-radius:6px;background:linear-gradient(90deg,#2b5f8f 0 25%,#2f7d74 0 45%,#8a7f3a 0 65%,#b06a35 0 85%,#c04545 0 100%);opacity:.9}
.gauge .gmark{position:absolute;top:-5px;width:3px;height:20px;background:var(--ink);border-radius:2px;box-shadow:0 0 0 2px rgba(0,0,0,.5)}
.gauge .gl{display:flex;justify-content:space-between;font-size:10.5px;color:var(--dim);margin-top:5px;font-family:var(--mono)}
.gauge .gv{font-family:var(--mono);font-weight:800;font-size:18px;margin-top:6px}
/* 三态总开关 / 仓位计 */
.stages{display:flex;gap:8px;margin-top:12px}
.stages .st{flex:1;text-align:center;padding:9px 6px;border:1px solid var(--line);border-radius:9px;color:var(--dim);font-size:13px;background:var(--panel2)}
.stages .st.on{border-color:var(--accent);color:var(--ink);font-weight:700;background:rgba(217,168,78,.09)}
.stages .st small{display:block;font-size:10.5px;color:var(--dim);font-family:var(--mono)}
.posmeter{position:relative;height:12px;border-radius:6px;background:#1b2230;margin-top:12px;overflow:hidden}
.posmeter i{position:absolute;top:0;bottom:0;left:0;background:linear-gradient(90deg,var(--accent-dim),var(--accent));border-radius:6px}
.posmeter em{position:absolute;top:-3px;bottom:-3px;width:2px;background:rgba(255,255,255,.35)}
.posml{display:flex;justify-content:space-between;font-size:10.5px;color:var(--dim);margin-top:4px;font-family:var(--mono)}
/* 六有点 */
.d6{display:inline-flex;gap:3px;vertical-align:middle;margin:0 6px}
.d6 i{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.08);border:1px solid var(--line2)}
.d6 i.on{background:var(--accent);border-color:var(--accent)}
/* 题材行 */
.trow{padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.trow .tr1{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.trow .tnm{font-weight:750;font-size:13.8px;min-width:110px}
.trow .tjd{font-size:12px;font-weight:700;padding:1px 9px;border-radius:9px}
.tj-main{background:rgba(229,72,77,.13);color:#f0a5a3}.tj-branch{background:rgba(216,160,61,.13);color:var(--half)}.tj-minor{background:rgba(255,255,255,.06);color:var(--sub)}
.trow .tbar{flex:1;min-width:120px;height:12px;background:rgba(255,255,255,.03);border-radius:3px;overflow:hidden;position:relative}
.trow .tbar i{position:absolute;left:0;top:2px;bottom:2px;border-radius:2px;background:linear-gradient(90deg,rgba(217,168,78,.8),rgba(217,168,78,.3));transform-origin:left}
.trow .tct{font-family:var(--mono);font-size:12.5px;font-weight:700;min-width:44px;text-align:right}
.trow .tds{font-size:12.2px;color:var(--sub);margin-top:4px}
/* 竞价池行 */
.pool .hb .hbl{flex-basis:150px}
.sigchip{display:inline-block;font-size:11px;font-weight:700;padding:0 7px;border-radius:7px;margin-left:6px}
.sig-yz{background:rgba(229,72,77,.14);color:#f0a5a3}.sig-mb{background:rgba(255,255,255,.06);color:var(--sub)}
/* 量能台阶梯(站在哪一阶) */
.steps{margin-top:12px}
.step{display:flex;align-items:center;gap:10px;padding:8px 12px;border:1px solid var(--line);border-radius:9px;margin-top:6px;background:var(--panel2)}
.step .sr{flex:0 0 108px;font-family:var(--mono);font-size:12.3px;color:var(--sub);text-align:right}
.step .sn{flex:0 0 170px;font-size:12.8px;font-weight:700}
.step .sn small{display:block;font-weight:400;font-size:11px;color:var(--dim)}
.step .sd{flex:1;display:flex;gap:6px;flex-wrap:wrap;min-height:18px}
.step .dayc{font-family:var(--mono);font-size:11.5px;padding:1px 8px;border-radius:8px;background:rgba(255,255,255,.06);color:var(--sub)}
.step .dayc.now{background:rgba(229,72,77,.2);color:#f6b8b6;font-weight:700}
.step.cur{border-color:var(--accent);background:rgba(217,168,78,.09)}
.step.dim .sn{color:var(--sub);font-weight:600}
@media(max-width:640px){.step .sn{flex-basis:120px}.step .sr{flex-basis:80px}}
/* ── 脚本段浅色inline覆盖(台账/温度卡等,勿改上游脚本) ── */
[style*="#faf7f0"]{background:var(--panel2)!important;color:#aab2c2!important}
[style*="#f3eee1"]{background:rgba(217,168,78,.07)!important;color:#b3a98f!important}
[style*="#fffdf9"],[style*="#f6f4ef"],[style*="#efeae0"]{background:var(--panel)!important;color:var(--ink)!important}
[style*="color:#1e8449"]{color:var(--down)!important}
[style*="color:#c0392b"]{color:var(--up)!important}
[style*="color:#b45309"]{color:var(--half)!important}
[style*="#eae1cc"]{background:rgba(217,168,78,.14)!important;color:var(--accent)!important}
/* ── 进场动画(JS加持,无JS=静态;尊重reduced-motion) ── */
@media (prefers-reduced-motion: no-preference){
.rv{opacity:0;transform:translateY(12px)}
.rv.on{opacity:1;transform:none;transition:opacity .55s cubic-bezier(.16,1,.3,1),transform .55s cubic-bezier(.16,1,.3,1)}
.on .hbt i,.on .tbar i{animation:growx .7s cubic-bezier(.16,1,.3,1)}
.on .cols i{animation:growy .7s cubic-bezier(.16,1,.3,1)}
@keyframes growx{from{transform:scaleX(0)}}
@keyframes growy{from{transform:scaleY(0)}}
}
'''

JS='''<script>
(function(){
if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
var els=document.querySelectorAll('.card,.obs,.routes .rt,.kv,.hero,details.chain,.tli,.cols,.gauge,.trow');
els.forEach(function(e){e.classList.add('rv')});
var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('on');io.unobserve(en.target)}})},{threshold:.12});
els.forEach(function(e){io.observe(e)});
})();
</script>'''

NAV=[('index.html','概览'),('cycle.html','周期情绪'),('auction.html','①竞价'),('lhb.html','②龙虎榜'),('theme.html','③主线题材'),('logic.html','④产业逻辑'),('limitup.html','⑤涨停复盘'),('history.html','历史')]
def nav(active,upd):
    s='<div class="nav"><span class="brand">情绪盯盘台</span>'
    for h,l in NAV:
        cls='on' if h==active else ''
        s+='<a class="'+cls+'" href="'+h+'">'+l+'</a>'
    return s+'<span class="upd">更新 '+upd+'</span></div>'

def _fold_tl(body):
    """时间线折叠v2(2026-07-11用户拍板):最新1条外露,其余收进details;条目>=2才折;幂等。"""
    res='';idx=0
    while True:
        p=body.find('<div class="tl">',idx)
        if p<0: res+=body[idx:]; break
        j2=_match_div(body,p)
        tl=body[p:j2]
        ds=_re.findall(r'<div class="d">([0-9][0-9-]+)',tl)
        if len(ds)<2 or 'tlfold' in body[max(0,p-160):p]:
            res+=body[idx:j2]; idx=j2; continue
        inner=tl[len('<div class="tl">'):-len('</div>')]
        items=[];k=0;prefix='';trailing=''
        while True:
            q=inner.find('<div class="tli">',k)
            if q<0: trailing=inner[k:]; break
            if not items: prefix=inner[k:q]
            e=_match_div(inner,q)
            items.append(inner[q:e]); k=e
        if len(items)<2:
            res+=body[idx:j2]; idx=j2; continue
        first='<div class="tl">'+prefix+items[0]+'</div>'
        rest=''.join(items[1:])
        fold=('<details class="chain tlfold"><summary><b>更早的认知迭代</b> '
          +'<span class="chip">'+str(len(items)-1)+'条</span> <span class="mut">'+ds[-1]+' ~ '+ds[1]+'</span></summary>'
          +'<div class="inner"><div class="tl">'+rest+trailing+'</div></div></details>')
        res+=body[idx:p]+first+fold; idx=j2
    return res

def shell(title,navbar,body):
    return ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>'+title
        +'</title><style>'+CSS+'</style></head><body>'+navbar+'<div class="wrap">'+body+'</div>'+JS+'</body></html>')
def build(date):
    os.makedirs(ARC,exist_ok=True); os.makedirs(L,exist_ok=True)
    j=json.load(open(os.path.join(L,'judgment_'+date+'.json'),encoding='utf-8'))
    upd=j.get('更新label',date); b=j['bodies']
    titles=[('index','概览'),('cycle','周期情绪'),('auction','竞价·第一路'),('lhb','龙虎榜·第二路'),('theme','主线题材·第三路'),('logic','产业逻辑·第四路'),('limitup','涨停复盘·第五路')]
    for k,t in titles:
        if k not in b: continue
        fn=k+'.html'
        open(os.path.join(SITE,fn),'w',encoding='utf-8').write(shell('情绪盯盘台 · '+t,nav(fn,upd),_fold_tl(_rt(b[k]))))
    topbar='<div class="nav"><span class="brand">情绪盯盘台 · 存档</span><a href="../index.html">← 返回概览</a><a href="../history.html">历史列表</a><span class="upd">冻结于 '+upd+'</span></div>'
    open(os.path.join(ARC,date+'.html'),'w',encoding='utf-8').write(shell('复盘存档 '+date,topbar,_rt(j['archive_body'])))
    idxp=os.path.join(L,'history_index.json')
    idx=json.load(open(idxp,encoding='utf-8')) if os.path.exists(idxp) else {}
    idx[date]=j.get('一句话','')
    json.dump(idx,open(idxp,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    dates=sorted([os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(ARC,'*.html'))],reverse=True)
    lis=''
    for dt in dates:
        disp=dt[4:6]+'-'+dt[6:8]
        lis+=('<li><span class="dt">'+disp+'</span><span class="st">'+idx.get(dt,'')
              +'</span><a class="go" href="archive/'+dt+'.html">看完整存档 →</a></li>')
    hb=('<div class="hero"><div class="kick">Archive · 历史记录</div><h1>历史复盘存档</h1><p>每天18:00收盘后当日完整复盘冻结存档,永久可回看;首页只显示最新一天。</p></div><h2>存档列表</h2><ul class="hlist">'
        +lis+'</ul><div class="foot">存档只加不删,对应每日18:00傍晚链路产物。</div>')
    open(os.path.join(SITE,'history.html'),'w',encoding='utf-8').write(shell('情绪盯盘台 · 历史',nav('history.html',upd),hb))
    print('盯盘台已生成:',date,'| 存档天数',len(dates))
    # ★2026-07-13封堵:每次重建都会冲掉PAPERTRADE看板→自动补跑模拟盘inject+六页锚点自检(保证下沉到代码,不依赖prompt纪律)
    import subprocess
    _eng=os.path.join(BASE,'模拟盘引擎.py')
    if os.path.exists(_eng):
        _r=subprocess.run([sys.executable,_eng,'inject',date],capture_output=True,text=True)
        if _r.returncode!=0:
            print('!!!模拟盘inject失败,页面缺PAPERTRADE看板:',((_r.stderr or _r.stdout) or '')[-300:])
        elif _r.stdout: print(_r.stdout.strip())
    else:
        print('!!!未找到模拟盘引擎.py,PAPERTRADE看板未注入')
    _miss=[k for k in ('index','auction','lhb','theme','logic','limitup')
        if os.path.exists(os.path.join(SITE,k+'.html'))
        and '<!--PAPERTRADE-->' not in open(os.path.join(SITE,k+'.html'),encoding='utf-8').read()]
    if _miss: print('!!!出页自检失败:以下页面缺PAPERTRADE锚 →',','.join(_miss))
    else: print('出页自检通过:六页PAPERTRADE看板在位')
    # ★重复段标题自检(2026-07-13加:抓"agent手写h2+脚本块自带h2"类重复,lhb资金温度双标题事故)
    import re as _re2
    for _k in ('index','cycle','auction','lhb','theme','logic','limitup'):
        _fp=os.path.join(SITE,_k+'.html')
        if not os.path.exists(_fp): continue
        _hs=[_m.group(1).strip() for _m in _re2.finditer(r'<h2[^>]*>([^<]+)</h2>',open(_fp,encoding='utf-8').read())]
        _dup=sorted({h for h in _hs if _hs.count(h)>1})
        if _dup: print('!!!出页自检失败:'+_k+'页重复段标题 →','; '.join(_dup))


if __name__=='__main__':
    build(sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime('%Y%m%d'))
