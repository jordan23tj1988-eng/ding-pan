# -*- coding: utf-8 -*-
"""涨停池回填.py —— 同花顺涨停池一年历史→_学习/_ths_zt_pool.json(断点续传,反复跑至补齐)。
v1 2026-07-10 用户拍板"历史回填质量库":样本1.6k→~2万,穿越退潮期,规则/胜率才站得住。
字段:code/name/order_amount(封单额元)/open_num(开板次数)/high_days(连板字符串)/
     first_limit_up_time(首封ts)/latest(收盘)/change_rate。
缺EM才有的字段(流通市值/换手/成交额)→训练侧标null(零编造,因子按覆盖参与)。"""
import os,sys,json,time,glob,datetime,urllib.request
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
OUT=os.path.join(L,"_ths_zt_pool.json")
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
   "Referer":"https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html"}
def fetch_day(d):
    out=[]
    for page in (1,2,3):
        url=(f"https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?page={page}&limit=200"
             "&field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970"
             f"&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={d}")
        j=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers=H),timeout=15).read().decode())
        if j.get("status_code")!=0: raise RuntimeError(str(j.get("status_msg"))[:50])
        info=(j.get("data") or {}).get("info") or []
        for x in info:
            out.append(dict(code=str(x.get("code","")).zfill(6),name=x.get("name"),
                order_amount=x.get("order_amount"),open_num=x.get("open_num"),
                high_days=x.get("high_days"),first_limit_up_time=x.get("first_limit_up_time"),
                latest=x.get("latest"),change_rate=x.get("change_rate")))
        if len(info)<200: break
    return out
def main(start='20250701'):
    t=json.load(open(OUT,encoding='utf-8')) if os.path.isfile(OUT) else {}
    # 交易日历:直接用市场温度表的日期(已回填250日)
    wt=json.load(open(os.path.join(L,'_市场温度表.json'),encoding='utf-8'))
    days=[d for d in sorted(wt) if d>=start]
    todo=[d for d in days if d not in t]
    print(f"THS池回填待取{len(todo)}/{len(days)}日",flush=True)
    for i,d in enumerate(todo):
        try: t[d]=fetch_day(d)
        except Exception as e: print("  失败",d,str(e)[:40],flush=True); continue
        if (i+1)%15==0:
            json.dump(t,open(OUT,'w',encoding='utf-8'),ensure_ascii=False)
            print(f"  进度{i+1}/{len(todo)} 最近{d} 当日{len(t[d])}只",flush=True)
        time.sleep(0.4)
    json.dump(t,open(OUT,'w',encoding='utf-8'),ensure_ascii=False)
    n=sum(len(v) for v in t.values())
    print(f"THS池: {len(t)}日 合计{n}条")
if __name__=='__main__':
    main(sys.argv[1] if len(sys.argv)>1 else '20250701')
