"""TEST ONLY: read-only integration of the real leading-card producer."""
from pathlib import Path
import hashlib,json,shutil
import review_pages as api
ROOT=Path(__file__).resolve().parents[1]
D='20260904'
def test_regenerate_lights_without_overwriting_input_artifacts(tmp_path, capsys):
 learn=tmp_path/'_学习';learn.mkdir()
 shutil.copy2(ROOT/'情绪先行指标.py',tmp_path/'情绪先行指标.py')
 (learn/'_市场温度表.json').write_text(json.dumps({D:{'温度':13.4,'五级':'TEST'}}),encoding='utf-8')
 rows={d:{'连板负溢价率%':None,'连板等权溢价%':None,'连板数量':0,'触发器':[]} for d in ['20260902','20260903',D]}
 (learn/'_情绪先行指标.json').write_text(json.dumps(rows),encoding='utf-8')
 (learn/f'先行指标灯_{D}.html').write_text('TEST_ONLY_OLD_null',encoding='utf-8')
 before={str(p.relative_to(tmp_path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob('*') if p.is_file()}
 html,paths=api._leading_lights(tmp_path,D)
 assert capsys.readouterr().out==''  # Producer chatter must not corrupt publish CLI JSON.
 assert '冰点进攻窗·触发' in api._Tree(html).root.text()
 assert '洗出反弹窗·—' in html and 'null' not in html
 assert {p.name for p in paths}=={'_情绪先行指标.json','_市场温度表.json','情绪先行指标.py'}
 after={str(p.relative_to(tmp_path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob('*') if p.is_file()}
 assert after==before
