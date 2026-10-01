# -*- coding: utf-8 -*-
"""竞价9:20前后差分；没有双时点轨迹时不可用，绝不从单帧倒推撤单。"""
from __future__ import annotations
import argparse, collections
from pathlib import Path
from capability_common import valid_date, auction_rows, write_json, result

def build(root: Path,d: str):
    valid_date(d); groups=collections.defaultdict(list); source=[]
    for ts,row in auction_rows(root,d):
        code=str(row.get('代码') or row.get('code') or '').zfill(6)
        try: pct=float(row.get('高开幅度') if row.get('高开幅度') not in (None,'') else row.get('pct'))
        except (TypeError,ValueError): pct=None
        if code and pct is not None: groups[code].append((ts,pct))
    if (root/d/"竞价轨迹.csv").is_file(): source.append(f"{d}/竞价轨迹.csv")
    if (root/"盘中"/d/"auction_traj.jsonl").is_file(): source.append(f"盘中/{d}/auction_traj.jsonl")
    diffs=[]
    for code,rows in groups.items():
        rows.sort(key=lambda x:x[0]); pre=[x for x in rows if x[0][11:16] < '09:20'] if all(len(x[0])>=16 for x in rows) else []
        post=[x for x in rows if x[0][11:16] >= '09:20'] if all(len(x[0])>=16 for x in rows) else []
        if pre and post: diffs.append({'code':code,'pre_pct':pre[-1][1],'post_pct':post[-1][1],'delta_pct':round(post[-1][1]-pre[-1][1],4)})
    status='pass' if diffs else 'unavailable'
    return result('auction_cancel_diff',d,status,source,{'codes_with_pre_post':len(diffs),'trajectory_codes':len(groups)},[] if diffs else ['缺少同一代码9:20前后两时点轨迹'], '差分是价格/匹配轨迹位移代理，不把它命名为逐笔撤单量')

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path);a=p.parse_args(argv);r=build(a.root.resolve(),a.d);write_json(a.out or a.root/"_学习"/f"竞价撤单差分_{a.d}.json",r);print(r);return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
