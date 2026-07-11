# -*- coding: utf-8 -*-
"""资金温度.py [{d}] —— 龙虎榜资金温度日度统计+图形(2026-07-10用户拍板)。
逐日统计买侧明细(剔转债/B股):机构/量化/知名游资/北向/普通营业部 的席次与买入金额(亿);
温度=当日总买入额在【截至当日】近60交易日的分位(当日视角,零后视镜,历史逐日重放);
产出: _学习/_资金温度.json(全序列) + SVG图(近20日滚动窗口,日期再多不影响展示) 注入lhb页<!--FUNDTEMP-->标记段。
本脚本只管FUNDTEMP段(链路分工铁律)。"""
import os,sys,json,glob
import pandas as pd
from 资金结构因子 import style
from 席位动向库 import clean
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
DIR=os.path.join(L,"_席位动向")
STYLES=["机构","量化","知名游资","北向","营业部"]
def build_series():
    """游资口径升级(2026-07-10用户抓出"游资1席假象"):知名游资名单挂一漏万,
    改【活跃游资】=截至前一日累计上榜≥8次的营业部席位(数据驱动,滚动判定零后视镜)∪知名名单。"""
    from collections import Counter
    seen=Counter()
    rows=[]
    for f in sorted(glob.glob(os.path.join(DIR,"20*.csv"))):
        d=os.path.basename(f)[:-4]
        df=pd.read_csv(f,dtype={"代码":str}); df["代码"]=df["代码"].str.zfill(6)
        df=clean(df)
        df["风格"]=df["席位"].map(style)
        active=df["席位"].map(lambda x:seen[x]>=8)   # 截至昨日累计≥8次=活跃(不含今日,零后视镜)
        df.loc[(df["风格"]=="营业部")&active,"风格"]="知名游资"
        r=dict(日=d)
        for st in STYLES:
            g=df[df["风格"]==st]
            r[st+"席次"]=int(len(g)); r[st+"金额亿"]=round(g["买入金额"].sum()/1e8,1)
        r["总金额亿"]=round(df["买入金额"].sum()/1e8,1)
        rows.append(r)
        for x in df["席位"]: seen[x]+=1
    s=pd.DataFrame(rows).sort_values("日").reset_index(drop=True)
    # 温度分位:当日视角(用截至当日的最近60日窗口含当日)——历史逐日重放,零后视镜
    temps=[]
    for i in range(len(s)):
        w=s["总金额亿"].iloc[max(0,i-59):i+1]
        temps.append(round((w<=s["总金额亿"].iloc[i]).mean()*100))
    s["温度分位"]=temps
    return s
