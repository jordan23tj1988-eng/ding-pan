# -*- coding: utf-8 -*-
"""竞价池初读.py {昨日d} —— 早盘固化步骤:对昨日竞价选股池(zt_pool首封≤9:31)做今晨T+1竞价初读。
零编造:昨日池由 {昨日d}/zt_pool.csv 首封≤09:31 确定性重建;今晨行情走sina实时(hq.sinajs.cn)。
规则初读判定(A档):盘中封板=✓兑现/高开≥4未封=◐/平开=未兑现/低开≤-2=✗打脸/现涨≤-8=✗✗近跌停。
产出 _学习/竞价池初读_{昨日d}.json,并幂等注入最新judgment的auction页「二·今晨初读」段。完整封板收益终结算由18:00傍晚场做。"""
import os,sys,re,json,glob,datetime,urllib.request
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
def sina(codes):
    out={}
    if not codes: return out
    lst=",".join(("sh" if c[0] in "69" else "sz")+c for c in codes)
    req=urllib.request.Request("https://hq.sinajs.cn/list="+lst,headers={"Referer":"https://finance.sina.com.cn"})
    for l in urllib.request.urlopen(req,timeout=10).read().decode("gbk").strip().split("\n"):
        mm=re.search(r'str_(?:sh|sz)(\d{6})="([^"]*)"',l)
        if not mm: continue
        p=mm.group(2).split(",")
        if len(p)>10 and float(p[2])>0:
            out[mm.group(1)]=dict(今开=float(p[1]),昨收=float(p[2]),现价=float(p[3]),高=float(p[4]))
    return out
def lim(c): return 19.9 if c[:2] in("30","68") else 9.9
def build_pool(dprev):
    df=pd.read_csv(os.path.join(BASE,dprev,"zt_pool.csv"),dtype={"代码":str})
    df["代码"]=df["代码"].astype(str).str.zfill(6)
    def hm(x): s=str(x).split(".")[0].zfill(6); return s[:2]+":"+s[2:4]
    pool=[]
    for _,r in df.iterrows():
        fb=hm(r["首次封板时间"])
        if fb>"09:31": continue
        lb=int(pd.to_numeric(r.get("连板数",1),errors="coerce") or 1)
        mv=pd.to_numeric(r.get("流通市值"),errors="coerce"); fj=pd.to_numeric(r.get("封板资金"),errors="coerce")
        fdb=round(float(fj)/float(mv)*100,2) if (mv and mv>0 and fj==fj) else None
        sig=("一字" if fb<="09:25" else "秒板")+(f"·{lb}板" if lb>1 else "·首板")
        pool.append(dict(代码=r["代码"],名称=str(r["名称"]),首封=fb,连板=lb,信号=sig,封单比=fdb,行业=str(r.get("所属行业",""))))
    return sorted(pool,key=lambda x:x["首封"])
def verdict(c,d):
    if not d: return ("dB","—未取到","")
    gk,cur=d["高开"],d["现涨"]
    if d["封板"]: return ("dA","✓封板(T+1兑现)","盘中封板,竞价信号兑现")
    if cur<=-8: return ("dC","✗✗近跌停","高位崩,最差")
    if gk<=-2: return ("dC","✗低开走弱","低开打脸,竞价信号证伪")
    if gk>=4: return ("dB","◐高开未封","竞价冲高但未封,盯回落")
    return ("dB","平开未兑现","无方向,竞价信号未兑现")
