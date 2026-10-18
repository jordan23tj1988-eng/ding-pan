# -*- coding: utf-8 -*-
"""涨停对链条.py [d] —— 每日铁例行:当日全部涨停股逐只做【三层题材归位】。
v2(2026-07-09升级,题材≠行业):
  · 归属三级证据: override(题材归位_{d}.json,agent写:催化/来源档) > 模板匹配(产业链模板.json) > 待归位(行业兜底)。
    跨行业票由催化归到真实题材线(大名城→算力),行业只作兜底提示,不作题材。
  · 每只票带【封板质量四维】(全A档,取自zt_pool): 首封时间/连板数/开板次数(炸板)/封单比(封板资金÷流通市值)。
  · 三层结构: 大方向 → 细分环节 → 个股催化; 每环节给强度画像(早封多家=主线承载 / 晚封高开板率=末端扩散)。
产出: _学习/涨停对链条_{d}.json"""
import os,sys,json,glob,datetime
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")

def hhmm(x):
    s=str(x).split(".")[0].zfill(6); return s[:2]+":"+s[2:4]

def kaiban(x):
    try: return int(float(x))
    except: return 0

def load_override(d):
    p=os.path.join(L,f"题材归位_{d}.json")
    if os.path.isfile(p):
        return json.load(open(p,encoding="utf-8")).get("映射",{})
    return {}

def load_template():
    tpl=json.load(open(os.path.join(BASE,"产业链模板.json"),encoding="utf-8"))
    cm={}
    for bk,cfg in tpl.items():
        if bk=="说明": continue
        for seg,ss in cfg.get("环节",{}).items():
            for pair in ss:
                cm[pair[0]]=(bk,seg)
    return cm

def seg_verdict(rows):
    """环节强度画像(A档量化):早封占比/开板占比/最早封 → 快判"""
    n=len(rows)
    first=min(r["首封"] for r in rows)
    kb=sum(1 for r in rows if r["开板次数"]>0)/n
    zao=sum(1 for r in rows if r["首封"]<="09:40")/n   # 早封占比
    maxlb=max(r["连板"] for r in rows)
    if kb>=0.6:
        v="分歧/末端:过半开板,封板质量差"
    elif zao<=0.34 and first>"10:00":
        v="末端扩散:普遍晚封、情绪外溢,可复制性差"
    elif zao>=0.6 and kb<0.34:
        v="主线承载核心:早封多家、封板扎实"
    else:
        v="中性:环节内甄别身位"
    return dict(家数=n,最高连板=maxlb,最早封板=first,早封占比=round(zao,2),开板占比=round(kb,2),快判=v)

def main(d):
    zp=os.path.join(BASE,d,"zt_pool.csv")
    if os.path.isfile(zp): df=pd.read_csv(zp,dtype={"代码":str})
    else:
        import akshare as ak; df=ak.stock_zt_pool_em(date=d)
    df["代码"]=df["代码"].astype(str).str.zfill(6)
    ov=load_override(d); cm=load_template()
    lines={}      # 大方向 -> {环节 -> [个股...]}
    daiguiwei=[]  # 待归位(行业兜底)
    for _,r in df.iterrows():
        c=r["代码"]; nm=str(r["名称"])
        lb=int(pd.to_numeric(r.get("连板数",1),errors="coerce") or 1)
        fb=hhmm(r.get("首次封板时间","")); kb=kaiban(r.get("炸板次数",0))
        mv=pd.to_numeric(r.get("流通市值"),errors="coerce"); fj=pd.to_numeric(r.get("封板资金"),errors="coerce")
        fdb=round(float(fj)/float(mv)*100,2) if (mv and mv>0 and fj==fj) else None
        base=dict(代码=c,名称=nm,首封=fb,连板=lb,开板次数=kb,封单比=fdb)
        if c in ov:
            o=ov[c]; dfx=o.get("大方向","其它"); seg=o.get("环节","未分环节")
            base.update(催化=o.get("催化"),来源档=o.get("来源档","B"),归属依据="override")
        elif c in cm:
            dfx,seg=cm[c]; base.update(催化=None,来源档="模板",归属依据="模板匹配")
        else:
            base.update(行业=str(r.get("所属行业","")))
            daiguiwei.append(base); continue
        lines.setdefault(dfx,{}).setdefault(seg,[]).append(base)
    # 汇总
    themes=[]
    for dfx,segs in lines.items():
        allrows=[x for s in segs.values() for x in s]
        seg_list=[]
        for seg,rows in segs.items():
            rows=sorted(rows,key=lambda x:x["首封"])
            sv=seg_verdict(rows); sv["环节"]=seg; sv["个股"]=rows
            seg_list.append(sv)
        seg_list=sorted(seg_list,key=lambda s:(s["最早封板"],-s["家数"]))
        core=max(seg_list,key=lambda s:s["家数"])["环节"] if seg_list else None
        n=len(allrows); first=min(r["首封"] for r in allrows)
        kbratio=round(sum(1 for r in allrows if r["开板次数"]>0)/n,2)
        zao=round(sum(1 for r in allrows if r["首封"]<="09:40")/n,2)
        maxlb=max(r["连板"] for r in allrows)
        pic=f"承载环节={core};家数{n}、最高{maxlb}板、早封占比{zao}、开板占比{kbratio}。" + \
            ("早封为主=真主线承载" if zao>=0.5 and kbratio<0.4 else "早封少/开板偏多=首板扩散或分歧,非高标主线")
        themes.append(dict(大方向=dfx,家数=n,最高连板=maxlb,最早封板=first,开板占比=kbratio,
                           承载环节=core,强度画像=pic,环节=seg_list))
    themes=sorted(themes,key=lambda t:(-t["家数"],-t["最高连板"]))
    daiguiwei=sorted(daiguiwei,key=lambda x:x["首封"])
    out={"日期":d,"涨停总数":int(len(df)),"题材线数":len(themes),"题材线":themes,
         "待归位_行业兜底":daiguiwei,
         "口径":"三层题材归位:override(催化/来源档,agent写)>模板匹配>待归位(行业只兜底不作题材)。封板质量四维=A档取自zt_pool;催化标签A=公告实锤/B=盘面复盘/C=搭车存疑。跨行业票以催化归真实题材线。"}
    json.dump(out,open(os.path.join(L,f"涨停对链条_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    # 控制台
    print(f"=== {d} 涨停{len(df)}只 → 题材线{len(themes)}条 / 待归位{len(daiguiwei)}只 ===")
    for t in themes:
        print(f'\n【{t["大方向"]}】{t["家数"]}只 最高{t["最高连板"]}板 最早封{t["最早封板"]} 开板占比{t["开板占比"]}')
        print(f'  画像: {t["强度画像"]}')
        for s in t["环节"]:
            print(f'  ── {s["环节"]} ({s["家数"]}只,最早封{s["最早封板"]},开板占比{s["开板占比"]}) → {s["快判"]}')
            for g in s["个股"]:
                cui=g.get("催化") or "(模板卡位)"; src=g.get("来源档","")
                fdb=f'{g["封单比"]}%' if g["封单比"] is not None else "null"
                kbt="[开板]" if g["开板次数"]>0 else ""
                lbt=f'[{g["连板"]}板]' if g["连板"]>1 else ""
                print(f'      {g["首封"]} {g["名称"]}({g["代码"]}) 封单{fdb} {kbt}{lbt} · {cui} <{src}>')
    if daiguiwei:
        print(f'\n  待归位(行业兜底,agent补题材): '+", ".join(f'{u["名称"]}[{u.get("行业","")}]' for u in daiguiwei[:30]))

if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime("%Y%m%d"))
