# -*- coding: utf-8 -*-
import socket; socket.setdefaulttimeout(20)
import importlib.util, os, json, collections, datetime
import pandas as pd
spec = importlib.util.spec_from_file_location("dl", "市场数据下载.py")
dl = importlib.util.module_from_spec(spec); spec.loader.exec_module(dl)
d="20260715"; OUT=os.path.join(dl.BASE,d)
zt=pd.read_csv(os.path.join(OUT,"zt_pool.csv"),dtype=str)
dt=pd.read_csv(os.path.join(OUT,"dt_pool.csv"),dtype=str) if os.path.exists(os.path.join(OUT,"dt_pool.csv")) else None
zb=pd.read_csv(os.path.join(OUT,"zb_pool.csv"),dtype=str) if os.path.exists(os.path.join(OUT,"zb_pool.csv")) else None
lhb_path=os.path.join(OUT,"lhb.csv"); lhb=pd.read_csv(lhb_path,dtype=str) if os.path.exists(lhb_path) else None
zt_s=dl._stat(zt); dt_s=dl._stat(dt); zb_s=dl._stat(zb)
lb=collections.Counter(); top=0
if "连板数" in zt_s.columns:
    for v in zt_s["连板数"].fillna(1):
        try:n=int(float(v))
        except:n=1
        lb[str(n)]+=1; top=max(top,n)
ind=collections.Counter(); ind2=collections.Counter()
for _,row in zt_s.iterrows():
    try:n=int(float(row.get("连板数",1)))
    except:n=1
    hy=row.get("所属行业") if "所属行业" in zt_s.columns else None
    if hy and str(hy)!='nan':
        ind[hy]+=1
        if n>=2: ind2[hy]+=1
n_zt=len(zt_s); n_dt=len(dt_s) if dt_s is not None else 0; n_zb=len(zb_s) if zb_s is not None else 0
n_cut=len(zt)-len(zt_s)
rate=round(n_zb/(n_zt+n_zb),3) if (n_zt+n_zb)>0 else None
try: to=dl.turnover_yi()
except: to=None
summary={"日期":d,"两市成交额_亿":to,"涨停家数":n_zt,"跌停家数":n_dt,"炸板家数":n_zb,
  "炸板率":rate,"最高连板":top,"连板梯队":{k:lb[k] for k in sorted(lb,key=lambda x:-int(x))},
  "涨停行业扎堆Top12":ind.most_common(12),"连板≥2行业Top8":ind2.most_common(8),
  "统计口径":"剔ST/退/N/C(原始csv保留)","剔除涨停家数":n_cut,
  "龙虎榜条数":len(lhb) if lhb is not None else 0,
  "龙虎榜状态":"null(同日18:5x未发布,东财直连返回空)" if (lhb is None or len(lhb)==0) else "ok",
  "抓取时间":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
dl._safe_dump(summary,os.path.join(OUT,"summary.json"))
print(json.dumps(summary,ensure_ascii=False,indent=1))
