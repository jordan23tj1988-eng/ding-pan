# -*- coding: utf-8 -*-
"""改动声明日志工具 —— Hermes 与 Claude Code 共写工作区的互相认识机制(2026-08-12 用户拍板)

用法:
  python _协作/改动声明.py declare <agent> <files...> --purpose "目的" [--impact "影响面"]
  python _协作/改动声明.py done    <agent> [--verify "验证结果"]
  python _协作/改动声明.py list

规则:
  - 动手前必须 declare(标记"进行中"), 改完必须 done(补验证结果)
  - 开工前先 list, 看到"进行中"声明 = 对方正在改, 先沟通再动手(软锁)
  - 声明日志=_协作/改动声明.jsonl(追加式, 永不清空)
"""
import sys, json, os
from datetime import datetime

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '改动声明.jsonl')

def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def declare(agent, files, purpose, impact):
    rec = {'ts': _now(), 'agent': agent, 'action': 'declare',
           'files': files, 'purpose': purpose, 'impact': impact,
           'status': '进行中'}
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print('[%s] %s 声明改动: %s → %s' % (_now(), agent, ','.join(files), purpose))

def done(agent, verify):
    # ★配对: 把最近一条同 agent 的"进行中"声明标完成(否则软锁永不释放, list永远显示进行中)
    #   2026-08-12 验证发现: done 只追加新记录不配对 → 声明累积成永久进行中
    rows = []
    if os.path.isfile(LOG):
        rows = [json.loads(l) for l in open(LOG, encoding='utf-8') if l.strip()]
    paired = False
    for r in reversed(rows):
        if r.get('agent') == agent and r.get('status') == '进行中':
            r['status'] = '完成'
            r['done_ts'] = _now()
            r['verify'] = verify
            paired = True
            break
    if paired:
        with open(LOG, 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print('[%s] %s 完成改动, 验证: %s (已配对声明)' % (_now(), agent, verify))
    else:
        rec = {'ts': _now(), 'agent': agent, 'action': 'done',
               'verify': verify, 'status': '完成'}
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        print('[%s] %s 完成改动, 验证: %s (无进行中声明,仅记录)' % (_now(), agent, verify))

def listing():
    if not os.path.isfile(LOG):
        print('(无声明记录)')
        return
    rows = [json.loads(l) for l in open(LOG, encoding='utf-8') if l.strip()]
    print('=== 进行中的声明(对方可能正在改, 先沟通) ===')
    for r in rows:
        if r['status'] == '进行中':
            print('  ⏳ [%s] %s 改 %s — %s' % (r['ts'], r['agent'], ','.join(r['files']), r['purpose']))
    print('=== 最近 5 条完成 ===')
    for r in [x for x in rows if x['status'] == '完成'][-5:]:
        print('  ✓ [%s] %s %s' % (r['ts'], r['agent'], r.get('verify', '')))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'declare':
        # declare <agent> <file1,file2> --purpose "..." [--impact "..."]
        agent = sys.argv[2]
        files = sys.argv[3].split(',')
        purpose = impact = ''
        if '--purpose' in sys.argv:
            purpose = sys.argv[sys.argv.index('--purpose') + 1]
        if '--impact' in sys.argv:
            impact = sys.argv[sys.argv.index('--impact') + 1]
        declare(agent, files, purpose, impact)
    elif cmd == 'done':
        agent = sys.argv[2]
        verify = ''
        if '--verify' in sys.argv:
            verify = sys.argv[sys.argv.index('--verify') + 1]
        done(agent, verify)
    elif cmd == 'list':
        listing()
    else:
        print(__doc__); sys.exit(1)
