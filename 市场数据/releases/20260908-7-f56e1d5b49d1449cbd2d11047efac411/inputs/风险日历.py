# -*- coding: utf-8 -*-
"""日期化风险日历适配器；无事件源时明确 partial，不补造事件。"""
from __future__ import annotations
import argparse
from pathlib import Path
from capability_common import valid_date, load_json, write_json, result

def build(root: Path, d: str):
    valid_date(d); cal=load_json(root/"_学习"/"_交易日历.json", [])
    cal={str(x).replace('-','') for x in cal} if isinstance(cal,list) else set()
    in_cal=d in cal
    # 事件源必须是独立文件；不存在时不能声称“无风险事件”。
    event_path=root/"_学习"/f"风险事件_{d}.json"
    events=load_json(event_path, None)
    sources=["_学习/_交易日历.json"] if cal else []
    if event_path.is_file(): sources.append(event_path.relative_to(root).as_posix())
    status="pass" if in_cal and isinstance(events, (dict,list)) else ("partial" if in_cal else "unavailable")
    return result("risk_calendar",d,status,sources,{"is_trading_day":in_cal,"event_source_present":event_path.is_file()},
                   [] if in_cal else ["目标日不在已留档交易日历"],
                   "事件源缺失时保持partial；不把缺事件解释成无风险")

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('d'); p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent); p.add_argument('--out',type=Path)
    a=p.parse_args(argv); r=build(a.root.resolve(),a.d); out=a.out or (a.root/"_学习"/f"风险日历_{a.d}.json"); write_json(out,r); print(r); return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
