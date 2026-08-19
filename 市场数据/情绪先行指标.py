#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""情绪先行指标.py —— 周期页三条先行序列(P0-1,2026-07-11评估落地)。
一 晋级率: 1进2=今日'2天2板'/昨日首板; 2进3=今日'3天3板'/昨日'2天2板';
   高度晋级=今日连续板(N天N板)且N>=3 / 昨日连续板且N>=2。数据=THS三池250日(无ST口径),缺日用本地zt_pool(过滤ST/退/N/C)兜底。
二 昨日涨停溢价(执行口径=今开买->今收): 当日模式用东财spot全场快照一次拉取;
   历史回填只用 _竞价池结算.jsonl 已有的"全场涨停均收"(零编造,更早标null)。
三 大面率=昨日涨停票今日涨跌幅<-5%占比(spot当日起,不回填);
   核按钮率=昨日涨停∩今日跌停/昨日涨停(本地dt_pool可回填,与大面率分开命名不混口径)。
产出: _学习/_情绪先行指标.json {date:{...}};print摘要供agent引用。
用法: python3 情绪先行指标.py [YYYYMMDD]   # 算指定日(默认最新THS日)
      python3 情绪先行指标.py --backfill    # 全量回填晋级率/核按钮/溢价(结算jsonl部分)
