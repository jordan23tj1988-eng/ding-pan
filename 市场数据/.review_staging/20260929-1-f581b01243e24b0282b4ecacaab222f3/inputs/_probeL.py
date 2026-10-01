import glob, os, json, re, time
from pathlib import Path
for f in sorted(glob.glob('_学习/*body_202609*.html')):
    print(os.path.getsize(f), time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(f))), f)
print('--- 29 台账 files:')
for f in sorted(glob.glob('_学习/*台账*') + glob.glob('_学习/*归位*')):
    print(os.path.getsize(f), time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(f))), f)
print('--- judgment mtimes:')
for f in ['_学习/judgment_20260929.json', '_学习/judgment_20260929.json.bak_force_cycle_20260930', '涨停复盘台账.py']:
    print(f, time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(f))))
