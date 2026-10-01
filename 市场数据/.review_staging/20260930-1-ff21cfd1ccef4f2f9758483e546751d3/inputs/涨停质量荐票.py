# -*- coding: utf-8 -*-
"""涨停质量荐票.py {d} v6 —— 16因子(v4含封单额+市场温度)质量分打标全部涨停,Top5作第5路荐票交总agent。
v4(2026-07-10晚): 因子14→16(+封单绝对额+市场温度,连板桶细化4档)。v3: 因子2→14(涨停质量训练.py打标当日统一算,训练/荐票同一代码路径保证口径一致);
质量分=有效因子加权评分卡(执行口径);每只带主导因子拆解(哪几个因子加分/拖累)。
★零后视镜:库不含当日前向;当日K线因子只用≤当日数据。★全量打标含待归位股。"""
import os,sys,json,datetime
import 涨停质量训练 as Q
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")

def 卡html(d,out,top5):
    """Top5荐票卡html片段→_学习/涨停质量荐票卡_{d}.html(傍晚场嵌judgment;台账日块也嵌=当日完整档案)。
    排版铁律:table-layout:fixed+列宽显式;标的/分/预测列nowrap防挤成竖条(v2.4排版教训)。"""
    import html as H
    disp=d[4:6]+"-"+d[6:8]
    rows=[]
    for i,x in enumerate(top5,1):
        hits=x.get("命中规则") or []
        lead=H.escape(x.get("主导因子") or "")
        leadh=f'<span class="mut" style="font-size:11px">主导: {lead}</span>' if lead else ''
        if hits:   # v6.1: 规则命中主行+评分卡主导因子副行;无命中退而显示主导因子(用户2026-07-11要求,不留空)
            hh=H.escape("; ".join(hits))+('<br>'+leadh if leadh else '')
        else:
            hh='<span class="mut">规则未命中</span>'+('<br>'+leadh if leadh else '')
        rows.append(
            f'<tr><td>{i}</td>'
            f'<td style="white-space:nowrap"><b>{H.escape(x["名称"])}</b><br><span class="mut">{x["代码"]}</span></td>'
            f'<td style="white-space:nowrap"><b>{x.get("抓龙率") if x.get("抓龙率") is not None else "—"}%</b><br><span class="mut">分{x["质量分"]}</span></td>'
            f'<td style="word-break:break-word">{hh}</td>'
            f'<td style="white-space:nowrap">执1 {x["预测执1胜率"]}%/{x["预测执1均涨"]:+.2f}%<br>'
            f'<span class="mut">执2 {x["预测执2胜率"]}%/{x["预测执2均涨"]:+.2f}%</span></td>'
            f'<td>{H.escape(x.get("大方向") or "待归位")}</td></tr>')
    env=next((x.get('环境提示') for x in top5 if x.get('环境提示')),None)   # v6环境规则(温度两端,训练脚本产)
    envh=('<div class="hint" style="color:#c62828">★环境规则v6: 市场温度过热≥85(历史日均执1约-1.8%),本日第5路荐票<b>全场回避·仅观察不追买</b></div>' if env=='过热回避'
          else '<div class="hint">★环境规则v6: 市场温度冰点&lt;25(历史日均执1约+0.3%),全场加分观察</div>' if env=='冰点加分' else '')
    card=(envh+f'<div class="card"><table style="table-layout:fixed;width:100%">'
     f'<colgroup><col style="width:26px"><col style="width:106px"><col style="width:62px">'
     f'<col><col style="width:150px"><col style="width:96px"></colgroup>'
     f'<tr><th>#</th><th>标的</th><th>抓龙率</th><th>命中规则(规则榜) / 主导因子(评分卡)</th><th>预测执行(T+1开买→收)</th><th>题材</th></tr>'
     +"".join(rows)+'</table></div>'
     f'<div class="hint">v5.1排序=命中规则数→抓龙率(P(执2≥+8%)),质量分仅负筛(只作用于0命中票,规则命中票全保);库{out["库样本"]}样本(一年窗口)/活跃因子{len(out.get("活跃因子") or [])};'
     f'规则榜多为扛出型(执1弱执2强=开盘买进当天套、次日兑现),桶均值非个股预言。明日T+1结算自动注入本日台账日块对账。</div>')
    p=os.path.join(L,f"涨停质量荐票卡_{d}.html")
    open(p,"w",encoding="utf-8").write(card)
    return p
