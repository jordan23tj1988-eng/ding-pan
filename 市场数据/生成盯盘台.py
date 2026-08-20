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
        blk=html[p:end]
        if blk.count('<div')!=blk.count('</div>'):
            # ★07-15晚事故: div不平衡时严禁end-6盲切(曾把</div>砍成孤立<);原样跳过
            res+=blk; idx=end; continue
        inner=html[p+len('<div class="tl">'):end-len('</div>')]
        items=[]; j=0; prefix=''; trailing=''
        while True:
            mq=_re.compile(r'<div class="tli[^"]*">').search(inner,j)   # ★容错tli mut等变体
            q=mq.start() if mq else -1
            if q<0:
                trailing=inner[j:]; break
            if not items: prefix=inner[j:q]
            e=_match_div(inner,q)
            items.append(inner[q:e]); j=e
        def _dt(it):
            m=_re.search(r'<div class="d">\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',it)
            if m: return m.group(1)
            m2=_re.search(r'<b>([0-9]{2}-[0-9]{2})',it)                  # ★fallback <b>07-15</b>
            return '0000-'+m2.group(1) if m2 else '0000-00-00'
        items=sorted(items,key=_dt,reverse=True)
        res+='<div class="tl">'+prefix+''.join(items)+trailing+'</div>'
        idx=end
    return res

