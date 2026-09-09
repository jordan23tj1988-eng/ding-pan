# -*- coding: utf-8 -*-
"""P1/P2 capability gate: producer + dated real evidence, fail closed."""
from __future__ import annotations
import argparse,json,re
from datetime import datetime
from pathlib import Path

CAPABILITIES={
 'risk_calendar':{'label':'风险日历','producers':['风险日历.py'],'evidence':'_学习/风险日历_{d}.json','hard':True},
 'auction_cancel_diff':{'label':'竞价撤单差分','producers':['竞价撤单差分.py'],'evidence':'_学习/竞价撤单差分_{d}.json','hard':True},
 'open_verification':{'label':'开盘验证维','producers':['开盘验证维.py'],'evidence':'_学习/开盘验证维_{d}.json','hard':True},
 'intraday_temperature_curve':{'label':'日内温度曲线','producers':['日内温度曲线.py'],'evidence':'_学习/日内温度曲线_{d}.json','hard':True},
 'intraday_rotation_graph':{'label':'日内轮动图谱','producers':['日内轮动图谱.py'],'evidence':'_学习/日内轮动图谱_{d}.json','hard':True},
 'theme_relocation':{'label':'题材归位','producers':['题材归位.py'],'evidence':'_学习/题材归位门禁_{d}.json','hard':True},
 'cognition_pack':{'label':'认知库打包/蒸馏','producers':['认知库打包.py','_认知库蒸馏_五路.py','review_learning.py'],'evidence':None,'hard':False},
 'playbook':{'label':'playbook生成','producers':['playbook生成.py'],'evidence':'盘中/{d}/playbook.json','hard':False},
}

def _read(path):
 try:return json.loads(path.read_text(encoding='utf-8-sig'))
 except (OSError,ValueError,TypeError):return None

def check(root:Path,d:str)->dict:
 rows=[]
 for key,s in CAPABILITIES.items():
  producers=[p for p in s['producers'] if (root/p).is_file()]
  ep=s['evidence'].format(d=d) if s['evidence'] else None; ev=_read(root/ep) if ep else None
  evidence_ok=isinstance(ev,dict) and ev.get('date')==d and ev.get('status')=='pass'
  if len(producers)<len(s['producers']): status='missing_producer' if not producers else 'partial_producer'
  elif ep and not (root/ep).is_file(): status='installed_no_evidence'
  elif ep and not evidence_ok: status='evidence_not_pass'
  else: status='available'
  rows.append({'key':key,'label':s['label'],'hard':s['hard'],'status':status,'producers':producers,'evidence':ep,'evidence_status':ev.get('status') if isinstance(ev,dict) else None})
 hard_missing=[x['key'] for x in rows if x['hard'] and x['status']!='available']
 return {'schema_version':2,'date':d,'generated_at':datetime.now().isoformat(timespec='seconds'),'status':'pass' if not hard_missing else 'fail','hard_missing':hard_missing,'capabilities':rows,'policy':'只有生产者齐全且本日证据status=pass才算available；缺数据保持fail-closed'}

def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('date');ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);ap.add_argument('--out',type=Path);a=ap.parse_args(argv)
 if not re.fullmatch(r'\d{8}',a.date):ap.error('date must be YYYYMMDD')
 r=check(a.root.resolve(),a.date); out=a.out or a.root/'_学习'/f'p1_p2_capability_gate_{a.date}.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
