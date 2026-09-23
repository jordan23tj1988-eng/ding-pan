# -*- coding: utf-8 -*-
"""龙虎榜质量荐票.py {d} —— 当日全部上榜股多因子打标,质量Top5作席位路荐票交总agent(照搬涨停模式)。
产出: _学习/龙虎榜质量荐票_{d}.json(分数唯一源) + 龙虎榜质量荐票卡_{d}.html(排版铁律fixed+nowrap)。
★质量分=环境仪表盘非买入指令;执行口径T+1开买;明日结算自动注入lhb台账日块对账。"""
import os,sys,json,glob,datetime,html as H
import 龙虎榜质量训练 as Q
BASE=os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir(os.path.join(BASE,'_学习')):
    g=glob.glob('/sessions/*/mnt/股票数据/市场数据')
    if g: BASE=g[0]
L=os.path.join(BASE,"_学习")
def 卡html(d,out,top5):
    rows=[]
    for i,x in enumerate(top5,1):
        who=(x.get("游资名") or "—")
        wr=x.get("游资胜率")
        who2=f'{who}<br><span class="mut">{("滚动胜率"+str(wr)+"%") if wr is not None else x["性质"]}</span>'
        rows.append(
            f'<tr><td>{i}</td>'
            f'<td style="white-space:nowrap"><b>{H.escape(x["名称"])}</b><br><span class="mut">{x["代码"]}</span></td>'
            f'<td style="white-space:nowrap"><b>{x["质量分"]}</b></td>'
            f'<td style="white-space:nowrap">执1 {x["预测执1胜率"]}%/{x["预测执1均涨"]:+.2f}%<br>'
            f'<span class="mut">执2 {x["预测执2胜率"]}%/{x["预测执2均涨"]:+.2f}%</span></td>'
            f'<td style="word-break:break-word">{H.escape(x.get("主导因子") or "")}</td>'
            f'<td style="white-space:nowrap">{who2}</td></tr>')
    card=(f'<div class="card"><table style="table-layout:fixed;width:100%">'
     f'<colgroup><col style="width:26px"><col style="width:112px"><col style="width:42px">'
     f'<col style="width:158px"><col><col style="width:120px"></colgroup>'
     f'<tr><th>#</th><th>标的</th><th>分</th><th>预测执行(T+1开买→收)</th><th>主导因子(加分|拖累)</th><th>主导资金</th></tr>'
     +"".join(rows)+'</table></div>'
     f'<div class="hint">质量分=有效因子加权评分卡(执行口径),库{out["库样本"]}样本/活跃因子{len(out.get("活跃因子") or [])};'
     f'桶均值非个股预言。已知铁律:榜单信号越猛跟随越亏,edge在"谁买"(游资滚动胜率因子)。明日T+1结算自动注入lhb台账日块对账。</div>')
    p=os.path.join(L,f"龙虎榜质量荐票卡_{d}.html")
    open(p,"w",encoding="utf-8").write(card)
    return p
def main(d):
    lib=Q._lib()
    rows=Q.打标当日(d)
    if not rows:
        print(d,"当日无上榜(或原料缺)"); return
    rows.sort(key=lambda x:(-x["质量分"],-(x.get("游资胜率") or 0),-(x.get("净占") or 0)))
    top5=rows[:5]
    out=dict(日=d,库窗口=lib["窗口"],库样本=lib["样本"],口径=lib["口径"],活跃因子=lib.get("活跃因子"),
        荐票源="09_席位命门(龙虎榜质量分)",打标数=len(rows),明细=rows,top5=top5)
    json.dump(out,open(os.path.join(L,f"龙虎榜质量荐票_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    卡html(d,out,top5)
    print(f"{d} 龙虎榜打标{len(rows)}只 | 质量Top5:")
    for i,x in enumerate(top5,1):
        print(f"  {i} {x['名称']} {x['代码']} 分{x['质量分']} 执1 {x['预测执1胜率']}%/{x['预测执1均涨']}% · {x.get('游资名') or x['性质']}")
if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime("%Y%m%d"))