CSS='''
:root{color-scheme:dark;
--bg:#08090f;--panel:#12141c;--panel2:#151824;--line:rgba(255,255,255,.07);--line2:rgba(255,255,255,.13);
--ink:#eceef5;--sub:#a8adbd;--dim:#8d93a8;
--accent:#e8a33d;--accent-dim:#8a6d3b;
--up:#ff5f56;--down:#3fcb86;
--hit:#2fd3c5;--half:#e8a33d;--miss:#ff5f56;
--mono:ui-monospace,"Cascadia Mono","SF Mono",Consolas,"Courier New",monospace}
*{box-sizing:border-box;margin:0;padding:0}
html{scrollbar-color:#2a2e3d var(--bg)}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.68;-webkit-font-smoothing:antialiased}
::selection{background:rgba(232,163,61,.25)}
/* ── nav ── */
.nav{position:sticky;top:0;z-index:9;background:rgba(12,15,21,.92);backdrop-filter:blur(10px);display:flex;gap:2px;align-items:center;padding:11px 18px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.nav .brand{color:var(--accent);font-size:13px;letter-spacing:3px;font-weight:700;margin-right:14px}
.nav a{color:#9aa3b5;text-decoration:none;font-size:13px;padding:5px 11px;border-radius:7px;transition:.15s;border:1px solid transparent}
.nav a:hover{color:var(--ink);border-color:var(--line2)}
.nav a.on{background:var(--accent);color:#14100a;font-weight:700}
.nav .upd{margin-left:auto;color:var(--dim);font-size:11.5px;font-family:var(--mono)}
.wrap{max-width:960px;margin:0 auto;padding:26px 18px 70px}
/* ── hero ── */





.stance{display:flex;gap:9px;flex-wrap:wrap;margin-top:16px}
.pill{background:rgba(255,255,255,.04);border:1px solid var(--line2);padding:5px 13px;border-radius:20px;font-size:12.8px;color:#c9cfdc}
.pill b{color:var(--ink)}
.pill.warn{background:rgba(255,95,86,.1);border-color:rgba(255,95,86,.35);color:#f0b6b4}
/* ── section head ── */


.hint{color:var(--dim);font-size:12.3px;margin:4px 0 14px;padding-left:15px}
/* ── strips/cards ── */
.strip{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.kv{flex:1;min-width:120px;background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:12px 15px}
.kv .l{font-size:11.8px;color:var(--sub)}.kv .v{font-size:20px;font-weight:800;margin-top:3px;font-family:var(--mono);letter-spacing:-.5px}
.dn{color:var(--down)}.up{color:var(--up)}.mut{color:var(--sub)}
.cor{display:inline-block;line-height:1.6}
.cor b{color:var(--ink);font-weight:700}
.cor .mut{margin-left:1px}
.jdx{display:block;line-height:1.55;color:var(--sub);font-size:11.5px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:17px 20px;margin-top:13px}
.card p{font-size:13.6px;color:#b9c1d0}
.card.hotcard{border-color:rgba(255,95,86,.35);background:linear-gradient(135deg,var(--panel),rgba(255,95,86,.05))}
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
.t-attack{background:rgba(47,211,197,.14);color:var(--hit)}.t-watch{background:rgba(232,163,61,.14);color:var(--half)}.t-avoid{background:rgba(255,95,86,.14);color:var(--miss)}
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
.track{height:8px;background:#191f2b;border-radius:5px;overflow:hidden}.track>i{display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,var(--accent-dim),var(--up))}
.track.teal>i{background:linear-gradient(90deg,#1f6a5e,var(--hit))}
.base{font-size:11.5px;color:var(--dim);margin-top:4px}
.ladder{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;align-items:stretch}
.rung{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;text-align:center;min-width:80px;font-size:12.6px}
.rung .lv{font-size:12px;color:var(--sub)}.rung .nm{font-size:12.5px;font-weight:600;margin-top:2px}
.rung.gap{background:rgba(255,95,86,.07);border-style:dashed;border-color:rgba(255,95,86,.4);color:var(--miss)}
.rung.high{border-color:var(--up)}
.rung .tag{display:inline-block;font-size:11px;font-weight:700;color:var(--accent);background:rgba(232,163,61,.12);border-radius:7px;padding:0 7px;margin-right:6px;font-family:var(--mono)}
.foot{margin-top:36px;padding:14px 18px;background:var(--panel2);border:1px solid var(--line);border-radius:11px;font-size:12.2px;color:var(--sub)}.foot b{color:var(--ink)}
.badge{display:inline-block;font-size:11px;padding:1px 8px;border-radius:10px;font-weight:600}
.bA{background:rgba(47,211,197,.14);color:var(--hit)}.bC{background:rgba(232,163,61,.14);color:var(--half)}.bMix{background:rgba(177,138,255,.14);color:#b18aff}
.hlist{list-style:none}.hlist li{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:13px 16px;margin-top:10px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.hlist .dt{font-weight:800;font-size:15px;flex:0 0 96px;font-family:var(--mono)}.hlist .st{flex:1;font-size:13.2px;color:#aab2c2;min-width:200px}
.hlist a.go{color:var(--accent);text-decoration:none;font-size:13px;font-weight:600;white-space:nowrap}
.jjr td{background:rgba(232,163,61,.06);border-bottom:1px solid var(--line);padding:7px 10px 9px;font-size:12.4px;color:#b3a98f}
.jjr .jjtag{display:inline-block;font-size:11px;font-weight:700;color:var(--accent);background:rgba(232,163,61,.14);border-radius:8px;padding:1px 8px;margin-right:8px;white-space:nowrap}
.jpr td{background:rgba(47,211,197,.06);border-bottom:1px solid var(--line);padding:7px 10px 9px;font-size:12.4px;color:#8fbcb0}
.jpr .jptag{display:inline-block;font-size:11px;font-weight:700;color:var(--hit);background:rgba(47,211,197,.14);border-radius:8px;padding:1px 8px;margin-right:8px;white-space:nowrap}
/* ── obs 荐票/观察卡 ── */
.obswrap{margin-top:6px}
.obs{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:0;margin-top:12px;overflow:hidden;transition:border-color .18s}
.obs:hover{border-color:var(--line2)}
.obs-head{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;padding:13px 16px 8px}
.obs-nm{font-weight:800;font-size:14.5px;flex:0 0 auto}.obs-nm .mut{font-weight:400;font-size:12px;margin-left:6px;font-family:var(--mono)}
.obs-pos{flex:1 1 240px;min-width:0;font-size:13px;color:#aab2c2;overflow-wrap:anywhere}
.obs-watch{padding:6px 16px 12px;font-size:13.2px;color:#c4cbd8;overflow-wrap:anywhere;border-bottom:1px solid var(--line)}
.obs-lab,.obs-lab2{display:inline-block;font-size:11px;font-weight:700;border-radius:8px;padding:1px 8px;margin-right:8px;white-space:nowrap}
.obs-lab{color:#f0a5a3;background:rgba(255,95,86,.13)}
.obs-rec{padding:8px 16px;font-size:12.6px;color:#8fbcb0;background:rgba(47,211,197,.05);overflow-wrap:anywhere}
.obs-lab2{color:var(--hit);background:rgba(47,211,197,.14)}
.obs-jj{padding:8px 16px 10px;font-size:12.4px;color:#b3a98f;background:rgba(232,163,61,.05);overflow-wrap:anywhere}
/* ── details 折叠 ── */
details.chain{background:var(--panel);border:1px solid var(--line);border-radius:13px;margin-top:12px;padding:0 18px}
details.chain summary{cursor:pointer;padding:13px 0;font-weight:700;font-size:14px;color:var(--ink);list-style:none;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
details.chain summary::before{content:"\\25B8";color:var(--accent);transition:.15s}
details.chain[open] summary::before{content:"\\25BE"}
details.chain summary .chip{font-size:11.5px;font-weight:600;padding:1px 9px;border-radius:10px;background:rgba(255,255,255,.05);color:var(--sub);border:1px solid var(--line)}
details.chain summary .chip.hot{background:rgba(255,95,86,.13);color:#f0a5a3;border-color:transparent}
details.chain summary .chip.cold{background:rgba(47,211,197,.13);color:var(--hit);border-color:transparent}
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
.hb .hbt i.pos{left:50%;background:linear-gradient(90deg,rgba(255,95,86,.75),rgba(255,95,86,.35));transform-origin:left}
.hb .hbt i.neg{right:50%;background:linear-gradient(270deg,rgba(63,203,134,.75),rgba(63,203,134,.35));transform-origin:right}
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
.stages .st.on{border-color:var(--accent);color:var(--ink);font-weight:700;background:rgba(232,163,61,.09)}
.stages .st small{display:block;font-size:10.5px;color:var(--dim);font-family:var(--mono)}
.posmeter{position:relative;height:12px;border-radius:6px;background:#191f2b;margin-top:12px;overflow:hidden}
.posmeter i{position:absolute;top:0;bottom:0;left:0;background:linear-gradient(90deg,var(--accent-dim),var(--accent));border-radius:6px}
.posmeter em{position:absolute;top:-3px;bottom:-3px;width:2px;background:rgba(255,255,255,.35)}
.posml{display:flex;justify-content:space-between;font-size:10.5px;color:var(--dim);margin-top:4px;font-family:var(--mono)}
/* 六有点 */
.d6{display:inline-flex;gap:3px;vertical-align:middle;margin:0 6px}
.d6 i{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.08);border:1px solid var(--line2)}
.d6 i.on{background:var(--accent);border-color:var(--accent)}
/* 生命周期七段轴(图2) */
.lifeaxis{display:flex;gap:6px;margin-top:10px;overflow-x:auto;padding-bottom:4px}
.lseg{flex:1;min-width:104px;border:1px solid var(--line);border-radius:10px;background:var(--panel2);padding:8px 10px}
.lseg .lt{font-size:12px;font-weight:700;color:var(--dim);text-align:center;padding-bottom:7px;margin-bottom:7px;border-bottom:1px solid var(--line);font-family:var(--mono)}
.lseg.on{border-color:var(--accent);background:rgba(232,163,61,.07)}
.lseg.on .lt{color:var(--accent)}
.lseg .ll{display:block;font-size:11.8px;color:#c4cbd8;padding:3px 0;line-height:1.45}
.lseg .ll b{color:var(--ink);font-weight:700}
.lseg .ll .lwarn{color:#ff8d7b;font-size:11px;font-weight:700}
.lseg .ll.mut{color:var(--sub)}
/* 题材行 */
.trow{padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.trow .tr1{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.trow .tnm{font-weight:750;font-size:13.8px;min-width:110px}
.trow .tjd{font-size:12px;font-weight:700;padding:1px 9px;border-radius:9px}
.tj-main{background:rgba(255,95,86,.13);color:#f0a5a3}.tj-branch{background:rgba(232,163,61,.13);color:var(--half)}.tj-minor{background:rgba(255,255,255,.06);color:var(--sub)}
.trow .tbar{flex:1;min-width:120px;height:12px;background:rgba(255,255,255,.03);border-radius:3px;overflow:hidden;position:relative}
.trow .tbar i{position:absolute;left:0;top:2px;bottom:2px;border-radius:2px;background:linear-gradient(90deg,rgba(232,163,61,.8),rgba(232,163,61,.3));transform-origin:left}
.trow .tct{font-family:var(--mono);font-size:12.5px;font-weight:700;min-width:44px;text-align:right}
.trow .tds{font-size:12.2px;color:var(--sub);margin-top:4px}
/* 竞价池行 */
.pool .hb .hbl{flex-basis:150px}
.sigchip{display:inline-block;font-size:11px;font-weight:700;padding:0 7px;border-radius:7px;margin-left:6px}
.sig-yz{background:rgba(255,95,86,.14);color:#f0a5a3}.sig-mb{background:rgba(255,255,255,.06);color:var(--sub)}
/* 量能台阶梯(站在哪一阶) */
.steps{margin-top:12px}
.step{display:flex;align-items:center;gap:10px;padding:8px 12px;border:1px solid var(--line);border-radius:9px;margin-top:6px;background:var(--panel2)}
.step .sr{flex:0 0 108px;font-family:var(--mono);font-size:12.3px;color:var(--sub);text-align:right}
.step .sn{flex:0 0 170px;font-size:12.8px;font-weight:700}
.step .sn small{display:block;font-weight:400;font-size:11px;color:var(--dim)}
.step .sd{flex:1;display:flex;gap:6px;flex-wrap:wrap;min-height:18px}
.step .dayc{font-family:var(--mono);font-size:11.5px;padding:1px 8px;border-radius:8px;background:rgba(255,255,255,.06);color:var(--sub)}
.step .dayc.now{background:rgba(255,95,86,.2);color:#f6b8b6;font-weight:700}
.step.cur{border-color:var(--accent);background:rgba(232,163,61,.09)}
.step.dim .sn{color:var(--sub);font-weight:600}
@media(max-width:640px){.step .sn{flex-basis:120px}.step .sr{flex-basis:80px}}
/* ── 脚本段浅色inline覆盖(台账/温度卡等,勿改上游脚本) ── */
[style*="#faf7f0"]{background:var(--panel2)!important;color:#aab2c2!important}
[style*="#f3eee1"]{background:rgba(232,163,61,.07)!important;color:#b3a98f!important}
[style*="#fffdf9"],[style*="#f6f4ef"],[style*="#efeae0"]{background:var(--panel)!important;color:var(--ink)!important}
[style*="color:#1e8449"]{color:var(--down)!important}
[style*="color:#c0392b"]{color:var(--up)!important}
[style*="color:#b45309"]{color:var(--half)!important}
[style*="#eae1cc"]{background:rgba(232,163,61,.14)!important;color:var(--accent)!important}
/* ── 进场动画(JS加持,无JS=静态;尊重reduced-motion) ── */

.rv{opacity:0;transform:translateY(12px)}
.rv.on{opacity:1;transform:none;transition:opacity .55s cubic-bezier(.16,1,.3,1),transform .55s cubic-bezier(.16,1,.3,1)}
.on .hbt i,.on .tbar i{animation:growx .7s cubic-bezier(.16,1,.3,1)}
.on .cols i{animation:growy .7s cubic-bezier(.16,1,.3,1)}
@keyframes growx{from{transform:scaleX(0)}}
@keyframes growy{from{transform:scaleY(0)}}


/* ── hero(v4 verdict式:渐变+角辉光,无侧条) ── */
.hero{position:relative;background:linear-gradient(150deg,#181420,var(--panel) 55%);border:1px solid var(--line);border-radius:18px;padding:24px 26px;overflow:hidden}
.hero:before{content:"";position:absolute;inset:0;background:radial-gradient(360px 220px at 92% -12%,rgba(232,163,61,.30),transparent 60%);pointer-events:none;opacity:.6}
.hero .kick{font-size:11px;letter-spacing:2.5px;color:var(--dim);text-transform:uppercase;font-family:var(--mono)}
.hero h1{font-size:24px;margin:9px 0 7px;font-weight:800;letter-spacing:-.3px;color:var(--ink);line-height:1.3;text-wrap:balance}
.hero h1 em{font-style:normal;color:var(--accent)}
.hero p{color:var(--sub);font-size:13.2px;max-width:680px;text-wrap:pretty}

h2{font-size:15.5px;margin:34px 0 4px;font-weight:700;letter-spacing:.3px;color:var(--ink);display:flex;align-items:center;gap:9px}
h2::before{content:"";width:8px;height:8px;border-radius:2px;background:var(--accent);transform:rotate(45deg);flex-shrink:0}
h2.hot::before{background:var(--up)}


/* ══ v4琥珀bento追加层(2026-07-15移植,index bento+全站导航;老组件类全保留在上方) ══ */
.num{font-variant-numeric:tabular-nums;letter-spacing:-.02em;font-family:var(--mono)}
/* 顶部pill导航(主站六页;存档页仍用旧.nav) */
.navbar{display:flex;align-items:center;gap:16px;flex-wrap:wrap;background:rgba(18,20,28,.92);backdrop-filter:blur(10px);
  border:1px solid var(--line);border-radius:20px;padding:10px 16px;box-shadow:0 1px 3px rgba(0,0,0,.4);
  position:sticky;top:10px;z-index:9;margin:12px auto 0;max-width:min(1440px,calc(100% - 32px))}
.navbar .brand{display:flex;align-items:center;gap:10px;padding-right:4px;color:var(--ink);font-weight:700;font-size:15px;letter-spacing:.5px;white-space:nowrap}
.navbar .logo{width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,var(--accent),#c07f22);
  display:grid;place-items:center;color:#141008;font-weight:800;font-size:15px;box-shadow:0 6px 18px rgba(232,163,61,.30)}
.pills{display:flex;align-items:center;gap:3px;background:var(--bg);border-radius:13px;padding:4px;flex-wrap:wrap}
.pills a{padding:7px 13px;border-radius:10px;color:var(--dim);font-size:13px;font-weight:600;text-decoration:none;white-space:nowrap;transition:.16s}
.pills a:hover:not(.on){color:var(--ink)}
.pills a.on{background:var(--accent);color:#141008;font-weight:700}
.pills a:focus-visible{outline:none;box-shadow:0 0 0 3px rgba(232,163,61,.25)}
.navbar .upd{margin-left:auto;color:var(--dim);font-size:11.5px;font-family:var(--mono);max-width:380px;line-height:1.5;display:flex;align-items:center;gap:8px}
.navbar .upd b{color:var(--accent);font-weight:600}
.live{position:relative;width:8px;height:8px;border-radius:50%;background:var(--accent);flex-shrink:0}
.live::after{content:'';position:absolute;inset:-4px;border-radius:50%;border:1px solid var(--accent);opacity:0;animation:pulse 2.2s ease-out infinite}
@keyframes pulse{0%{transform:scale(.4);opacity:.8}70%{transform:scale(1.15);opacity:0}100%{opacity:0}}
/* 行情带(全页唯一marquee) */
.ticker{overflow:hidden;background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:0 0 14px;padding:7px 0;position:relative}
.ticker:before,.ticker:after{content:'';position:absolute;top:0;bottom:0;width:56px;z-index:1;pointer-events:none}
.ticker:before{left:0;background:linear-gradient(90deg,var(--panel),transparent)}
.ticker:after{right:0;background:linear-gradient(270deg,var(--panel),transparent)}
.ticker .in{display:flex;width:max-content;animation:tick 52s linear infinite}
.ticker:hover .in{animation-play-state:paused}
.ticker .grp{display:flex;gap:36px;padding:0 18px;font-family:var(--mono);font-size:12px;color:var(--dim);white-space:nowrap}
.ticker b{font-weight:700;color:var(--ink)}
.ticker b.u{color:var(--up)}.ticker b.d{color:var(--down)}.ticker b.a{color:var(--accent)}
@keyframes tick{to{transform:translateX(-50%)}}

/* chip语义帽 */
.chip2{display:inline-block;font-size:11px;font-weight:700;padding:2px 9px;border-radius:9px;white-space:nowrap}
.c-hit{background:rgba(47,211,197,.12);color:var(--hit)}
.c-half{background:rgba(232,163,61,.13);color:var(--half)}
.c-miss{background:rgba(255,95,86,.12);color:#ff8d86}
.c-mut{background:rgba(255,255,255,.05);color:var(--dim)}
.c-acc{background:rgba(232,163,61,.13);color:var(--accent)}
.c-cool{background:rgba(123,140,255,.13);color:#7b8cff}
.c-mid{background:rgba(232,163,61,.13);color:var(--half)}
.ok{color:var(--accent);font-weight:600}
table.p2{margin:10px 0;width:100%;border-collapse:collapse}
.chip2.c-hot{background:rgba(255,107,107,.14);color:#ff8d7b;border:1px solid rgba(255,107,107,.32)}/* 8/13修复: 机器温度卡自造(偏热档)原无定义=裸奔 */
.chip2.c-warn{background:rgba(232,163,61,.13);color:var(--half);border:1px solid rgba(232,163,61,.32)}/* 8/13修复: 机器卡自造(分歧/警示)原无定义=裸奔 */
/* 8/12修复: LLM自造类(8/11/8/12温度档徽章)原无定义=裸奔, 补中性琥珀(黄金版体系无此类) */
/* index bento网格 */
.wrap:has(.rowA){max-width:1440px}
.rowA{display:grid;grid-template-columns:2.4fr 1fr 1fr 1fr 1fr;gap:14px;margin-bottom:14px;align-items:stretch}
@media(max-width:1080px){.rowA{grid-template-columns:1fr 1fr}.rowA .hero{grid-column:1/-1}}
@media(max-width:560px){.rowA{grid-template-columns:1fr}}
.rowA .hero{margin:0}
.kpi{display:flex;flex-direction:column;gap:7px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 16px;transition:border-color .2s}
.kpi:hover{border-color:rgba(232,163,61,.3)}
.kpi .top{display:flex;justify-content:space-between;align-items:center}
.kpi .ico{width:32px;height:32px;border-radius:10px;background:rgba(232,163,61,.13);display:grid;place-items:center}
.kpi .ico svg{width:16px;height:16px;stroke:var(--accent);fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.kpi .lab{font-size:11.5px;color:var(--sub);letter-spacing:.04em}
.kpi .big{font-size:28px;font-weight:800;color:var(--ink);font-family:var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.5px}
.kpi .big small{font-size:13px;font-weight:600;color:var(--dim);margin-left:2px}
.kpi .sub2{font-size:11.3px;color:var(--dim);line-height:1.45;margin-top:auto}
.kpi .sub2 b{color:var(--sub)}
.kpi .gauge{margin-top:2px}
.spark{width:100%;height:30px;margin-top:2px}
/* index 观察点+右栏 */
.rowC{display:grid;grid-template-columns:1fr 340px;gap:14px;margin-bottom:14px;align-items:start}
@media(max-width:1080px){.rowC{grid-template-columns:1fr}}
.rowC .card{margin-top:0}
.rail{display:flex;flex-direction:column;gap:14px}
.rowE{display:grid;grid-template-columns:1fr 1.35fr;gap:14px;margin-bottom:6px;align-items:start}
@media(max-width:1080px){.rowE{grid-template-columns:1fr}}
.rowE .card{margin-top:0}
/* PAPERTRADE注入块琥珀化覆盖(勿改上游模拟盘引擎;靠inline子串匹配retint) */
[style*="background:#14171e"]{background:linear-gradient(140deg,#171308,var(--panel) 46%)!important;
  border:1px solid rgba(232,163,61,.28)!important;border-radius:18px!important;
  box-shadow:0 12px 44px -18px rgba(232,163,61,.30),0 1px 3px rgba(0,0,0,.4)!important}
[style*="color:#d9a441"]{color:var(--accent)!important}
[style*="color:#e05d5d"]{color:var(--up)!important}
[style*="color:#4caf7d"]{color:var(--down)!important}
[style*="color:#aab3c0"]{color:var(--sub)!important}
[style*="color:#8892a0"]{color:var(--dim)!important}
[style*="color:#d8dee9"]{color:var(--ink)!important}
[style*="border-left:2px solid #3a4150"]{border-left-color:rgba(255,255,255,.13)!important}
'''

