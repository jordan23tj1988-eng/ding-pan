# -*- coding: utf-8 -*-
"""日内温度曲线：按实时tick时间聚合涨跌分布；缺少多时点则不可用。"""
from __future__ import annotations
import argparse, collections
from pathlib import Path
from capability_common import valid_date,continuous_rows,write_json,result

def build(root:Path,d:str):
    valid_date(d); by=collections.defaultdict(list)
    for ts,row in continuous_rows(root,d):
        v=row.get('pct')
        if isinstance(v,(int,float)): by[ts].append(float(v))
    curve=[]
    for ts,vs in sorted(by.items()):
        if not vs: continue
        curve.append({'ts':ts,'n':len(vs),'up':sum(v>0 for v in vs),'flat':sum(v==0 for v in vs),'down':sum(v<0 for v in vs),'mean_pct':round(sum(vs)/len(vs),4)})
    src=f'盘中/{d}/realtime_ticks.jsonl'; status='pass' if len(curve)>=2 else 'unavailable'
    return result('intraday_temperature_curve',d,status,[src] if (root/'盘中'/d/'realtime_ticks.jsonl').is_file() else [],{'time_points':len(curve)},[] if len(curve)>=2 else ['缺少至少两个盘中时间点的实时涨跌分布'],'该曲线是观察池样本分布，不等同全市场温度；样本不足不输出结论') | {'curve':curve}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path);a=p.parse_args(argv);r=build(a.root.resolve(),a.d);write_json(a.out or a.root/'_学习'/f'日内温度曲线_{a.d}.json',r);print(r);return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
