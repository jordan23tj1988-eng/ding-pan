# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,json,re
from datetime import datetime
from pathlib import Path

DATES=('20260902','20260904','20260905')

def _load(p):
    try:return json.loads(p.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError,TypeError):return None

def evaluate(diag:Path, progress:Path, evidence_dir:Path|None=None):
    parts=[p.read_text(encoding='utf-8',errors='replace') for p in (diag,progress) if p.is_file()]
    text='\n'.join(parts); evidence_dir=evidence_dir or diag.parent/'evidence'
    items=[]
    for d in DATES:
        verdict=None; verdict_path=None; same_day=[]
        if evidence_dir.is_dir():
            for p in evidence_dir.rglob(f'*{d}*.json'):
                obj=_load(p)
                if isinstance(obj,dict):
                    same_day.append(p.relative_to(evidence_dir).as_posix())
                    if p.name.startswith('history_recovery_verdict_') and obj.get('status') in ('confirmed_recoverable','confirmed_unrecoverable'):
                        verdict=obj['status']; verdict_path=p
        hits=[ln.strip() for ln in text.splitlines() if d in ln and any(k in ln.upper() for k in ['BLOCKED','缺失','损坏','没有快照','不可','欠账'])]
        if verdict:
            status='confirmed'; reason=verdict
        elif hits:
            status='blocked_by_diagnostic'; reason='存在诊断阻断证据，但没有显式历史裁决'
        else:
            status='not_confirmed'; reason='未找到显式历史裁决，禁止回填'
        items.append({'date':d,'status':status,'verdict':verdict,'verdict_path':verdict_path.relative_to(evidence_dir).as_posix() if verdict_path else None,'date_matching_file_count':len(same_day),'evidence':hits[:8],'reason':reason})
    return {'status':'pass' if all(x['status']=='confirmed' for x in items) else 'blocked','items':items,'policy':'缺证据不回填；只有显式confirmed_recoverable/confirmed_unrecoverable才关闭历史项','evidence_dir':str(evidence_dir)}

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--diagnosis',type=Path,required=True);ap.add_argument('--progress',type=Path,required=True);ap.add_argument('--evidence-dir',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args(argv)
    r=evaluate(a.diagnosis,a.progress,a.evidence_dir);r['generated_at']=datetime.now().isoformat(timespec='seconds');a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
