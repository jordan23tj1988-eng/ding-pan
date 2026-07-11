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
     f'<div class="hint">v5排序=命中规则数→抓龙率(P(执2≥+8%)),质量分仅负筛(剔当日最低四分位);库{out["库样本"]}样本(一年窗口)/活跃因子{len(out.get("活跃因子") or [])};'
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
    if len(rows)>=8:
        import statistics
        q25=sorted(r["质量分"] for r in rows)[len(rows)//4]
        pool=[r for r in rows if r["质量分"]>q25] or rows
    else: pool=rows
    top5=pool[:5]
    out=dict(日=d,库窗口=lib["窗口"],库样本=lib["样本"],口径=lib["口径"],
        活跃因子=lib.get("活跃因子"),荐票源="12_涨停复盘(v5规则榜+抓龙率)",打标数=len(rows),明细=rows,top5=top5)
    json.dump(out,open(os.path.join(L,f"涨停质量荐票_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    卡html(d,out,top5)
    print(f"{d} v5打标{len(rows)}只(活跃因子{len(lib.get('活跃因子') or [])}) | 质量Top5:")
    for i,x in enumerate(top5,1):
        print(f"  {i} {x['名称']} {x['代码']} 抓龙率{x.get('抓龙率')}% 分{x['质量分']} 命中{x['命中数']}条 · {x['大方向']}")
        print(f"    规则: {'; '.join(x.get('命中规则') or ['无'])} | 主导: {x['主导因子']}")
if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime("%Y%m%d"))
