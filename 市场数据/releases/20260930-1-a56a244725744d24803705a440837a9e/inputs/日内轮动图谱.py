# -*- coding: utf-8 -*-
"""日内轮动图谱：实时tick×题材归位聚合；缺少双时点/双题材不结论。"""
from __future__ import annotations
import argparse,collections
from pathlib import Path
from capability_common import valid_date,continuous_rows,read_mapping,write_json,result

def build(root:Path,d:str):
    valid_date(d); mp=read_mapping(root,d); by=collections.defaultdict(list)
    for ts,row in continuous_rows(root,d):
        code=str(row.get('code')).zfill(6); theme=(mp.get(code) or {}).get('大方向') if isinstance(mp.get(code),dict) else None; v=row.get('pct')
        if theme and isinstance(v,(int,float)): by[(ts,theme)].append(float(v))
    graph=[]
    for (ts,theme),vs in sorted(by.items()): graph.append({'ts':ts,'theme':theme,'n':len(vs),'mean_pct':round(sum(vs)/len(vs),4)})
    points=sorted({x['ts'] for x in graph}); themes=sorted({x['theme'] for x in graph}); status='pass' if len(points)>=2 and len(themes)>=2 else 'unavailable'
    src=[f'盘中/{d}/realtime_ticks.jsonl',f'_学习/题材归位_{d}.json']; return result('intraday_rotation_graph',d,status,[x for x in src if (root/x).is_file()],{'time_points':len(points),'themes':len(themes),'rows':len(graph)},[] if status=='pass' else ['缺少至少两个盘中时间点或两个已归位题材'],'题材名只来自题材归位唯一真源；缺映射不归因') | {'graph':graph}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path);a=p.parse_args(argv);r=build(a.root.resolve(),a.d);write_json(a.out or a.root/'_学习'/f'日内轮动图谱_{a.d}.json',r);print(r);return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