def svg_chart(s,n=20):
    t=s.tail(n).reset_index(drop=True); m=len(t)
    W,H=940,300; padL,padB,padT=46,34,18
    gw=(W-padL-10)/m
    # 上半:席次堆叠柱(机构/量化/游资);下半略——金额画折线(总金额)叠加右轴
    maxN=max(1,(t["机构席次"]+t["量化席次"]+t["知名游资席次"]).max())
    maxA=max(1.0,t["总金额亿"].max())
    ch=H-padB-padT
    parts=[f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;font-family:inherit">']
    # y轴刻度(席次)
    for k in range(5):
        y=padT+ch-ch*k/4; v=int(maxN*k/4)
        parts.append(f'<line x1="{padL}" y1="{y:.0f}" x2="{W-10}" y2="{y:.0f}" stroke="#e8e2d4" stroke-width="1"/>')
        parts.append(f'<text x="{padL-6}" y="{y+4:.0f}" text-anchor="end" font-size="10" fill="#8a8272">{v}</text>')
    C={"机构":"#2e6f5e","量化":"#7c5cbf","知名游资":"#c0392b"}
    for i,r in t.iterrows():
        x=padL+gw*i+gw*0.18; bw=gw*0.55; y=padT+ch
        for st in ["机构","量化","知名游资"]:
            h=ch*r[st+"席次"]/maxN
            y-=h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{C[st]}"/>')
        lab=r["日"][4:6]+"/"+r["日"][6:]
        if m<=22 or i%2==0:
            parts.append(f'<text x="{x+bw/2:.0f}" y="{H-padB+13}" text-anchor="middle" font-size="9" fill="#8a8272">{lab}</text>')
        # 温度点色
        col="#c0392b" if r["温度分位"]>=67 else "#c8a24a" if r["温度分位"]>=34 else "#7f9db9"
        parts.append(f'<circle cx="{x+bw/2:.0f}" cy="{H-padB+22}" r="3" fill="{col}"/>')
    # 金额折线(右轴)
    pts=[]
    for i,r in t.iterrows():
        x=padL+gw*i+gw*0.18+gw*0.55/2
        y=padT+ch-ch*r["总金额亿"]/maxA
        pts.append(f"{x:.1f},{y:.1f}")
    parts.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#1f2430" stroke-width="2" stroke-dasharray="4 3"/>')
    for k in range(3):
        y=padT+ch-ch*k/2; v=round(maxA*k/2)
        parts.append(f'<text x="{W-8}" y="{y+4:.0f}" text-anchor="end" font-size="10" fill="#1f2430">{v}亿</text>')
    parts.append('</svg>')
    return "".join(parts)
def main(d=None):
    s=build_series()
    json.dump(s.to_dict("records"),open(os.path.join(L,"_资金温度.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    last=s.iloc[-1]
    tw="热" if last["温度分位"]>=67 else "温" if last["温度分位"]>=34 else "冷"
    # 最近5日数值表
    t5=s.tail(5).iloc[::-1]
    rows=''.join(f'<tr><td style="white-space:nowrap">{r["日"][4:6]}-{r["日"][6:]}</td>'
      f'<td>{r["机构席次"]}<span class="mut">/{r["机构金额亿"]}亿</span></td>'
      f'<td>{r["量化席次"]}<span class="mut">/{r["量化金额亿"]}亿</span></td>'
      f'<td>{r["知名游资席次"]}<span class="mut">/{r["知名游资金额亿"]}亿</span></td>'
      f'<td>{r["北向席次"]}<span class="mut">/{r["北向金额亿"]}亿</span></td>'
      f'<td><b>{r["总金额亿"]}亿</b></td><td><b>{r["温度分位"]}</b></td></tr>' for _,r in t5.iterrows())
    sec=(f'<h2>二 资金温度 · 日度统计(买侧席位明细)</h2>'
     f'<div class="hint">柱=当日出手席次(<span style="color:#2e6f5e">■机构</span> <span style="color:#7c5cbf">■量化</span> <span style="color:#c0392b">■游资=活跃(截至昨日累计上榜≥8次,数据驱动)∪知名名单</span>),'
     f'虚线=买侧总金额(右轴);底部圆点=温度(红热≥67/黄温/蓝冷<34,当日总额在截至当日近60日的分位,零后视镜)。'
     f'滚动窗口只显示最近20个交易日,日期增加不影响展示。★库实证(清洗后,区分度15.9pp,倒U型):<b>温和放量日(34-66分位)跟买61.6%最好,过热(≥67)仅45.7%,冷48.7%居中</b>=有钱进但不拥挤才有肉。<b>今日温度:{last["温度分位"]}分位({tw})</b></div>'
     f'<div class="card">{svg_chart(s)}</div>'
     f'<div class="card"><table style="table-layout:fixed;width:100%"><colgroup><col style="width:52px"><col><col><col><col><col style="width:70px"><col style="width:46px"></colgroup>'
     f'<tr><th>日</th><th>机构</th><th>量化</th><th>游资(活跃+知名)</th><th>北向</th><th>总额</th><th>温度</th></tr>{rows}</table></div>')
    # 注入judgment lhb页 FUNDTEMP标记段(幂等;无标记则报错提示先加锚)
    js=sorted(glob.glob(os.path.join(L,"judgment_*.json"))); jp=js[-1]
    J=json.load(open(jp,encoding="utf-8")); b=J["bodies"].get("lhb","")
    if '<!--FUNDTEMP-->' in b:
        b=b[:b.find('<!--FUNDTEMP-->')+len('<!--FUNDTEMP-->')]+sec+b[b.find('<!--/FUNDTEMP-->'):]
        J["bodies"]["lhb"]=b; json.dump(J,open(jp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        inj="已注入"+os.path.basename(jp)
    else: inj="⚠lhb页无FUNDTEMP锚,未注入"
    print(f'资金温度: {len(s)}日 今日{last["温度分位"]}分位({tw}) 机构{last["机构席次"]}席/{last["机构金额亿"]}亿 量化{last["量化席次"]}席 游资{last["知名游资席次"]}席 | {inj}')
if __name__=="__main__": main()