JS='''<script>
(function(){
var RM=false; /*2026-07-15用户拍板:私用盯盘台动画常开,不跟随系统'减少动态效果';要恢复无障碍降级,把false改回 matchMedia('(prefers-reduced-motion: reduce)').matches */
/* ★2026-08-17修复(防复发): 进场动画可见性兜底——IO未触发/报错时内容必须最终可见。
   事故: 涨停106只→归位台账明细卡高~3000px,IO threshold:.12需360px+入视口才触发,
   用户矮窗口(788px)滚动位置未达标→.rv保持opacity:0→明细表永久透明"只显示推荐标的"。
   三重保障: ①3.5s定时强制全显(即使IO报错/未触发,内容必现) ②无IntersectionObserver环境直接全显 ③threshold:0+12%提前量(大元素早触发)。 */
setTimeout(function(){document.querySelectorAll('.rv:not(.on)').forEach(function(e){e.classList.add('on')})},3500);
/* 旧机制:IO进场(全站沿用,无依赖) */
function legacy(){
  if(RM)return;
  var els=document.querySelectorAll('.card,.obs,.routes .rt,.kv,.hero,details.chain,.tli,.cols,.gauge,.trow,.kpi,.ticker,.steps .step');
  els.forEach(function(e){e.classList.add('rv')});
  if(!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add('on')});return;}
  var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('on');io.unobserve(en.target)}})},{threshold:0,rootMargin:'0px 0px 12% 0px'});
  els.forEach(function(e){io.observe(e)});
}
/* v4增强:GSAP计数器/sparkline画入(渐进增强;无gsap/RM=静态终态,数字已内联写死) */
function v4(){
  if(RM||typeof gsap==='undefined')return;
  document.querySelectorAll('[data-v]').forEach(function(el){
    var v=parseFloat(el.dataset.v),d=parseInt(el.dataset.dec||'0',10);
    var pre=el.dataset.pre||'',suf=el.dataset.suf||'';
    gsap.to({n:0},{n:v,duration:1.3,ease:'power2.out',onUpdate:function(){
      el.textContent=pre+this.targets()[0].n.toFixed(d)+suf;}});
  });
  document.querySelectorAll('polyline.drawin').forEach(function(p,i){
    var len=p.getTotalLength();p.style.strokeDasharray=len;p.style.strokeDashoffset=len;
    gsap.to(p,{strokeDashoffset:0,duration:1.4,ease:'power2.out',delay:.3+i*.15});
  });
  gsap.from('.kpi .chip2',{scale:.5,opacity:0,duration:.45,ease:'back.out(1.7)',stagger:.05,delay:.4});
}
legacy();
var s=document.createElement('script');
s.src=(location.pathname.indexOf('/archive/')>-1?'../':'')+'lib/gsap.min.js';
s.onload=v4;s.onerror=function(){};
document.head.appendChild(s);
})();
</script>'''

