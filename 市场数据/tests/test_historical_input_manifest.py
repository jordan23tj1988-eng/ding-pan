"""TEST ONLY source-inventory fixtures; no production or ledger execution."""
import review_publish as pub
ROUTES=('auction','lhb','theme','logic','limitup','master')

def test_freezes_nav_ledgers_and_extra_bars(tmp_path):
    sim=tmp_path/'_学习/_模拟盘';sim.mkdir(parents=True)
    needed=set()
    for route in ROUTES:
        folder=sim/route;folder.mkdir()
        for name in ('净值.json','账本.jsonl'):
            (folder/name).write_text('{}\n',encoding='utf-8')
            needed.add(f'_学习/_模拟盘/{route}/{name}')
    extra=sim/'_bars_extra';extra.mkdir()
    (extra/'603533.csv').write_text('date,close\n20260902,1\n',encoding='utf-8')
    needed.add('_学习/_模拟盘/_bars_extra/603533.csv')
    before={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    names=set(pub.input_files(tmp_path,'20260902'))
    assert needed<=names, sorted(needed-names)
    assert before=={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
