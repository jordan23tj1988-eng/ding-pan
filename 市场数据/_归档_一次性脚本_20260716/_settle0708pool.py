# -*- coding: utf-8 -*-
"""07-08竞价选股池·今晨(07-09)初读结算。sina实时口径,零编造。"""
import re,json,urllib.request,datetime,os
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
# 07-08池8只(从当日auction页转录)：代码,名称,07-08竞价信号,题材线
POOL=[
 ("000977","浪潮信息","09:25一字·封单强(54亿)","算力·服务器整机(业绩288%)"),
 ("603137","恒尚节能","09:25一字·7板","存储跨界重组(孤峰)"),
 ("001208","华菱线缆","09:25一字","电网/线缆"),
 ("000524","岭南控股","09:25一字","旅游(散点)"),
 ("001229","魅视科技","09:25秒板·2板","算力·AI视觉(减持利空)"),
 ("301251","威尔高","09:30秒板·2板","算力·PCB/AI电源"),
 ("603296","华勤技术","09:30秒板","算力·服务器整机洼地"),
 ("002841","视源股份","09:34秒板·2板","算力·AI教育(异动利空)"),
]
def sina(codes):
    lst=",".join(("sh" if c[0] in "69" else "sz")+c for c in codes)
    req=urllib.request.Request("https://hq.sinajs.cn/list="+lst,headers={"Referer":"https://finance.sina.com.cn"})
    out={}
    for l in urllib.request.urlopen(req,timeout=10).read().decode("gbk").strip().split("\n"):
        mm=re.search(r'str_(?:sh|sz)(\d{6})="([^"]*)"',l)
        if not mm: continue
        p=mm.group(2).split(",")
        if len(p)>10 and float(p[2])>0:
            out[mm.group(1)]=dict(名=p[0],今开=float(p[1]),昨收=float(p[2]),现价=float(p[3]),高=float(p[4]),低=float(p[5]),成交额=float(p[9]))
    return out
def lim(c): return 19.9 if c[:2] in("30","68") else 9.9
q=sina([c for c,_,_,_ in POOL])
now=datetime.datetime.now()
inwin=now.replace(hour=9,minute=30,second=30)>now
res=[]
for c,nm,sig,th in POOL:
    s=q.get(c)
    if not s: res.append((c,nm,sig,th,None)); continue
    gk=round((s["今开"]/s["昨收"]-1)*100,2)
    cur=round((s["现价"]/s["昨收"]-1)*100,2)
    hi=round((s["高"]/s["昨收"]-1)*100,2)
    sealed = cur>=lim(c)-0.1
    je=("%.1f亿"%(s["成交额"]/1e8)) if s["成交额"]>0 else None
    res.append((c,nm,sig,th,dict(高开=gk,现涨=cur,盘中高=hi,封板=sealed,成交额=je)))
print("采到",len([r for r in res if r[4]]),"/",len(POOL),"| inwin成交额有效=",inwin)
for c,nm,sig,th,d in res:
    if d: print(f"  {nm}({c}) {th[:10]:12} 高开{d['高开']:+.1f}% 现{d['现涨']:+.1f}% 高{d['盘中高']:+.1f}% {'封板' if d['封板'] else '未封'} 额{d['成交额']}")
    else: print(f"  {nm}({c}) 未取到")
json.dump({"pool_date":"20260708","read_date":"20260709","read_time":now.strftime("%H:%M"),
  "明细":[dict(代码=c,名称=nm,信号=sig,题材=th,今晨=d) for c,nm,sig,th,d in res]},
  open(L+"/竞价池初读_20260708.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
