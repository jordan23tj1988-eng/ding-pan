# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,json,re
from datetime import datetime
from pathlib import Path

def evaluate(root: Path, required=5):
    dates={}
    for p in (root/'releases').glob('*-*'):
        m=re.match(r'(\d{8})-',p.name)
        if not m: continue
        try: manifest=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
        except Exception: continue
        if manifest.get('status')=='pass': dates.setdefault(m.group(1),[]).append({'release':p.name,'manifest':'pass'})
    observed=[]
    for d, entries in sorted(dates.items()):
        receipt=root/'.review_deploy'/f'{d}.json'
        if receipt.is_file():
            try:
                rd=json.loads(receipt.read_text(encoding='utf-8'))
                if rd.get('status')=='pass': observed.append(d)
            except Exception: pass
    return {'status':'pass' if len(observed)>=required else 'blocked','required_days':required,'observed_days':len(observed),'dates':observed,'reason':None if len(observed)>=required else '连续稳定观察尚未达到门槛'}

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--required',type=int,default=5); a=ap.parse_args(argv)
    r=evaluate(a.root,a.required); r['generated_at']=datetime.now().isoformat(timespec='seconds'); a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(r,ensure_ascii=False)); return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
