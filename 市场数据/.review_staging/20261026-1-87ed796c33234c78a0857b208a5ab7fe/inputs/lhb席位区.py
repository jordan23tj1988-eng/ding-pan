# -*- coding: utf-8 -*-
"""lhb席位区.py {d} —— v2只产【固定段·全市场席位分档库】html→_学习/席位分档库.html
(2026-07-10链路统一:荐票卡/动向表已移入龙虎榜台账日块=唯一每日管道;本脚本只管滚动库固定段)"""
import os,sys,json,html as H
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
def main(d):
    lib=json.load(open(os.path.join(L,'_席位分档.json'),encoding='utf-8'))
    seats=lib['席位']; sa={s:v for s,v in seats.items() if v['档'] in 'SA'}
    mv=pd.read_csv(os.path.join(L,'_席位动向',f'{d}.csv'),dtype={'代码':str}); mv['代码']=mv['代码'].str.zfill(6)
    mv=mv[(mv['净额']>0)&(mv['买入金额']>=1e7)].drop_duplicates(subset=['代码','席位'])
    hits=mv[mv['席位'].isin(sa)].copy()
    hits['档']=hits['席位'].map(lambda s:sa[s]['档'])
    hits['序']=hits['档'].map({'S':0,'A':1})
    hits=hits.sort_values(['序','净额'],ascending=[True,False])
    sa_sorted=sorted(sa.items(),key=lambda x:({'S':0,'A':1}[x[1]['档']],-x[1]['执1胜率'],-x[1]['样本']))
    librows=''.join(f'<tr><td style="white-space:nowrap"><b class="{"s-ok" if v["档"]=="S" else "s-mid"}">[{v["档"]}]</b> {H.escape(s[:24])}…</td>'
      f'<td style="white-space:nowrap">{v["执1胜率"]}%/{v["执1均涨"]}%</td><td style="white-space:nowrap">{v["执2胜率"]}%/{v["执2均涨"]}%</td>'
      f'<td>{v["样本"]}</td><td>{v["通道"]}</td>'
      f'<td style="word-break:break-word"><span class="mut">{"、".join(x["名"]+("%+.1f"%x["执1"]) for x in v["近5笔"][-3:])}</span></td></tr>' for s,v in sa_sorted)
    cnt=lib['档分布']
    # v2.1(2026-07-11用户): 窗口末日<事实表最新日=有已入库待结算的动向,折叠条明示,防"数据断了"误读(零后视镜:当日笔T+1才结算入窗)
    md=max((f[:8] for f in os.listdir(os.path.join(L,'_席位动向')) if f[:8].isdigit() and f.endswith('.csv')),default='')
    wend=str(lib["窗口"]).split('~')[-1]
    pend=(f' <span class="chip cold">{md[4:6]}-{md[6:8]}动向已入库·待T+1结算入窗</span>' if md and md>wend else '')
    libblk=(f'<details class="chain"><summary><b>全市场席位分档库(自我净化)</b> <span class="chip">S{cnt.get("S",0)}/A{cnt.get("A",0)}/B{cnt.get("B",0)}/C{cnt.get("C",0)}/预备{cnt.get("P",0)}</span> 窗口{lib["窗口"]} {lib["笔数"]}笔{pend}</summary><div class="inner">'
     f'<div class="hint">{H.escape(lib["口径"])}。S=n≥5且执1胜率≥60%且均涨>1%;A=胜率≥55%或(≥50%且均涨>1.5%);B=45-55%;C=<45%;每晚重算,掉档自动降级。</div>'
     f'<div class="card"><table style="table-layout:fixed;width:100%"><colgroup><col><col style="width:92px"><col style="width:92px"><col style="width:36px"><col style="width:52px"><col style="width:170px"></colgroup>'
     f'<tr><th>席位</th><th>执1胜率/均涨</th><th>执2</th><th>n</th><th>通道</th><th>近3笔</th></tr>{librows}</table></div></div></details>')
    open(os.path.join(L,'席位分档库.html'),'w',encoding='utf-8').write(libblk)
    print(f'席位分档库固定段已产出(S{cnt.get("S",0)}/A{cnt.get("A",0)})')
if __name__=="__main__": main(sys.argv[1] if len(sys.argv)>1 else "")
