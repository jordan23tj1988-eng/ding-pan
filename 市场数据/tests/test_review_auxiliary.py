from pathlib import Path
import hashlib,importlib.util
ROOT=Path(__file__).resolve().parents[1]
def test_auxiliary_preserves_bodies_and_rewrites_asset_links(tmp_path):
 p=ROOT/'review_auxiliary.py';assert p.exists()
 spec=importlib.util.spec_from_file_location('aux',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 source=ROOT/'复盘/盯盘台';before={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['intraday.html','history.html']}
 result=m.build_auxiliary(source,tmp_path,'http://127.0.0.1:8899/盯盘台/')
 assert result['status']=='pass'
 for n in before:
  assert hashlib.sha256((source/n).read_bytes()).hexdigest()==before[n]
  original=(source/n).read_text(encoding='utf-8');current=(tmp_path/n).read_text(encoding='utf-8')
  assert m.body_text(original)==m.body_text(current)
  assert m.local_missing(tmp_path,n)==[]
 assert 'overflow-x:auto' in (tmp_path/'intraday.html').read_text(encoding='utf-8')
