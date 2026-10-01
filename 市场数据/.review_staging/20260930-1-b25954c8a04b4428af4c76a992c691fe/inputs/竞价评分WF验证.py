# -*- coding: utf-8 -*-
"""竞价评分WF验证.py —— 竞价分走查(walk-forward,零后视镜):
每月只用该月之前的样本建分桶库→给当月池票打分→对照当月真实执行收益。
指标:月度RankIC(竞价分vs执行收益秩相关)、三分位价差(高分组-低分组执行均涨)、单调性。
★评分公式与 竞价评分.py 共用同一函数(import),杜绝口径漂移。
产出: _学习/_竞价评分WF.json。用法: python3 竞价评分WF验证.py"""
import os,sys,json,importlib.util
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
def _imp(name,fn):
    sp=importlib.util.spec_from_file_location(name,os.path.join(BASE,fn))
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
BF=_imp("bf","竞价池分桶回填.py")   # build_pool/settle/桶函数
SC=_imp("sc","竞价评分.py")         # build_scorecard/score_stock(共用评分公式)

def collect_samples():
    ths=json.load(open(os.path.join(L,"_ths_zt_pool.json"),encoding="utf-8"))
    wdt=json.load(open(os.path.join(L,"_市场温度表.json"),encoding="utf-8"))
    days=sorted(ths.keys()); S=[]
    for di,d in enumerate(days[:-1]):
        dnext=days[di+1]; wd=(wdt.get(d) or {}).get("温度")
        for t in BF.build_pool(ths[d]):
            r=BF.settle(t["代码"],d,dnext)
            if r is None: continue
            gk,ex,sg,mv=r
            fdb=round(t["封单额亿"]/mv*100,2) if (mv and mv>0) else None
            S.append(dict(日=d,月=d[:6],代码=t["代码"],信号=t["信号"],连板=t["连板"],炸板=t["炸板"],
                          封单比=fdb,温度=wd,T1高开=gk,执行=ex))
    return S

def agg(vs):
    n=len(vs)
    if n<10: return None
    return dict(n=n,执行胜率=round(sum(1 for v in vs if v>0)/n*100,1),执行均涨=round(sum(vs)/n,2))
def build_lib(train):
    """从训练样本构建与 _竞价池分桶库.json 同构的最小lib(评分所需字段)"""
    def bk(keyf):
        g={}
        for s in train:
            k=keyf(s)
            if k is None: continue
            g.setdefault(k,[]).append(s["执行"])
        return {k:agg(v) for k,v in g.items() if agg(v)}
    sig=lambda s:s["信号"].split("·")[0]
    return {"基准":{"池整体":agg([s["执行"] for s in train])},
        "一维":{"按信号":bk(sig),"按连板":bk(lambda s:BF.lb_bucket(s["连板"])),
                "按炸板":bk(lambda s:"未炸" if s["炸板"]==0 else "炸1+"),
                "按封单比":bk(lambda s:BF.fd_bucket(s["封单比"])),
                "按温度":bk(lambda s:BF.wd_bucket(s["温度"]))},
        "交叉":{"信号x连板":bk(lambda s:f'{sig(s)}|{BF.lb_bucket(s["连板"])}'),
                "信号x高开档":bk(lambda s:f'{sig(s)}|{BF.gk_bucket(s["T1高开"])}')}}

def rankic(xs,ys):
    n=len(xs)
    if n<3: return None
    def rk(v):
        o=sorted(range(n),key=lambda i:v[i]); r=[0]*n
        for j,i in enumerate(o): r[i]=j
        return r
    rx,ry=rk(xs),rk(ys); mx=sum(rx)/n; my=sum(ry)/n
    num=sum((rx[i]-mx)*(ry[i]-my) for i in range(n))
    dx=sum((r-mx)**2 for r in rx)**.5; dy=sum((r-my)**2 for r in ry)**.5
    return round(num/(dx*dy),3) if dx*dy else None

def main():
    S=collect_samples()
    months=sorted({s["月"] for s in S})
    res=[]; allsc=[]
    for m in months[2:]:  # 前2个月只做训练
        train=[s for s in S if s["月"]<m]; test=[s for s in S if s["月"]==m]
        if len(train)<200 or len(test)<30: continue
        lib=build_lib(train)
        sc,v0,_=SC.build_scorecard(lib)
        scored=[]
        for s in test:
            t=dict(信号=s["信号"],连板=s["连板"],炸板=s["炸板"],封单比=s["封单比"])
            score,_c=SC.score_stock(t,s["温度"],sc,v0)
            scored.append((score,s["执行"],s["T1高开"]))
            allsc.append(dict(月=m,分=score,执行=s["执行"],高开=s["T1高开"]))
        scored.sort(key=lambda x:x[0])
        n=len(scored); k=n//3
        lo=[x[1] for x in scored[:k]]; hi=[x[1] for x in scored[-k:]]
        ic=rankic([x[0] for x in scored],[x[1] for x in scored])
        res.append(dict(月=m,n=n,训练n=len(train),RankIC=ic,
            低分组均涨=round(sum(lo)/len(lo),2),高分组均涨=round(sum(hi)/len(hi),2),
            价差pp=round(sum(hi)/len(hi)-sum(lo)/len(lo),2)))
    # 汇总
    ics=[r["RankIC"] for r in res if r["RankIC"] is not None]
    sp=[r["价差pp"] for r in res]
    # 全期三分位(拼所有WF月)
    allsc.sort(key=lambda x:x["分"])
    n=len(allsc); k=n//3
    ter=[allsc[:k],allsc[k:2*k],allsc[2*k:]]
    tstats=[dict(组=g,n=len(t),执行均涨=round(sum(x["执行"] for x in t)/len(t),2),
                 胜率=round(sum(1 for x in t if x["执行"]>0)/len(t)*100,1))
            for g,t in zip(("低分1/3","中分1/3","高分1/3"),ter)]
    # 闸门内(高开<5)的分层
    gated=[x for x in allsc if x["高开"]<5]
    gated.sort(key=lambda x:x["分"]); ng=len(gated); kg=ng//3
    gstats=[dict(组=g,n=len(t),执行均涨=round(sum(x["执行"] for x in t)/len(t),2),
                 胜率=round(sum(1 for x in t if x["执行"]>0)/len(t)*100,1))
            for g,t in zip(("闸门内低分","闸门内中分","闸门内高分"),(gated[:kg],gated[kg:2*kg],gated[2*kg:]))]
    out=dict(口径="WF零后视镜:每月只用之前样本建库打分;评分公式=竞价评分.py同函数;执行=T+1开→收",
        月度=res,IC均值=round(sum(ics)/len(ics),3) if ics else None,
        IC为正月占比=round(sum(1 for i in ics if i>0)/len(ics)*100,1) if ics else None,
        价差均值pp=round(sum(sp)/len(sp),2) if sp else None,
        价差为正月占比=round(sum(1 for s in sp if s>0)/len(sp)*100,1) if sp else None,
        全期三分位=tstats,闸门内三分位=gstats)
    json.dump(out,open(os.path.join(L,"_竞价评分WF.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("月度WF:")
    for r in res: print(" ",r)
    print("IC均值",out["IC均值"],"| IC>0月占比",out["IC为正月占比"],"% | 价差均值",out["价差均值pp"],"pp | 价差>0月占比",out["价差为正月占比"],"%")
    print("全期三分位:",json.dumps(tstats,ensure_ascii=False))
    print("闸门内三分位:",json.dumps(gstats,ensure_ascii=False))
if __name__=="__main__":
    main()
