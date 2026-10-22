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
    ev = events if isinstance(events, dict) else {}
    ev_status = ev.get("status") if event_path.is_file() else None
    ev_metrics = ev.get("metrics") if isinstance(ev.get("metrics"), dict) else {}
    ev_ok = event_path.is_file() and ev_status == "pass"      # 只认 pass：partial/unavailable 不得当“无风险”
    sources=["_学习/_交易日历.json"] if cal else []
    if event_path.is_file(): sources.append(event_path.relative_to(root).as_posix())
    sources.extend([str(x) for x in (ev.get("sources") or [])])
    errors=[]
    if not in_cal: errors.append("目标日不在已留档交易日历")
    elif not event_path.is_file(): errors.append(f"事件源缺失: _学习/风险事件_{d}.json 未生成(风险事件.py 未跑或失败)")
    elif ev_status != "pass": errors.append(f"事件源 status={ev_status}: "+"; ".join([str(x) for x in (ev.get("errors") or [])[:3]]))
    status="unavailable" if not in_cal else ("pass" if ev_ok else "partial")
    metrics={"is_trading_day":in_cal,"event_source_present":event_path.is_file(),
             "event_source_status":ev_status,"事件条数":ev_metrics.get("事件条数"),
             "覆盖维度":ev_metrics.get("覆盖维度"),"未接入维度":ev_metrics.get("未接入维度")}
    note="事件源缺失/降级时保持partial；不把缺事件解释成无风险"
    if ev_metrics.get("未接入维度"):
        note += "；未接入维度=" + "/".join(str(x) for x in ev_metrics["未接入维度"]) + "（不得据此声称无此类风险）"
    return result("risk_calendar",d,status,sources,metrics,errors,note)

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('d'); p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent); p.add_argument('--out',type=Path)
    a=p.parse_args(argv); r=build(a.root.resolve(),a.d); out=a.out or (a.root/"_学习"/f"风险日历_{a.d}.json"); write_json(out,r); print(r); return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