NAV=[('intraday.html','盘中作战'),('index.html','概览'),('cycle.html','周期情绪'),('auction.html','①竞价'),('lhb.html','②龙虎榜'),('theme.html','③主线题材'),('logic.html','④产业逻辑'),('limitup.html','⑤涨停复盘'),('history.html','历史')]
def nav(active,upd):
    s='<nav class="navbar"><span class="brand"><span class="logo">\u76ef</span>\u60c5\u7eea\u76ef\u76d8\u53f0</span><div class="pills">'
    for h,l in NAV:
        s+='<a class="'+('on' if h==active else '')+'" href="'+h+'">'+l+'</a>'
    return s+'</div><span class="upd"><i class="live"></i><span class="txt">\u66f4\u65b0 '+upd+'</span></span></nav>'

def _fold_tl(body):
    """时间线折叠v2(2026-07-11用户拍板):最新1条外露,其余收进details;条目>=2才折;幂等。"""
    res='';idx=0
    while True:
        p=body.find('<div class="tl">',idx)
        if p<0: res+=body[idx:]; break
        j2=_match_div(body,p)
        tl=body[p:j2]
        if tl.count('<div')!=tl.count('</div>'):
            res+=body[idx:j2]; idx=j2; continue   # ★不平衡不折,防切坏
        ds=_re.findall(r'<div class="d">([0-9][0-9-]+)',tl)
        if len(ds)<2:
            ds=_re.findall(r'<div class="tli[^"]*">\s*<b>([0-9-]{4,5})',tl)   # ★fallback <b>07-15</b>
        if len(ds)<2 or 'tlfold' in body[max(0,p-160):p]:
            res+=body[idx:j2]; idx=j2; continue
        inner=tl[len('<div class="tl">'):-len('</div>')]
        items=[];k=0;prefix='';trailing=''
        while True:
            mq=_re.compile(r'<div class="tli[^"]*">').search(inner,k)   # ★容错tli mut
            q=mq.start() if mq else -1
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

