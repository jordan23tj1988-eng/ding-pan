# -*- coding: utf-8 -*-
"""开盘后5分钟验证：只消费同日实时tick，缺窗口即不可用。"""
from __future__ import annotations
import argparse, collections, datetime
from pathlib import Path
from capability_common import valid_date, continuous_rows, write_json, result

def build(root: Path,d: str):
    valid_date(d); groups=collections.defaultdict(list)
    for ts,row in continuous_rows(root,d): groups[str(row.get('code')).zfill(6)].append((ts,row))
    out=[]
    for code,rows in groups.items():
        rows.sort(key=lambda x:x[0]); base=rows[0][0]
        try: t0=datetime.datetime.fromisoformat(base.replace('Z','+00:00'))
        except ValueError: continue
        win=[]
        for ts,r in rows:
            try: dt=datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))
            except ValueError: continue
            if 0 <= (dt-t0).total_seconds() <= 300: win.append(r)
        if len(win)<2: continue
        p0=win[0].get('pct'); p1=win[-1].get('pct')
        if isinstance(p0,(int,float)) and isinstance(p1,(int,float)): out.append({'code':code,'samples':len(win),'first_pct':p0,'last_pct':p1,'delta_pct':round(p1-p0,4)})
    source=f'盘中/{d}/realtime_ticks.jsonl'; status='pass' if out else 'unavailable'
    return result('open_verification',d,status,[source] if (root/'盘中'/d/'realtime_ticks.jsonl').is_file() else [],{'verified_codes':len(out),'min_samples_per_code':2},[] if out else ['缺少开盘后5分钟内同一代码至少两个实时tick'],'只验证已采集窗口，不从收盘或竞价单帧补造开盘表现')

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path);a=p.parse_args(argv);r=build(a.root.resolve(),a.d);write_json(a.out or a.root/'_学习'/f'开盘验证维_{a.d}.json',r);print(r);return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