铁律: 零编造(拿不到标null)/零后视镜(全部T日收盘后可知)/不覆盖发出版任何文件。
"""
import os, sys, json, re
import pandas as pd
try:
    from trading_calendar import load_trading_calendar
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from trading_calendar import load_trading_calendar

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
THS = os.path.join(L, "_ths_zt_pool.json")
OUT = os.path.join(L, "_情绪先行指标.json")
PAT = re.compile(r'(\d+)天(\d+)板')

def is_junk(name):
    """ST/退市整理/新股(N/C)统一过滤——与波段战法剔ST规则对齐。"""
    s = str(name or "")
    return ("ST" in s.upper()) or ("退" in s) or s.startswith("N") or s.startswith("C")

def _hd(x):
    """high_days -> (连续天数,板数,是否连续). '首板'/None=(1,1,True); 'N天M板'=(N,M,N==M)。"""
    s = str(x or "")
    m = PAT.search(s)
    if not m:
        return (1, 1, True)
    n, mm = int(m.group(1)), int(m.group(2))
    return (n, mm, n == mm)

def load_ths():
    if not os.path.isfile(THS):
        return {}
    return json.load(open(THS, encoding="utf-8"))

def pool_of(d, ths):
    """某日涨停池 -> [(code,连续天数,板数,连续)] 。THS优先(本身无ST);缺日用本地zt_pool(过滤junk)。"""
    if d in ths:
        rows = ths[d]
        out = []
        for r in rows:
            if is_junk(r.get("name")):
                continue
            n, m, cons = _hd(r.get("high_days"))
            out.append((str(r.get("code", "")).zfill(6), n, m, cons))
        return out, "ths"
    zp = os.path.join(BASE, d, "zt_pool.csv")
    if not os.path.isfile(zp):
        return None, None
    z = pd.read_csv(zp, dtype={"代码": str})
    z = z[~z["名称"].astype(str).map(is_junk)]
    out = []
    for _, r in z.iterrows():
        try:
            lb = int(float(r.get("连板数", 1)))
        except Exception:
            lb = 1
        # 本地池无"N天M板",涨停统计字段形如 '3/2' (N天/M板)
        n = lb
        st = str(r.get("涨停统计", "") or "")
        mm = re.match(r'(\d+)/(\d+)', st)
        if mm:
            n = int(mm.group(1))
        out.append((str(r["代码"]).zfill(6), n, lb, n == lb))
    return out, "local"

def promo(d, dprev, ths):
    """晋级率块(纯池数学,T日收盘后可知)。"""
    cur, src = pool_of(d, ths)
    prev, _ = pool_of(dprev, ths) if dprev else (None, None)
    if cur is None:
        return None
    n_first = sum(1 for c in cur if c[2] == 1)
    n_2b = sum(1 for c in cur if c[2] == 2 and c[3])          # 2天2板(连续)
    n_3b = sum(1 for c in cur if c[2] == 3 and c[3])          # 3天3板
    n_hi2 = sum(1 for c in cur if c[2] >= 2 and c[3])
    n_hi3 = sum(1 for c in cur if c[2] >= 3 and c[3])
    blk = {"来源": src, "涨停数_净": len(cur), "首板": n_first, "二连板": n_2b, "三连板": n_3b}
    if prev is not None:
        p_first = sum(1 for c in prev if c[2] == 1)
        p_2b = sum(1 for c in prev if c[2] == 2 and c[3])
        p_hi2 = sum(1 for c in prev if c[2] >= 2 and c[3])
        blk["一进二率"] = round(n_2b / p_first, 3) if p_first else None
        blk["二进三率"] = round(n_3b / p_2b, 3) if p_2b else None
        blk["高度晋级率"] = round(n_hi3 / p_hi2, 3) if p_hi2 else None
    else:
        blk["一进二率"] = blk["二进三率"] = blk["高度晋级率"] = None
    return blk

def nuke(d, dprev):
    """核按钮率=昨日涨停∩今日跌停/昨日涨停(本地池对撞,可回填)。"""
    if not dprev:
        return None
    zp = os.path.join(BASE, dprev, "zt_pool.csv")
    dp = os.path.join(BASE, d, "dt_pool.csv")
    if not (os.path.isfile(zp) and os.path.isfile(dp)):
        return None
    z = pd.read_csv(zp, dtype={"代码": str})
    z = z[~z["名称"].astype(str).map(is_junk)]
    t = pd.read_csv(dp, dtype={"代码": str})
    if "名称" in t.columns:
        t = t[~t["名称"].astype(str).map(is_junk)]
    zs = set(z["代码"].str.zfill(6))
    ds = set(t["代码"].str.zfill(6))
    if not zs:
        return None
    hit = len(zs & ds)
    return {"昨日涨停数": len(zs), "今日跌停回杀": hit, "核按钮率": round(hit / len(zs), 3)}

def premium_spot(d, dprev):
    """昨日涨停溢价+大面率:仅当d=当天且盘后,用spot一次全场快照。拿不到标null。"""
    import datetime
    if d != datetime.date.today().strftime("%Y%m%d"):
        return None
    zp = os.path.join(BASE, dprev, "zt_pool.csv") if dprev else None
    if not (zp and os.path.isfile(zp)):
        return None
    try:
        import akshare as ak
        sp = ak.stock_zh_a_spot_em()
    except Exception as e:
        print("  [spot失败,溢价标null] " + str(e))
        return None
    sp["代码"] = sp["代码"].astype(str).str.zfill(6)
    sp = sp.set_index("代码")
    z = pd.read_csv(zp, dtype={"代码": str})
    z = z[~z["名称"].astype(str).map(is_junk)]
    exe, pct = [], []
    for c in z["代码"].str.zfill(6):
        if c not in sp.index:
            continue
        r = sp.loc[c]
        o = pd.to_numeric(r.get("今开"), errors="coerce")
        cl = pd.to_numeric(r.get("最新价"), errors="coerce")
        ch = pd.to_numeric(r.get("涨跌幅"), errors="coerce")
        if pd.notna(o) and o > 0 and pd.notna(cl):
            exe.append((cl - o) / o * 100)
        if pd.notna(ch):
            pct.append(ch)
    if not exe:
        return None
    n = len(exe)
    return {"样本": n,
            "执行均收": round(sum(exe) / n, 2),
            "执行胜率": round(sum(1 for x in exe if x > 0) / n, 3),
            "再封率": round(sum(1 for x in pct if x >= 9.7) / len(pct), 3) if pct else None,
            "大面率": round(sum(1 for x in pct if x < -5) / len(pct), 3) if pct else None,
            "来源": "spot"}

def load_out():
    return json.load(open(OUT, encoding="utf-8")) if os.path.isfile(OUT) else {}

def save_out(t):
    json.dump(t, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def settle_premium_backfill(t):
    """溢价回填:只搬 _竞价池结算.jsonl 里已算好的全场涨停均收(执行口径),零编造。
    ★A(2026-08-16):池日=T,均收=T+1执行→记到紧邻下一交易日(交易日历)。T+1不在序列(复盘缺日/停机)则丢弃,防跨断档错配(7/16的-2.53曾错配到8/11)。"""
    p = os.path.join(L, "_竞价池结算.jsonl")
    if not os.path.isfile(p):
        return
    cal = load_trading_calendar()
    idx = {d: i for i, d in enumerate(cal)}
    for ln in open(p, encoding="utf-8"):
        try:
            r = json.loads(ln)
        except Exception:
            continue
        dpool = str(r.get("池日", ""))
        v = r.get("全场涨停均收")
        if not dpool or v is None:
            continue
        i = idx.get(dpool)
        if i is None or i + 1 >= len(cal):
            continue
        nxt = cal[i + 1]
        if nxt in t and t[nxt].get("昨日涨停溢价") is None:
            t[nxt]["昨日涨停溢价"] = {"执行均收": v, "来源": "竞价池结算jsonl"}

def run_day(d, ths, t, with_spot=True):
    days = sorted(ths.keys())
    if d in days:
        i = days.index(d)
        dprev = days[i - 1] if i > 0 else None
    else:
        dprev = max([x for x in days if x < d], default=None)
    row = t.get(d, {})
    row["晋级"] = promo(d, dprev, ths)
    nk = nuke(d, dprev)
    if nk:
        row["核按钮"] = nk
    if with_spot and dprev:
        pm = premium_spot(d, dprev)
        if pm:
            row["昨日涨停溢价"] = pm
    row.setdefault("昨日涨停溢价", row.get("昨日涨停溢价"))
    t[d] = row
    return row

def summary_line(d, row):
    j = row.get("晋级") or {}
    pm = row.get("昨日涨停溢价") or {}
    nk = row.get("核按钮") or {}
    def f(v, mul=100, suf="%"):
        return ("%.1f%s" % (v * mul, suf)) if isinstance(v, (int, float)) else "null"
    print("%s 净涨停%s 首板%s 1进2 %s | 2进3 %s | 高度晋级 %s | 昨停溢价 %s | 大面率 %s | 核按钮 %s" % (
        d, j.get("涨停数_净", "?"), j.get("首板", "?"),
        f(j.get("一进二率")), f(j.get("二进三率")), f(j.get("高度晋级率")),
        (str(pm.get("执行均收")) + "%") if pm.get("执行均收") is not None else "null",
        f(pm.get("大面率")) if pm.get("大面率") is not None else "null",
        f(nk.get("核按钮率")) if nk.get("核按钮率") is not None else "null"))

def triggers(d, t):
    """三条A档择时窗(阈值=冰点触发器回测.py 2026-07-11定稿;样本域2025-07~2026-07单牛市周期,小样本如实标注)。
    ★复合"≥2转机分量"硬条件已被回测证伪(250日仅触发1次且为负),不采用;分量只作叙事参考。"""
    msgs = []
    tp = os.path.join(L, "_市场温度表.json")
    temp = None
    if os.path.isfile(tp):
        T = json.load(open(tp, encoding="utf-8"))
        temp = (T.get(d) or {}).get("温度")
    if temp is not None:
        if temp < 25:
            msgs.append("★冰点进攻窗(温度%.1f<25): A档回测次日接力y1均+0.30%%/胜率60%%(n=15日/12独立段,全样本基准-0.21%%/45%%)——冰点敢喊进攻,试错接力环境转正;小样本+单牛市周期,给环境判断不给指令" % temp)
        if temp >= 85:
            msgs.append("★过热禁追窗(温度%.1f≥85): A档回测0/6全负,y1均-1.86%%(4独立段)——禁追买;与资金温度>90分位共振=最高级别警报" % temp)
    days = sorted(x for x in t if x <= d)
    if len(days) >= 3:
        ps = [(t[x].get("昨日涨停溢价") or {}).get("执行均收") for x in days[-3:]]
        if all(p is not None and p < 0 for p in ps):
            msgs.append("★洗出反弹窗(昨停溢价连负3日): A档回测次日y1均+0.46%%/胜率65%%(n=34)——绞肉出清后概率反弹;只反弹不反转(y5衰减至+0.13%%),低吸不追高")
    return msgs


def card(d, t):
    """--card: 深色先行指标卡(cycle页段二嵌入)+index灯条。A档脚本段,agent只嵌不改数。"""
    ds = [x for x in sorted(t) if x <= d][-20:]
    if not ds:
        print("无数据"); return
    zt, j12, prem, labs = [], [], [], []
    for x in ds:
        jj = t[x].get("晋级") or {}
        zt.append(jj.get("涨停数_净"))
        j12.append(jj.get("一进二率"))
        prem.append((t[x].get("昨日涨停溢价") or {}).get("执行均收"))
        labs.append(x[4:6] + "-" + x[6:8])
    n = len(ds)
    # 温度
    temp = wg = None
    tp = os.path.join(L, "_市场温度表.json")
    if os.path.isfile(tp):
        T = json.load(open(tp, encoding="utf-8"))
        temp = (T.get(d) or {}).get("温度"); wg = (T.get(d) or {}).get("温度档")
    trig = t[d].get("触发器") or []
    hit = {"ice": any("冰点进攻窗" in m for m in trig),
           "hot": any("过热禁追窗" in m for m in trig),
           "wash": any("洗出反弹窗" in m for m in trig)}
    # ---- SVG1 背离图: 涨停数柱(灰) x 1进2率(金线,右轴) ----
    X0, X1, YT, YB = 46, 866, 20, 172
    span = (X1 - X0) / n; bw = span * 0.52
    mz = max([v for v in zt if v is not None] or [1])
    mj = max([v * 100 for v in j12 if v is not None] or [10]); mj = max(25.0, mj * 1.15)
    bars, pts, dots, dl = "", [], "", ""
    for i, x in enumerate(ds):
        cx = X0 + span * i + span / 2
        if zt[i] is not None:
            h = (YB - YT) * zt[i] / mz
            hot = ' fill="#7d5a63"' if x == d else ' fill="#4a5666"'
            bars += f'<rect x="{cx-bw/2:.1f}" y="{YB-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="1.5"{hot}/>'
            bars += f'<text x="{cx:.1f}" y="{YB-h-3:.0f}" font-size="8" fill="#6b7683" text-anchor="middle">{zt[i]}</text>'
        if j12[i] is not None:
            y = YB - (YB - YT) * (j12[i] * 100) / mj
            pts.append(f"{cx:.1f},{y:.1f}")
            dots += f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="3" fill="#d9a441"/>'
            if i >= n - 1:
                dots += f'<text x="{cx:.1f}" y="{y-7:.1f}" font-size="10" font-weight="700" fill="#d9a441" text-anchor="end">{j12[i]*100:.1f}%</text>'
        if i % 2 == (n - 1) % 2:
            dl += f'<text x="{cx:.1f}" y="{YB+13}" font-size="8.5" fill="#6b7683" text-anchor="middle">{labs[i]}</text>'
    yref = YB - (YB - YT) * 10 / mj
    svg1 = (f'<svg viewBox="0 0 880 196" style="width:100%;height:auto;display:block">'
        f'<line x1="{X0}" y1="{YB}" x2="{X1}" y2="{YB}" stroke="#3a3f46"/>'
        f'<line x1="{X0}" y1="{yref:.1f}" x2="{X1}" y2="{yref:.1f}" stroke="#8a6d2f" stroke-dasharray="4 4" stroke-width="0.8"/>'
        f'<text x="{X1}" y="{yref-3:.1f}" font-size="8.5" fill="#8a6d2f" text-anchor="end">1进2率10%=接力冰点参考线</text>'
        f'{bars}<polyline points="{" ".join(pts)}" fill="none" stroke="#d9a441" stroke-width="1.8"/>{dots}{dl}'
        f'<text x="{X0}" y="12" font-size="9" fill="#98a0ab">灰柱=净涨停数(剔ST,峰{mz}) · 金线=1进2率(右满刻度{mj:.0f}%)</text></svg>')
    # ---- SVG2 溢价红绿柱 ----
    MID, AMP = 88, 58
    vals = [v for v in prem if v is not None]
    ma = max([abs(v) for v in vals] or [1.0])
    bars2, dl2, wash = "", "", ""
    for i, x in enumerate(ds):
        cx = X0 + span * i + span / 2
        v = prem[i]
        if v is None:
            bars2 += f'<text x="{cx:.1f}" y="{MID-4}" font-size="8" fill="#4a5666" text-anchor="middle">∅</text>'
        else:
            h = AMP * abs(v) / ma
            if v >= 0:
                bars2 += f'<rect x="{cx-bw/2:.1f}" y="{MID-h:.1f}" width="{bw:.1f}" height="{max(h,1):.1f}" rx="1.5" fill="#d64541"/>'
            else:
                bars2 += f'<rect x="{cx-bw/2:.1f}" y="{MID:.1f}" width="{bw:.1f}" height="{max(h,1):.1f}" rx="1.5" fill="#2f9e6e"/>'
            if abs(v) == ma or i == n - 1:
                yy = MID - h - 4 if v >= 0 else MID + h + 10
                bars2 += f'<text x="{cx:.1f}" y="{yy:.1f}" font-size="8.5" fill="#98a0ab" text-anchor="middle">{v:+.1f}</text>'
        if i >= 2 and all(prem[i-m] is not None and prem[i-m] < 0 for m in range(3)):
            wash += f'<circle cx="{cx:.1f}" cy="{MID+AMP+9}" r="2.6" fill="#d9a441"/>'
        if i % 2 == (n - 1) % 2:
            dl2 += f'<text x="{cx:.1f}" y="{MID+AMP+22}" font-size="8.5" fill="#6b7683" text-anchor="middle">{labs[i]}</text>'
    svg2 = (f'<svg viewBox="0 0 880 182" style="width:100%;height:auto;display:block">'
        f'<line x1="{X0}" y1="{MID}" x2="{X1}" y2="{MID}" stroke="#3a3f46"/>'
        f'{bars2}{wash}{dl2}'
        f'<text x="{X0}" y="12" font-size="9" fill="#98a0ab">昨停溢价=昨日涨停池今日开盘买→收盘均收(执行口径,%);红正绿负;金点=连负≥3日(洗出反弹窗条件)</text></svg>')
    # ---- 三窗灯 ----
    def lamp(on, name, icon, cond, rec, ctone):
        if on:
            return (f'<div style="flex:1;min-width:190px;border:1px solid {ctone};border-radius:8px;padding:8px 10px;background:rgba(217,164,65,.06)">'
                f'<div style="font-weight:700;font-size:13px;color:{ctone}">{icon} {name} · 触发</div>'
                f'<div style="font-size:11px;color:#98a0ab;margin-top:2px">{cond} · A档:{rec}</div></div>')
        return (f'<div style="flex:1;min-width:190px;border:1px solid #33383f;border-radius:8px;padding:8px 10px">'
            f'<div style="font-weight:700;font-size:13px;color:#5b636d">{icon} {name} · 灭</div>'
            f'<div style="font-size:11px;color:#5b636d;margin-top:2px">{cond} · A档:{rec}</div></div>')
    lamps = ('<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">'
        + lamp(hit["ice"], "冰点进攻窗", "❄", "温度<25", "y1+0.30%/胜率60%(n=15/12段)", "#4fb3aa")
        + lamp(hit["hot"], "过热禁追窗", "☢", "温度≥85", "0/6全负·-1.86%", "#d64541")
        + lamp(hit["wash"], "洗出反弹窗", "♨", "溢价连负3日", "+0.46%/65%(n=34)·只反弹不反转", "#d9a441") + "</div>")
    tstr = ("%.1f·%s" % (temp, wg)) if temp is not None else "null"
    html = ('<div class="card"><p style="font-weight:700;margin-bottom:2px">情绪先行指标 · 近20日 '
        f'<span class="mut" style="font-weight:400">(脚本段A档 · 情绪先行指标.py --card · 当日温度 {tstr},阈值冰点&lt;25/过热≥85)</span></p>'
        + svg1 + svg2 + lamps
        + '<div style="font-size:11px;color:#6b7683;margin-top:8px">读法:柱线剪刀口张开(涨停创高而金线趴地)=数量繁荣×接力冰点;三窗战绩=2025-07~2026-07单牛市周期回测,小样本,给环境判断不给指令。已证伪:复合"冰点+≥2转机分量"硬条件。</div></div>')
    p1 = os.path.join(L, f"先行指标卡_{d}.html")
    open(p1, "w", encoding="utf-8").write(html)
    # ---- index灯条 ----
    def chip(on, txt, ctone):
        if on:
            return f'<span style="padding:2px 10px;border-radius:99px;border:1px solid {ctone};color:{ctone};background:rgba(217,164,65,.07);font-weight:700">{txt}·触发</span>'
        return f'<span style="padding:2px 10px;border-radius:99px;border:1px solid #33383f;color:#5b636d">{txt}·灭</span>'
    strip = ('<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:0 0 10px;font-size:12px">'
        '<span style="color:#98a0ab;font-weight:700">三窗触发器(A档)</span>'
        + chip(hit["ice"], "❄冰点进攻窗", "#4fb3aa") + chip(hit["hot"], "☢过热禁追窗", "#d64541")
        + chip(hit["wash"], "♨洗出反弹窗", "#d9a441")
        + f'<span style="color:#6b7683">温度 {tstr} · 1进2率 '
        + (("%.1f%%" % (j12[-1] * 100)) if j12 and j12[-1] is not None else "null")
        + ' · 昨停溢价 ' + (("%+.2f%%" % prem[-1]) if prem and prem[-1] is not None else "null") + "</span></div>")
    p2 = os.path.join(L, f"先行指标灯_{d}.html")
    open(p2, "w", encoding="utf-8").write(strip)
    print("[卡] %s\n[灯] %s" % (p1, p2))

def main():
    ths = load_ths()
    if not ths:
        print("[失败] THS池不存在")
        return
    t = load_out()
    if len(sys.argv) > 1 and sys.argv[1] == "--backfill":
        days = sorted(ths.keys())
        for d in days:
            run_day(d, ths, t, with_spot=False)
        settle_premium_backfill(t)
        save_out(t)
        print("[回填完成] %d 日; 最近10日:" % len(days))
        for d in days[-10:]:
            summary_line(d, t[d])
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--card":
        card(sys.argv[2], t); return
    d = sys.argv[1] if len(sys.argv) > 1 else sorted(ths.keys())[-1]
    row = run_day(d, ths, t, with_spot=True)
    card(d, t)
    settle_premium_backfill(t)
    tr = triggers(d, t)
    t[d]["触发器"] = tr
    save_out(t)
    summary_line(d, t[d])
    for m in tr:
        print("  " + m)
    if not tr:
        print("  触发器: 三窗均未触发(冰点<25/过热≥85/溢价连负3日)")

if __name__ == "__main__":
    main()
