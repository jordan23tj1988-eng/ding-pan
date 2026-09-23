# -*- coding: utf-8 -*-
"""涨停原因.py {d} —— 同花顺涨停池公开接口:当日全部涨停的【涨停原因】(reason_type)。
题材归位的B档基础证据源(公告A档可覆盖,搜索兜底)。产出 _学习/涨停原因_{d}.json。
口径:同花顺数据中心limit_up_pool;date=YYYYMMDD;原因为THS编辑聚合=B档,标来源"同花顺涨停原因"。"""
import os,sys,json,datetime,urllib.request
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
   "Referer":"https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html"}
def fetch(d):
    out={}
    for page in (1,2):
        url=(f"https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?page={page}&limit=200"
             "&field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970"
             f"&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={d}")
        j=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers=H),timeout=15).read().decode())
        if j.get("status_code")!=0: raise RuntimeError(str(j.get("status_msg")))
        info=(j.get("data") or {}).get("info") or []
        for x in info:
            c=str(x.get("code","")).zfill(6)
            ts=x.get("first_limit_up_time")
            fb=datetime.datetime.fromtimestamp(int(ts)).strftime("%H:%M") if ts else None
            out[c]=dict(名称=x.get("name"),原因=x.get("reason_type"),连板口径=x.get("high_days"),首封=fb)
        if len(info)<200: break
    return out
def main(d):
    m=fetch(d)
    json.dump({"日期":d,"来源":"同花顺涨停原因(B档)","条数":len(m),"映射":m},
        open(os.path.join(L,f"涨停原因_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"{d} 涨停原因{len(m)}条已存")
    for c,v in list(m.items())[:5]: print(" ",c,v["名称"],"|",v["原因"])
if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime("%Y%m%d"))
