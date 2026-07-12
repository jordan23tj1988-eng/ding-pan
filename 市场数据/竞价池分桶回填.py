# -*- coding: utf-8 -*-
"""竞价池分桶回填.py —— 竞价路A档历史分桶库(2026-07-12建,08号竞价命门agent优化①)。
★用 _学习/_ths_zt_pool.json(一年THS涨停池,含首封时间戳)零后视镜重建每日竞价池
  (口径逐条复刻 竞价池结算.py: 首封≤09:31入池,一字=首封≤09:25,剔ST/退/N/C),
  接 _bars_cache 算T+1执行收益(T+1开→T+1收),叠 _市场温度表 温度档,
  产出 信号×连板×高开档×温度 分桶胜率库 → _学习/_竞价池分桶库.json。
★零后视镜:池由T日收盘已知信息决定;高开档用T+1开盘价=执行时点(9:25竞价)已知,
  只作"到价才决策"的执行闸门统计,不进选池条件。
★诚实边界:桶均值≠个股预言;bars缺票如实计数(幸存者偏差);n≥10才出桶,n<25标小样本。
用法: python3 竞价池分桶回填.py [--verify]   (--verify=金标对照20260709/0710线上版)"""
import os,sys,json,re,glob
from datetime import datetime,timezone,timedelta
import pandas as pd

BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache")
CST=timezone(timedelta(hours=8))

def _junk(name):  # 同 竞价池结算.py
    s=str(name or "")
    return ("ST" in s.upper()) or ("退" in s) or s.startswith("N") or s.startswith("C")

def _hm(ts):
    """THS first_limit_up_time(UTC秒) → CST 'HH:MM'"""
    try: return datetime.fromtimestamp(int(ts),CST).strftime("%H:%M")
    except Exception: return None

def _lb(hd):
    """high_days '5天4板'→4;空/'首板'→1"""
    m=re.search(r"(\d+)板",str(hd or ""))
    return int(m.group(1)) if m else 1

_BARS={}
def bars(c):
    if c in _BARS: return _BARS[c]
    f=os.path.join(CDIR,c+".csv"); b=None
    if os.path.isfile(f):
        b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
        b=b.reset_index(drop=True)
    _BARS[c]=b; return b

def build_pool(day_rows):
    pool=[]
    for r in day_rows:
        if _junk(r.get("name")): continue
        fb=_hm(r.get("first_limit_up_time"))
        if not fb or fb>"09:31": continue
        lb=_lb(r.get("high_days"))
        sig=("一字" if fb<="09:25" else "秒板")+(f"·{lb}板" if lb>1 else "·首板")
        pool.append(dict(代码=str(r["code"]).zfill(6),名称=str(r.get("name")),首封=fb,连板=lb,
                         信号=sig,炸板=int(r.get("open_num") or 0),封单额亿=round(float(r.get("order_amount") or 0)/1e8,3)))
    return sorted(pool,key=lambda x:x["首封"])

def settle(c,dprev,dnext):
    """返回 (T1高开,执行,信号,封单比) 或 None;停牌错位(T+1行≠dnext)剔除"""
    b=bars(c)
    if b is None: return None
    idx=b.index[b['date']==dprev]
    if not len(idx) or idx[0]+1>=len(b): return None
    i=idx[0]
    if str(b.loc[i+1,'date'])!=dnext: return None  # 停牌错位,T+1不可执行
    Tc=float(b.loc[i,'close']); o1=float(b.loc[i+1,'open']); c1=float(b.loc[i+1,'close'])
    mv=b.loc[i,'circ_mv亿'] if 'circ_mv亿' in b.columns else None
    return (round((o1/Tc-1)*100,2),round((c1/o1-1)*100,2),round((c1/Tc-1)*100,2),
            (float(mv) if mv==mv else None))

def gk_bucket(g): return "低开≤0" if g<=0 else ("高开0~5" if g<5 else "高开≥5")
def wd_bucket(w): return None if w is None else ("冷<40" if w<40 else ("中40~65" if w<65 else "热≥65"))
def lb_bucket(l): return "首板" if l==1 else ("2板" if l==2 else "3板+")
def fd_bucket(fdb): return None if fdb is None else ("<0.5%" if fdb<0.5 else ("0.5~1.5%" if fdb<1.5 else ("1.5~4%" if fdb<4 else "≥4%")))