_DETTAG=_re.compile(r'<details\b|</details>')
def _match_det(s,start):
    depth=0
    for m in _DETTAG.finditer(s,start):
        if m.group()=='</details>':
            depth-=1
            if depth==0: return m.end()
        else: depth+=1
    return len(s)
def _fold_ledger(body):
    """台账日卡收纳:连续>=3个日期台账<details class="chain">(summary以MM-DD开头)
    → 首条展开+其余装进一个"更早存档"折叠(仿_fold_tl,一处修复所有台账页)。"""
    out='';idx=0;n=len(body)
    while idx<n:
        p=body.find('<details class="chain"',idx)
        if p<0: out+=body[idx:];break
        run=[];q=p
        while q>=0:
            e=_match_det(body,q)
            mm=_re.match(r'<details class="chain"[^>]*><summary><b>(\d{2}-\d{2})',body[q:e])
            if mm is None: break
            run.append((q,e,mm.group(1)))
            nxt=body.find('<details class="chain"',e)
            if nxt<0 or body[e:nxt].strip()!='': break
            q=nxt
        if len(run)>=3:
            out+=body[idx:run[0][0]]
            first=body[run[0][0]:run[0][1]]
            if not _re.match(r'<details class="chain"\s+open',first):
                first=first.replace('<details class="chain"','<details class="chain" open',1)
            rest=body[run[1][0]:run[-1][1]]
            fold=('<details class="chain foldarchive"><summary><b>更早存档</b> '
                  '<span class="chip">'+str(len(run)-1)+'条</span> '
                  '<span class="mut">'+run[-1][2]+' ~ '+run[1][2]+'</span></summary>'
                  '<div class="inner">'+rest+'</div></details>')
            out+=first+fold;idx=run[-1][1]
        else:
            e=_match_det(body,p)
            out+=body[idx:e];idx=e
    return out
