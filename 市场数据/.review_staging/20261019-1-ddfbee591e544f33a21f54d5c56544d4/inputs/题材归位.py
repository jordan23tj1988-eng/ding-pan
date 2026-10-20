# -*- coding: utf-8 -*-
"""题材归位唯一真源校验入口；不凭行业或记忆补写映射。"""
from __future__ import annotations
import argparse
from pathlib import Path
from capability_common import valid_date,load_json,write_json,result

def build(root:Path,d:str):
    valid_date(d); p=root/'_学习'/f'题材归位_{d}.json'; obj=load_json(p,{})
    mp=obj.get('映射') if isinstance(obj,dict) else None; ok=isinstance(mp,dict) and bool(mp)
    bad=[]
    for code,v in (mp or {}).items():
        if not isinstance(v,dict) or not v.get('大方向'): bad.append(str(code))
    status='pass' if ok and not bad else ('partial' if ok else 'unavailable')
    return result('theme_relocation',d,status,[p.relative_to(root).as_posix()] if p.is_file() else [],{'mapped_count':len(mp or {}),'invalid_count':len(bad)},[] if ok and not bad else ['题材归位缺失或存在无大方向映射'], '本入口只核验既有唯一真源；不自动补造题材归属')

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('d');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path);a=p.parse_args(argv);r=build(a.root.resolve(),a.d);write_json(a.out or a.root/'_学习'/f'题材归位门禁_{a.d}.json',r);print(r);return 0 if r['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