def agg(samples):
    ex=[s["执行"] for s in samples]; n=len(ex)
    if n==0: return None
    d=dict(n=n,执行胜率=round(sum(1 for e in ex if e>0)/n*100,1),执行均涨=round(sum(ex)/n,2),
           次日封板率=round(sum(1 for s in samples if s["次日封板"])/n*100,1),
           信号均涨=round(sum(s["信号"] for s in samples)/n,2))
    if n<25: d["注"]="小样本"
    return d

def main(verify=False):
    ths=json.load(open(os.path.join(L,"_ths_zt_pool.json"),encoding="utf-8"))
    wdt=json.load(open(os.path.join(L,"_市场温度表.json"),encoding="utf-8"))
    bench={}
    bp=os.path.join(L,"_全场涨停执行均收_回填.json")
    if os.path.isfile(bp):
        _b=json.load(open(bp,encoding="utf-8"))
        bench={k:(v.get("执行均收") if isinstance(v,dict) else v) for k,v in _b.items()} if isinstance(_b,dict) else {}
    days=sorted(ths.keys())
    S=[]; miss=0; total_pool=0; daily=[]
    for di,d in enumerate(days[:-1]):
        dnext=days[di+1]
        pool=build_pool(ths[d]); total_pool+=len(pool)
        wd=(wdt.get(d) or {}).get("温度")
        drets=[]
        for t in pool:
            r=settle(t["代码"],d,dnext)
            if r is None: miss+=1; continue
            gk,ex,sg,mv=r
            fdb=round(t["封单额亿"]/mv*100,2) if (mv and mv>0) else None
            nx={x["code"] for x in ths.get(dnext,[])}
            S.append(dict(日=d,代码=t["代码"],信号=t["信号"].split("·")[0],连板=t["连板"],炸板=t["炸板"],
                          封单比=fdb,温度=wd,T1高开=gk,执行=ex,信号收益=sg,次日封板=t["代码"] in nx))
            drets.append(ex)
        if drets:
            daily.append(dict(日=d,n=len(drets),池均收=round(sum(drets)/len(drets),2),基准=bench.get(d)))
    cov=round((1-miss/max(total_pool,1))*100,1)
    # ---- 分桶 ----
    def bucketize(keyf):
        out={}
        for s in S:
            k=keyf(s)
            if k is None: continue
            out.setdefault(k,[]).append(dict(执行=s["执行"],信号=s["信号收益"],次日封板=s["次日封板"]))
        return {k:agg(v) for k,v in sorted(out.items()) if agg(v)}
    lib=dict(
        更新=datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
        窗口=f"{days[0]}~{days[-1]}",样本=len(S),池票总数=total_pool,bars覆盖率pct=cov,
        口径=("池=THS涨停池零后视镜重建(首封≤09:31,一字≤09:25,剔ST/退/N/C,与竞价池结算.py同构);"
             "执行=T+1开→T+1收;高开档=执行时点已知只作闸门;温度=T日值(收盘已知);停牌错位剔除;"
             "★幸存者偏差:bars缺票已计数如实标注;桶均值≠个股预言"),
        基准=dict(池整体=agg([dict(执行=s["执行"],信号=s["信号收益"],次日封板=s["次日封板"]) for s in S])),
        一维=dict(
            按信号=bucketize(lambda s:s["信号"]),
            按连板=bucketize(lambda s:lb_bucket(s["连板"])),
            按高开档=bucketize(lambda s:gk_bucket(s["T1高开"])),
            按温度=bucketize(lambda s:wd_bucket(s["温度"])),
            按炸板=bucketize(lambda s:"未炸" if s["炸板"]==0 else "炸1+"),
            按封单比=bucketize(lambda s:fd_bucket(s["封单比"]))),
        交叉=dict(
            信号x高开档=bucketize(lambda s:f'{s["信号"]}|{gk_bucket(s["T1高开"])}'),
            连板x高开档=bucketize(lambda s:f'{lb_bucket(s["连板"])}|{gk_bucket(s["T1高开"])}'),
            温度x高开档=bucketize(lambda s:(f'{wd_bucket(s["温度"])}|{gk_bucket(s["T1高开"])}' if s["温度"] is not None else None)),
            信号x温度=bucketize(lambda s:(f'{s["信号"]}|{wd_bucket(s["温度"])}' if s["温度"] is not None else None)),
            信号x连板=bucketize(lambda s:f'{s["信号"]}|{lb_bucket(s["连板"])}')),
        稳定性_高开档分月={},
        日度增益=dict(
            有基准天数=sum(1 for x in daily if x["基准"] is not None),
            池均收_全期=round(sum(x["池均收"]*x["n"] for x in daily)/max(sum(x["n"] for x in daily),1),2),
            平均日增益pp=round(sum(x["池均收"]-x["基准"] for x in daily if x["基准"] is not None)
                          /max(sum(1 for x in daily if x["基准"] is not None),1),2),
            增益为正天占比pct=round(sum(1 for x in daily if x["基准"] is not None and x["池均收"]>x["基准"])
                          /max(sum(1 for x in daily if x["基准"] is not None),1)*100,1)))
    # 稳定性:高开档效应分月
    bym={}
    for s in S:
        m=s["日"][:6]; bym.setdefault(m,{}).setdefault(gk_bucket(s["T1高开"]),[]).append(s["执行"])
    for m in sorted(bym):
        row={}
        for g in ("低开≤0","高开0~5","高开≥5"):
            v=bym[m].get(g,[])
            row[g]=dict(n=len(v),均涨=round(sum(v)/len(v),2)) if v else None
        lo,hi=row.get("低开≤0"),row.get("高开≥5")
        row["低开减高开pp"]=round(lo["均涨"]-hi["均涨"],2) if (lo and hi) else None
        lib["稳定性_高开档分月"][m]=row
    out=os.path.join(L,"_竞价池分桶库.json")
    json.dump(lib,open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"窗口{lib['窗口']} 样本{len(S)}/{total_pool}(覆盖{cov}%) → {out}")
    print("池整体:",json.dumps(lib["基准"]["池整体"],ensure_ascii=False))
    print("按高开档:",json.dumps(lib["一维"]["按高开档"],ensure_ascii=False))
    # ---- 金标对照 ----
    if verify:
        print("\n===金标对照(THS回填 vs 东财线上发出版)===")
        for d in ("20260709","20260710"):
            fp=os.path.join(L,f"竞价池发出_{d}.json")
            if not os.path.isfile(fp): continue
            online={x["代码"]:x for x in json.load(open(fp,encoding="utf-8"))["池"]}
            mine={x["代码"]:x for x in build_pool(ths.get(d,[]))}
            both=set(online)&set(mine)
            sig_same=sum(1 for c in both if online[c]["信号"]==mine[c]["信号"])
            print(f"{d}: 线上{len(online)}只 回填{len(mine)}只 交集{len(both)} 信号一致{sig_same}/{len(both)}"
                  f" | 仅线上:{sorted(set(online)-set(mine))} 仅回填:{sorted(set(mine)-set(online))}")
        # 复现20260709结算汇总
        d,dn="20260709","20260710"
        sp=os.path.join(L,f"竞价池结算_{d}.json")
        if os.path.isfile(sp):
            ol=json.load(open(sp,encoding="utf-8"))["汇总"]
            pool=json.load(open(os.path.join(L,f"竞价池发出_{d}.json"),encoding="utf-8"))["池"]
            nx={x["code"] for x in ths.get(dn,[])}
            ex=[]; win=0; seal=0
            for t in pool:
                r=settle(str(t["代码"]).zfill(6),d,dn)
                if r is None: continue
                ex.append(r[1]); win+=r[1]>0; seal+=str(t["代码"]).zfill(6) in nx
            print(f"{d}结算复现: 胜率{win}/{len(ex)} 均收{round(sum(ex)/len(ex),2)}% 封板{seal}/{len(pool)}"
                  f"  vs 线上 {ol['执行胜率']} / {ol['执行均收']}% / {ol['次日封板']}")

if __name__=="__main__":
    main(verify="--verify" in sys.argv)