FOOT='<div class="foot"><b>\u60c5\u7eea\u76ef\u76d8\u53f0 v4</b> \u00b7 \u6bcf\u592918:00\u66f4\u65b0,\u65e7\u7684\u8fdb\u5386\u53f2\u5b58\u6863 \u00b7 \u4e94\u8def:\u2460\u7ade\u4ef7 \u2461\u9f99\u864e\u699c \u2462\u9898\u6750 \u2463\u4ea7\u903b \u2464\u6da8\u505c</div>'
def shell(title,navbar,body,tick=''):
    return ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>'+title
        +'</title><style>'+CSS+'</style></head><body>'+navbar+'<div class="wrap">'+tick+body+FOOT+'</div>'+JS+'</body></html>')
def _ab_fallback(j, date):
    """archive_body 空时 fallback: 用 bodies 当日 open 块 + 一句话 组装存档(2026-08-12小项7)"""
    bd = (j.get('bodies') or {}).get('limitup') or ''
    i = bd.find('<details class="chain" open>')
    j2 = bd.find('<details class="chain">', i + 10)
    seg = bd[i:j2] if i >= 0 else ''
    one = j.get('一句话', '')
    if not seg:
        return ''
    return ('<div class="card"><b>%s 涨停复盘存档 · 完整档案</b>'
            '<p style="margin:6px 0 0">%s</p></div>%s' % (date, one, seg))


