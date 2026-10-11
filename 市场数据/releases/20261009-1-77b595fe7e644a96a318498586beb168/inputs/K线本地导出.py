# -*- coding: utf-8 -*-
"""K线本地导出.py [批量N] —— 从百度网盘年度zip(全A日K raw)批量导出涨停股K线到 _bars_cache。
v1 2026-07-10: 质量库扩容用户拍板。来源=网盘2025/2026.zip(每股csv,gbk,含turnover换手%/circ_mv流通市值万元),
volume单位手→×100对齐sina(股);2026.zip止于06-26,尾部保留/续接既有sina缓存行。
新缓存schema 8列: date,open,high,low,close,volume,turnover,circ_mv亿。断点续传:已带turnover列的跳过。"""
import os,sys,json,glob,zipfile,io
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache")
ND=glob.glob('/sessions/*/mnt/BaiduNetdiskDownload/全A日K')
def suf(c): return 'SH' if c[0] in '69' else ('BJ' if (c[0] in '48' or c.startswith('92')) else 'SZ')
def main(batch=400):
    codes=set()
    ths=json.load(open(os.path.join(L,'_ths_zt_pool.json'),encoding='utf-8'))
    for d,rows in ths.items():
        for x in rows: codes.add(str(x['code']).zfill(6))
    for p in glob.glob(os.path.join(BASE,'20*','zt_pool.csv')):
        df=pd.read_csv(p,dtype={'代码':str}); codes.update(df['代码'].str.zfill(6))
    codes=sorted(codes)
    todo=[]
    for c in codes:
        f=os.path.join(CDIR,c+'.csv')
        if os.path.isfile(f) and 'turnover' in open(f,encoding='utf-8').readline(): continue
        todo.append(c)
    print(f"代码总数{len(codes)} 待导出{len(todo)}",flush=True)
    if not todo: print("EXPORT_DONE"); return
    if not ND: print("网盘未挂载!"); return
    z25=zipfile.ZipFile(os.path.join(ND[0],'2025.zip')); z26=zipfile.ZipFile(os.path.join(ND[0],'2026.zip'))
    n25=set(z25.namelist()); n26=set(z26.namelist())
    ok=miss=0
    for c in todo[:batch]:
        parts=[]
        for z,ns,yr in ((z25,n25,'2025'),(z26,n26,'2026')):
            m=f"{yr}/{c}.{suf(c)}.csv"
            if m in ns:
                try:
                    df=pd.read_csv(io.BytesIO(z.read(m)),encoding='gbk')
                    df=df.rename(columns={'datetime':'date'})
                    df=df[df['date']>='2025-06-01']
                    parts.append(pd.DataFrame(dict(date=df['date'],open=df['open'],high=df['high'],
                        low=df['low'],close=df['close'],volume=df['volume']*100,
                        turnover=df['turnover'],circ_mv亿=pd.to_numeric(df['circ_mv'],errors='coerce')/1e4)))
                except Exception: pass
        old=os.path.join(CDIR,c+'.csv')
        if parts:
            new=pd.concat(parts).drop_duplicates('date').sort_values('date')
            mx=new['date'].max()
            if os.path.isfile(old):
                try:
                    ob=pd.read_csv(old); ob=ob[ob['date']>mx]
                    if len(ob):
                        ob['turnover']=None; ob['circ_mv亿']=None
                        new=pd.concat([new,ob[new.columns]])
                except Exception: pass
            new.to_csv(old,index=False); ok+=1
        else:
            miss+=1
            if not os.path.isfile(old):
                open(os.path.join(CDIR,c+'.miss'),'w').write('netdisk无此code')
    print(f"本批完成: 导出{ok} 网盘缺{miss} 剩余{max(0,len(todo)-batch)}",flush=True)
if __name__=='__main__':
    main(int(sys.argv[1]) if len(sys.argv)>1 else 400)