def main(d):
    lib=Q._lib()
    meta={}
    cp=os.path.join(L,f"涨停对链条_{d}.json")
    if os.path.isfile(cp):
        zt=json.load(open(cp,encoding="utf-8"))
        for t in zt["题材线"]:
            for s in t["环节"]:
                for g in s["个股"]:
                    meta[g["代码"]]=dict(大方向=t["大方向"],环节=s["环节"],催化=g.get("催化"),来源档=g.get("来源档"))
        for g in zt.get("待归位_行业兜底") or []:
            meta[g["代码"]]=dict(大方向="待归位",环节="行业:"+str(g.get("行业","")),催化=g.get("催化"),来源档=g.get("来源档"))
    rows=Q.打标当日(d)
    for r in rows:
        r.update(meta.get(r["代码"],dict(大方向="待归位",环节=None,催化=None,来源档=None)))
    # v5(2026-07-10用户拍板"分数没区分度"): 质量分只做负筛(剔当日最低四分位),排序=命中规则数→预测抓龙率→质量分
    rows.sort(key=lambda x:(-x["命中数"],-(x["抓龙率"] or 0),-x["质量分"]))
    # v5.1(2026-08-13用户拍板"方案A"): 负筛只作用于0命中票, 规则命中票(规则榜硬证据)全保。
    # 修复事故: v5 负筛用质量分(第三排序键)否决命中规则数(第一排序键)——8/12/8/13 蓝盾光电(命中6条/抓龙22.8%·20.8%)
    # 连续两晚被 P25 误杀, Top5 沦为全0命中次优票。q25 口径同步改为只在0命中票内计算(负筛真正作用的群体)。
    if len(rows)>=8:
        z0=[r for r in rows if r["命中数"]<=0]
        if z0 and len(z0)>=4:
            q25=sorted(r["质量分"] for r in z0)[len(z0)//4]
            pool=[r for r in rows if r["命中数"]>0 or r["质量分"]>q25] or rows
        else:
            pool=rows
    else: pool=rows
    top5=pool[:5]
    out=dict(日=d,库窗口=lib["窗口"],库样本=lib["样本"],口径=lib["口径"],
        活跃因子=lib.get("活跃因子"),荐票源="12_涨停复盘(v5.1规则榜+抓龙率)",打标数=len(rows),明细=rows,top5=top5)
    json.dump(out,open(os.path.join(L,f"涨停质量荐票_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    卡html(d,out,top5)
    print(f"{d} v5打标{len(rows)}只(活跃因子{len(lib.get('活跃因子') or [])}) | 质量Top5:")
    for i,x in enumerate(top5,1):
        print(f"  {i} {x['名称']} {x['代码']} 抓龙率{x.get('抓龙率')}% 分{x['质量分']} 命中{x['命中数']}条 · {x['大方向']}")
        print(f"    规则: {'; '.join(x.get('命中规则') or ['无'])} | 主导: {x['主导因子']}")
def 池外候选卡(d):
    """池外候选卡_{d}.html —— 量价因子库A2全市场扫描候选(2026-08-13上线)
    读 D:/股票数据/量价因子库/data/daily/candidates_{d}.json; 不存在/空→不生成(向后兼容零影响)。"""
    import html as H
    cp = os.path.join(r"D:/股票数据/量价因子库/data/daily", f"candidates_{d}.json")
    if not os.path.isfile(cp):
        print(f"  池外候选: candidates_{d}.json 未就绪(A2扫描未跑), 本日无池外卡")
        return None
    cand = json.load(open(cp, encoding="utf-8"))
    cs = cand.get("候选") or []
    if not cs:
        print(f"  池外候选: 本日候选0, 不生成卡")
        return None
    disp = d[4:6] + "-" + d[6:8]
    def _b_pos(p):
        return "低位" if p < 0.5 else ("中位" if p <= 1.0 else "高位")
    # 排序: 执2胜率降序(预测值缺失排尾) → 执2均值降序
    cs = sorted(cs, key=lambda x: (-(x.get("预测执2胜率") is not None),
                                   -(x.get("预测执2胜率") or -1),
                                   -(x.get("预测执2均涨") or -99)))
    rows = []
    for i, x in enumerate(cs[:10], 1):
        nm = H.escape(x.get("名称") or x["code"])
        pool = x["池"]
        feat = [f"大阳{x.get('大阳线')}", f"量能{x.get('量能比')}"]
        pos, v5tag = x.get("位置"), x.get("量比档")
        if pos is not None and v5tag:
            feat.append(f"桶:{_b_pos(pos)}×{v5tag}")
        elif x.get("位置") is not None:
            feat.append(f"位{round(float(x['位置']) * 100)}%")
        if x.get("MA20档"):
            feat.append(x["MA20档"])
        if x.get("连板"):
            feat.append(f"{x['连板']}板")
        exec_ = ""
        if x.get("预测执1均涨") is not None:
            exec_ = (f'<span class="mut">执1 {x["预测执1胜率"]}%/{x["预测执1均涨"]:+.2f}%</span><br>'
                     f'<b>执2 {x["预测执2胜率"]}%/{x["预测执2均涨"]:+.2f}%</b>')
        else:
            exec_ = '<span class="mut">无预测表</span>'
        rows.append(
            f'<tr><td>{i}</td>'
            f'<td style="white-space:nowrap"><b>{nm}</b><br><span class="mut">{x["code"]}</span></td>'
            f'<td style="white-space:nowrap">{pool}</td>'
            f'<td style="word-break:break-word">{"; ".join(feat)}</td>'
            f'<td style="white-space:nowrap">{exec_}</td>'
            f'<td style="word-break:break-word">{H.escape(x.get("买入条件") or "—")}</td></tr>')
    envh = H.escape(cand.get("环境提示") or "")
    card = ('<div class="card"><table style="table-layout:fixed;width:100%">'
            '<colgroup><col style="width:26px"><col style="width:106px"><col style="width:60px">'
            '<col><col style="width:150px"><col></colgroup>'
            '<tr><th>#</th><th>标的</th><th>池</th><th>特征(量价甜点)</th><th>预测执行(T+1开买)</th><th>次日买入/放弃条件</th></tr>'
            + "".join(rows) + '</table></div>')
    hint = ('<div class="hint">池外候选=量价因子库全市场扫描(SW-1甜点:前10日≥3大阳+缩量&lt;0.8×20日均; CW断板修复池), '
            f'26年实测样本/毛收益未扣费; 环境={cand.get("环境")}(涨停{cand.get("当日涨停家数")}家); '
            '买入=次日低开或高开&gt;5%,放弃=平开中段/高潮环境; 非荐票,是与涨停池Top5并列的观察池。</div>')
    # 昨日候选今日结算段(读量价因子库 settle json; 缺文件跳过)
    import datetime as _dt
    _dp = (_dt.date(int(d[:4]), int(d[4:6]), int(d[6:8])) - _dt.timedelta(days=1)).strftime("%Y%m%d")
    _sp = os.path.join(r"D:/股票数据/量价因子库/data/settle", f"settle_{_dp}.json")
    settle_h = ""
    if os.path.isfile(_sp):
        st = json.load(open(_sp, encoding="utf-8"))
        e1 = [s["执1"] for s in st.get("明细") or [] if s.get("执1") is not None]
        e2 = [s["执2"] for s in st.get("明细") or [] if s.get("执2") is not None]
        mean1 = (sum(e1) / len(e1)) if e1 else None
        mean2 = (sum(e2) / len(e2)) if e2 else None
        settle_h = (f'<div class="hint">昨日候选结算({st.get("候选日")}→{st.get("结算日")}): '
                    f'候选{st.get("候选数")} → 可买{st.get("可买数")}/放弃{st.get("放弃数")}/无数据{st.get("无数据数")}'
                    + (f' | 执1均值 {mean1:+.2f}%(n={len(e1)})' if mean1 is not None else '')
                    + (f' | 执2均值 {mean2:+.2f}%(n={len(e2)})' if mean2 is not None else '')
                    + '</div>')
    body = (envh and f'<div class="hint" style="color:#c62828">{envh}</div>') + card + hint + settle_h
    p = os.path.join(L, f"池外候选卡_{d}.html")
    open(p, "w", encoding="utf-8").write(body)
    print(f"  池外候选: {len(cs)} 只(示前10) → 池外候选卡_{d}.html")
    return p

if __name__=="__main__":
    d = sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime("%Y%m%d")
    main(d)
    池外候选卡(d)
