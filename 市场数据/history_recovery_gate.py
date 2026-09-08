# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,json,re
from datetime import datetime
from pathlib import Path

def evaluate(diag: Path, progress: Path):
    text='\n'.join(p.read_text(encoding='utf-8',errors='replace') for p in [diag,progress] if p.is_file())
    blocked=[]
    for d in ['20260902','20260904','20260905']:
        hits=[ln.strip() for ln in text.splitlines() if d in ln and any(k in ln.upper() for k in ['BLOCKED','缺失','损坏','没有快照','不可','欠账'])]
        blocked.append({'date':d,'evidence':hits[:8],'status':'blocked' if hits else 'not_confirmed'})
    return {'status':'blocked' if any(x['status'] != 'confirmed' for x in blocked) else 'pass','items':blocked,'policy':'缺证据不回填、不用后日页面冒充历史时点'}

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--diagnosis',type=Path,required=True); ap.add_argument('--progress',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(argv)
    r=evaluate(a.diagnosis,a.progress); r['generated_at']=datetime.now().isoformat(timespec='seconds'); a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(r,ensure_ascii=False)); return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
