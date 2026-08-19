# -*- coding: utf-8 -*-
"""文件指纹检查 —— Hermes 与 Claude Code 互相认识改动的机器层(2026-08-12 用户拍板)

用法:
  python _协作/检查改动.py check   # 开工前: 比对快照, 报告自上次以来被改/新增/删除的文件
  python _协作/检查改动.py update  # 收工后: 更新指纹快照

被监控文件: 生产关键脚本 + 当日数据真源 + 页面产物 + 治理文件。
任何一方改动后, 对方开工 check 即见 —— 先理解对方改动, 再动手, 不静默覆盖。
"""
import os, json, hashlib, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 市场数据/
FP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '文件指纹.json')

# 关键文件清单(改这里=双方约定监控范围; 用 glob 相对 ROOT)
WATCH = [
    # 生产脚本(生成/渲染/训练/荐票/结算/哨兵/回归)
    '生成盯盘台.py', 'module_render_limitup.py', '生成复盘HTML.py',
    '涨停质量训练.py', '涨停质量荐票.py', '质量荐票结算.py',
    'limitup数据核对.py', '回归_链路.py', '复盘一致性哨兵.py',
    # 当日数据真源(_学习 下核心 json; 用 glob 匹配当日文件, 避免日期写死次日失效)
    '_学习/judgment_*.json', '_学习/题材归位_*.json',
    '_学习/_市场温度表.json', '_学习/_ths_zt_pool.json',
    '_学习/_涨停质量库.json', '_学习/涨停质量荐票_*.json',
    # 页面产物
    '复盘/盯盘台/limitup.html',
    # 治理文件(文件指纹.json 不监控自身——update 时必然变化, 无意义)
    '_变更总账.md', '_协作/改动声明.py', '_协作/检查改动.py',
]

def _sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:16]

def _scan():
    out = {}
    for rel in WATCH:
        if '*' in rel or '?' in rel:
            # glob 模式: 监控匹配的**最新**文件(judgment_*.json 取最新日期)
            import glob as _g
            hits = sorted(_g.glob(os.path.join(ROOT, rel)))
            if hits:
                out[rel] = _sha(hits[-1])  # 最新一个
            else:
                out[rel] = None
        else:
            p = os.path.join(ROOT, rel)
            if os.path.isfile(p):
                out[rel] = _sha(p)
            else:
                out[rel] = None  # 文件缺失也记录
    return out

def check():
    now = _scan()
    if not os.path.isfile(FP):
        print('首次运行: 无指纹快照, 已生成基线(先 update 一次再正式用)')
        json.dump({'ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'finger': now},
                  open(FP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return 0
    old = json.load(open(FP, encoding='utf-8'))['finger']
    changed, added, deleted = [], [], []
    for k, v in now.items():
        if k not in old:
            added.append(k)
        elif old[k] != v:
            changed.append(k)
    for k in old:
        if k not in now:
            deleted.append(k)
    print('=== 自上次指纹(%s)以来 ===' % json.load(open(FP, encoding='utf-8')).get('ts', '?'))
    if not (changed or added or deleted):
        print('  ✅ 无变化')
        return 0
    for k in changed: print('  ✏️  修改: %s' % k)
    for k in added:   print('  ➕ 新增: %s' % k)
    for k in deleted: print('  🗑  删除: %s' % k)
    print('→ 这些文件可能被对方改过: 先 git/变更总账/改动声明 查谁改的、改了什么, 再动手')
    return 1

def update():
    now = _scan()
    json.dump({'ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'finger': now},
              open(FP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('指纹已更新(%d 文件)' % len(now))

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'check':
        sys.exit(check())
    elif cmd == 'update':
        update()
    else:
        print(__doc__)
        sys.exit(1)