def build(date):
    os.makedirs(ARC,exist_ok=True); os.makedirs(L,exist_ok=True)
    j=json.load(open(os.path.join(L,'judgment_'+date+'.json'),encoding='utf-8'))
    upd=j.get('更新label',date); b=j['bodies']; tick=j.get('ticker','')
    titles=[('index','概览'),('cycle','周期情绪'),('auction','竞价·第一路'),('lhb','龙虎榜·第二路'),('theme','主线题材·第三路'),('logic','产业逻辑·第四路'),('limitup','涨停复盘·第五路')]
    for k,t in titles:
        if k not in b and k not in ('index','cycle', 'auction', 'logic'): continue
        fn=k+'.html'
        if k=='limitup':
            # ★S2(2026-08-11): limitup 走模块化渲染(module_render_limitup.build_page_full)
            # 组件化: 机器组件从数据源渲染 + LLM 组件从 bodies 提取; 已模拟 _fold_tl/_fold_ledger
            # 失败回退原路径(不阻塞生产出页); 其他 6 页原路径不动
            try:
                import module_render_limitup as _mrl
                _pb=_mrl.build_page_full(date)
                if not _pb or '<h2>一' not in _pb:
                    raise RuntimeError('build_page_full 输出异常(len=%d)'%len(_pb))
            except Exception as _e:
                print('!!!limitup 模块化渲染失败,回退原路径:',str(_e)[-200:])
                _pb=_fold_ledger(_fold_tl(_rt(b[k])))
        elif k=='lhb':
            # ★S2(2026-08-12): lhb 走模块化渲染(module_render_lhb.build_page_full)
            # 六板块: 一席位综合判断(LLM) 二资金温度FUNDTEMP(资金温度.py --card权威) 三台账LHBLEDGER(bodies注入段+foldarchive)
            #          四分档库(lhb席位区.py权威) 五自主深挖(LLM) 六认知迭代(LLM+tlfold); 已模拟 _fold_tl/_fold_ledger
            # 失败回退原路径(不阻塞生产出页)
            try:
                import module_render_lhb as _mrl2
                _pb=_mrl2.build_page_full(date)
                if not _pb or '<h2>一' not in _pb:
                    raise RuntimeError('build_page_full 输出异常(len=%d)'%len(_pb))
            except Exception as _e:
                print('!!!lhb 模块化渲染失败,回退原路径:',str(_e)[-200:])
                _pb=_fold_ledger(_fold_tl(_rt(b[k])))
        elif k=='theme':
            # ★S2(2026-08-12): theme 走模块化渲染(module_render_theme.build_page_full)
            # 机器区三卡(战场全貌/6有/四维, 锚点成对可回源) + 黄金版六板块 LLM 原文逐字节保真
            # 失败回退原路径(不阻塞生产出页)
            try:
                import module_render_theme as _mrt
                _pb=_mrt.build_page_full(date)
                if not _pb or '<h2>一' not in _pb:
                    raise RuntimeError('build_page_full 输出异常(len=%d)'%len(_pb))
            except Exception as _e:
                print('!!!theme 模块化渲染失败,回退原路径:',str(_e)[-200:])
                _pb=_fold_ledger(_fold_tl(_rt(b[k])))
        elif k=='cycle':
            # ★S2(2026-08-12): cycle 走模块化渲染(module_render_cycle.build_page_full)
            # 机器区四卡(量能台阶/先行指标/连板梯队/五路投票, 锚点成对可回源) + 黄金版七板块 LLM 原文逐字节保真
            # 8/11 起晚间管道未产 cycle body → 渲染器自产断档卡(零编造); 失败回退原路径(不阻塞生产出页)
            try:
                import module_render_cycle as _mrc
                _pb=_mrc.build_page_full(date)
                if not _pb:
                    raise RuntimeError('build_page_full 输出异常(len=%d)'%len(_pb))
            except Exception as _e:
                print('!!!cycle 模块化渲染失败,回退原路径:',str(_e)[-200:])
                _pb=_fold_ledger(_fold_tl(_rt(b.get('cycle',''))))
        elif k=='auction':
            # ★S2(2026-08-12): auction 走模块化渲染(module_render_auction.build_page_full)
            # 机器区三卡(竞价选股池/昨池结算/信号胜率库, 锚点成对可回源, MACHSCORE/MACHPOOL/MACHSIG)
            # + LLM body 整段逐字节保真(7/16旧八段与8/12新六段两种格式都保真)
            # 无 body 日(如8/11) → 自产事实性 hero + 机器折叠区三卡(当日真实数据) + 断档卡
            # 失败回退原路径(不阻塞生产出页)
            try:
                import module_render_auction as _mra
                _pb=_mra.build_page_full(date)
                if not _pb or '<h2>' not in _pb:
                    raise RuntimeError('build_page_full 输出异常(len=%d)'%len(_pb))
            except Exception as _e:
                print('!!!auction 模块化渲染失败,回退原路径:',str(_e)[-200:])
                _pb=_fold_ledger(_fold_tl(_rt(b.get('auction',''))))
        elif k=='logic':
            # ★S2(2026-08-12): logic 走模块化渲染(module_render_logic.build_page_full)
            # 机器折叠区三卡(链条深度地图库/中报预增雷达漏斗/荐票历史结算, 锚点成对可回源,
            #   MACHCHAIN/MACHRADAR/MACHHIST) + LLM body 整段逐字节保真(7/16旧七段与8/12新六段都保真)
            # 无 body 日(如8/11) → 自产事实性 hero + 机器折叠区三卡(当日真实数据) + 断档卡
            # 失败回退原路径(不阻塞生产出页)
            try:
                import module_render_logic as _mrl
                _pb=_mrl.build_page_full(date)
                if not _pb or '<h2>' not in _pb:
                    raise RuntimeError('build_page_full 输出异常(len=%d)'%len(_pb))
            except Exception as _e:
                print('!!!logic 模块化渲染失败,回退原路径:',str(_e)[-200:])
                _pb=_fold_ledger(_fold_tl(_rt(b.get('logic',''))))
        elif k=='index':
            # ★S2(2026-08-12): index 走模块化渲染(module_render_index.build_page_full), 六页模块化收官
            # 有 body 日: 头部(hero/kpi/stance+竞价兑现卡)原文保真 + 五板块物理h2切块逐字节保真
            #   + 认知迭代折叠(_fold_tl同语义) —— 与旧路径输出逐字节一致(已验证7/16/8/12)
            # 无 body 日(如8/11): 自产事实性 hero + 机器折叠区三卡(IDXTEMP温度/IDXLEAD先行指标/
            #   IDXVOTE五路投票, 当日真实数据可回源) + 断档卡 —— 根治"无body残留旧日期页"
            # 失败回退原路径(不阻塞生产出页)
            try:
                import module_render_index as _mri
                _pb=_mri.build_page_full(date)
                if not _pb:
                    raise RuntimeError('build_page_full 输出异常(len=%d)'%len(_pb))
            except Exception as _e:
                print('!!!index 模块化渲染失败,回退原路径:',str(_e)[-200:])
                _pb=_fold_ledger(_fold_tl(_rt(b.get('index',''))))
        else:
            _pb=_fold_ledger(_fold_tl(_rt(b[k])))
        open(os.path.join(SITE,fn),'w',encoding='utf-8',newline='\n').write(shell('情绪盯盘台 · '+t,nav(fn,upd),_pb,tick))
    topbar='<div class="nav"><span class="brand">情绪盯盘台 · 存档</span><a href="../index.html">← 返回概览</a><a href="../history.html">历史列表</a><span class="upd">冻结于 '+upd+'</span></div>'
    # ★2026-08-12小项7根治: archive_body 空(LLM漏写)→fallback 当日bodies当日块, 存档页禁止空壳
    ab8 = j.get('archive_body') or _ab_fallback(j, date)
    open(os.path.join(ARC,date+'.html'),'w',encoding='utf-8',newline='\n').write(shell('复盘存档 '+date,topbar,_rt(ab8),tick))
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
    open(os.path.join(SITE,'history.html'),'w',encoding='utf-8',newline='\n').write(shell('情绪盯盘台 · 历史',nav('history.html',upd),hb,tick))
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
    # ★2026-08-12(用户指示补上): 交易计划存在性校验(六路) — 复盘断供→荐票→交易计划静默缺失的告警
    # 交易计划_{route}_{date}.json 由晚间管道(复盘→荐票→agent决策)生成; 缺失=上游断供,当晚即应告警而非静默
    _plans_miss = [_r for _r in ('lhb', 'auction', 'theme', 'logic', 'limitup', 'master')
                   if not os.path.exists(os.path.join(L, '交易计划_%s_%s.json' % (_r, date)))]
    if _plans_miss: print('!!!交易计划缺失(晚间管道应生成,缺失=上游复盘断供):', ','.join(_plans_miss))
    else: print('交易计划自检通过:六路计划在位')
    # ★2026-08-12 P2阶段2: 每晚出版时跑五路认知库蒸馏(次日复盘读子agent增强/最新日期文件)
    _kb = os.path.join(BASE, '_认知库蒸馏_五路.py')
    if os.path.exists(_kb):
        _r = subprocess.run([sys.executable, _kb], capture_output=True, text=True)
        if _r.returncode != 0: print('!!!认知库蒸馏失败:', ((_r.stderr or _r.stdout) or '')[-300:])
        elif _r.stdout: print(_r.stdout.strip())
    else:
        print('!!!未找到 _认知库蒸馏_五路.py,认知库未更新')
    # ★重复段标题自检(2026-07-13加:抓"agent手写h2+脚本块自带h2"类重复,lhb资金温度双标题事故)
    import re as _re2
    for _k in ('index','cycle','auction','lhb','theme','logic','limitup'):
        _fp=os.path.join(SITE,_k+'.html')
        if not os.path.exists(_fp): continue
        _hs=[_m.group(1).strip() for _m in _re2.finditer(r'<h2[^>]*>([^<]+)</h2>',open(_fp,encoding='utf-8').read())]
        _dup=sorted({h for h in _hs if _hs.count(h)>1})
        if _dup: print('!!!出页自检失败:'+_k+'页重复段标题 →','; '.join(_dup))
    # ★index 组件类名断言(2026-08-12加: 用户"完全复刻黄金版组件"拍板后; 防 LLM body 自造裸奔类 .b/.h/.st)
    #   黄金版 index 核心组件必须全部在位; 缺失/自造 = 样式裸奔, 禁止发布
    _ifp=os.path.join(SITE,'index.html')
    if os.path.exists(_ifp):
        _ih=open(_ifp,encoding='utf-8').read()
        _ib=_ih[_ih.find('<body'):_ih.rfind('</body>')]
        _need=('class="obs"','class="obs-head"','class="gauge"','class="hb"',
               'class="routes"','class="rtn"','class="tli"','class="kpi"',
               'class="rowC"','class="rowE"','class="hero"','class="stance"')
        _miss_comp=[c for c in _need if c not in _ib]
        if _miss_comp: print('!!!出页自检失败:index缺黄金版组件 → '+','.join(_miss_comp))
        # 自造裸奔类: CSS 无定义的 class 出现在 body(白名单: 动画/复合类)
        # ★2026-08-12 v2: 遍历多类名每个类(原 .split()[0] 只查首个类, class="hero xyzzy" 会漏检 xyzzy)
        _cssm=_re2.search(r'<style[^>]*>(.*?)</style>',_ih,_re2.S)
        _css=_cssm.group(1) if _cssm else ''
        _bare=sorted({_c for _m in _re2.finditer(r'class="([a-z][^"]*)"',_ib) for _c in _m.group(1).split()
            if not _re2.search(r'\.%s\b'%_re2.escape(_c),_css)
            and _c not in ('up','dn','mut','pos','neg','tag','inner','drawin','on','hot','warn','cold','a','u','d','rv','live','txt','st','dayc','now','cur','dim','bar','fines','tlfold','chain')})
        if _bare: print('!!!出页自检失败:index自造裸奔类(CSS无定义) → '+','.join(_bare))
        if not _miss_comp and not _bare: print('index组件自检通过:黄金版组件在位,无裸奔类')
    # ★limitup 数字核对哨兵(2026-08-11加: bodies手写数字 vs 数据源 内容级核对;
    #   历史事故: 高标张冠李戴/抄昨日板数/温度抄错 全靠用户逐卡验收才显形)
    #   FAIL 不阻断出页(页面已生成), 但打印醒目错误, 强制人工复核后才能发布
    _lf=os.path.join(BASE,'limitup数据核对.py')
    if os.path.exists(_lf):
        _lr=subprocess.run([sys.executable,_lf,date],capture_output=True,text=True)
        if _lr.returncode!=0:
            print('!!!limitup数据核对 FAIL — 页面数字与数据源不一致, 禁止发布!')
            for _ln in (_lr.stdout or '').strip().split('\n'):
                if '✗' in _ln or 'FAIL' in _ln: print('    '+_ln.strip())
        elif _lr.stdout:
            print(_lr.stdout.strip().split('\n')[-1])
    else:
        print('!!!未找到 limitup数据核对.py, 数字核对跳过')
    # ★lhb 数字核对哨兵(2026-08-12加: 台账三数/分档库窗口档数/FUNDTEMP表/锚点/负面验证 内容级核对)
    #   FAIL 不阻断出页(页面已生成), 但打印醒目错误, 强制人工复核后才能发布
    _lf2=os.path.join(BASE,'lhb数据核对.py')
    if os.path.exists(_lf2):
        _lr2=subprocess.run([sys.executable,_lf2,date],capture_output=True,text=True)
        if _lr2.returncode!=0:
            print('!!!lhb数据核对 FAIL — 页面数字与数据源不一致, 禁止发布!')
            for _ln in (_lr2.stdout or '').strip().split('\n'):
                if '✗' in _ln or 'FAIL' in _ln: print('    '+_ln.strip())
        elif _lr2.stdout:
            print(_lr2.stdout.strip().split('\n')[-1])
    else:
        print('!!!未找到 lhb数据核对.py, 数字核对跳过')
    # ★cycle 数字核对哨兵(2026-08-13接线: 脚本8/12已存在但生成器漏接=哨兵不跑形同虚设)
    #   FAIL 不阻断出页(页面已生成), 但打印醒目错误, 强制人工复核后才能发布
    _lf3=os.path.join(BASE,'cycle数据核对.py')
    if os.path.exists(_lf3):
        _lr3=subprocess.run([sys.executable,_lf3,date],capture_output=True,text=True)
        if _lr3.returncode!=0:
            print('!!!cycle数据核对 FAIL — 页面数字与数据源不一致, 禁止发布!')
            for _ln in (_lr3.stdout or '').strip().split('\n'):
                if '✗' in _ln or 'FAIL' in _ln: print('    '+_ln.strip())
        elif _lr3.stdout:
            print(_lr3.stdout.strip().split('\n')[-1])
    else:
        print('!!!未找到 cycle数据核对.py, 数字核对跳过')
    # ★theme 数字核对哨兵(2026-08-19接线: 脚本8/12已存在但生成器漏接=哨兵不跑形同虚设;
    #   8/17-8/19三连"三 主流生命周期 LLM定性判断/判据缺失"根因之一=结构化json漏产无人拦;
    #   0a闸门: 题材生命周期判断/龙头判断 json 必须存在+键齐全, 缺=FAIL 禁止发布)
    #   FAIL 不阻断出页(页面已生成), 但打印醒目错误, 强制人工复核后才能发布
    _lf4=os.path.join(BASE,'theme数据核对.py')
    if os.path.exists(_lf4):
        _lr4=subprocess.run([sys.executable,_lf4,date],capture_output=True,text=True)
        if _lr4.returncode!=0:
            print('!!!theme数据核对 FAIL — 页面数字与数据源不一致, 禁止发布!')
            for _ln in (_lr4.stdout or '').strip().split('\n'):
                if '✗' in _ln or 'FAIL' in _ln: print('    '+_ln.strip())
        elif _lr4.stdout:
            print(_lr4.stdout.strip().split('\n')[-1])
    else:
        print('!!!未找到 theme数据核对.py, 数字核对跳过')


if __name__=='__main__':
    build(sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime('%Y%m%d'))