def main(dprev):
    pool=build_pool(dprev)
    q=sina([p["代码"] for p in pool])
    seal=0; rows=""
    for p in pool:
        s=q.get(p["代码"]); d=None
        if s:
            d=dict(高开=round((s["今开"]/s["昨收"]-1)*100,2),现涨=round((s["现价"]/s["昨收"]-1)*100,2),
                   盘中高=round((s["高"]/s["昨收"]-1)*100,2),封板=(s["现价"]/s["昨收"]-1)*100>=lim(p["代码"])-0.1)
            if d["封板"]: seal+=1
        p["今晨"]=d; cl,tag,why=verdict(p["代码"],d)
        cell=(f'高开{d["高开"]:+.1f}% · 现{d["现涨"]:+.1f}% · {"封板" if d["封板"] else "未封"}') if d else "—"
        fdb=f'{p["封单比"]}%' if p["封单比"] is not None else "—"
        rows+=f'<tr><td><b>{p["名称"]}</b><br><span class="mut">{p["代码"]}</span></td><td>{p["信号"]} · 封{fdb}</td><td>{cell}</td><td class="{cl}">{tag}<br><span class="mut" style="font-weight:400">{why}</span></td></tr>'
    n=len(pool); rate=round(seal/n*100) if n else 0
    out=dict(池日=dprev,初读日=datetime.date.today().strftime("%Y%m%d"),初读时间=datetime.datetime.now().strftime("%H:%M"),
             池家数=n,盘中封板=seal,封板率=rate,明细=pool)
    json.dump(out,open(os.path.join(L,f"竞价池初读_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    disp=dprev[4:6]+"-"+dprev[6:8]
    block=(f'<h2 class="hot">★今晨初读 · {disp}池 T+1竞价初读({datetime.datetime.now().strftime("%H:%M")}实时)</h2>'
     f'<div class="hint">昨日({disp})竞价池={disp} zt_pool首封≤9:31(确定性重建),用今晨集合竞价+早盘实时做T+1初读。★成交额盘中为累计非竞价额,故只用高开/现价定强弱。完整封板/收益终结算今晚18:00补。</div>'
     f'<div class="card"><table><tr><th>标的</th><th>{disp}竞价信号</th><th>今晨实况</th><th>初读判定</th></tr>{rows}</table>'
     f'<p class="base" style="margin-top:10px"><b>★初读封板率 {seal}/{n}≈{rate}%</b>(对照一字42.1%/秒板25.9%历史)。业绩硬/高度真的扛住,缺业绩缺高度的扩散票T+1走弱——竞价强身位须与产业逻辑+题材身位共振。agent可在此基础上补深评。</p></div>')
    # 幂等注入最新judgment auction
    js=sorted(glob.glob(os.path.join(L,"judgment_*.json"))); jp=js[-1]
    J=json.load(open(jp,encoding="utf-8")); a=J["bodies"]["auction"]
    a=re.sub(r'<h2 class="hot">(?:二·今晨初读、|★今晨初读 · ).*?(?=<h2)','',a,flags=re.S)  # 删旧初读段(兼容旧编号版)
    anchor=next((m for m in ['<h2>二 昨日','<h2 class="hot">二 昨日','<h2>三 今日竞价温度','<h2>附·','<h2>二、昨日选股池结算','<h2 class="hot">二、昨日选股池结算','<h2>三、竞价信号','<h2 class="hot">三、竞价信号'] if m in a),None)
    if anchor:
        a=a.replace('<h2>二、昨日选股池结算','<h2>附·历史池结算',1).replace('<h2 class="hot">二、昨日选股池结算','<h2>附·历史池结算',1)
        anchor=next((m for m in ['<h2>二 昨日','<h2 class="hot">二 昨日','<h2>三 今日竞价温度','<h2>附·','<h2>三、竞价信号','<h2 class="hot">三、竞价信号'] if m in a),None)
        i=a.find(anchor); a=a[:i]+block+"\n"+a[i:]
    else: a=a+block
    J["bodies"]["auction"]=a
    json.dump(J,open(jp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"{disp}池初读: {n}只 盘中封板{seal}/{n}={rate}% | 已注入{os.path.basename(jp)} auction")
    for p in pool:
        d=p["今晨"]; print(f'  {p["名称"]}({p["代码"]}) {p["信号"]:8} '+(f'高开{d["高开"]:+.1f}% 现{d["现涨"]:+.1f}% {"封" if d["封板"] else "未"}' if d else "未取到"))
if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else (sorted(glob.glob(os.path.join(BASE,"2026*")))[-1].split(os.sep)[-1]))
