# -*- coding: utf-8 -*-
"""镜像同步前的敏感预扫: 列出 ding-pan仓库 未提交变更中的可疑文件(凭据/密钥类)。只读。"""
import re, subprocess
from pathlib import Path

REPO = Path(r'D:\股票数据\ding-pan仓库')
PAT = re.compile(rb'(sk-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-|-----BEGIN [A-Z ]*PRIVATE KEY|'
                 rb'(api[_-]?key|secret|passwd|password|token)\s*[=:]\s*["\']?[A-Za-z0-9/\+_\-]{12,})', re.I)
NAME_PAT = re.compile(r'(?i)\.(env|key|pem|p12|pfx)$|credential|secret|passwd|token')

st = subprocess.run(['git', 'status', '--porcelain', '-uall'], cwd=REPO, capture_output=True, text=True,
                    encoding='utf-8', errors='replace').stdout.splitlines()
files = [l[3:].strip().strip('"') for l in st if l.strip()]
print('变更条目数:', len(files))
name_hits = [f for f in files if NAME_PAT.search(f)]
print('文件名可疑:', name_hits[:20])
content_hits = []
for rel in files:
    p = REPO / rel
    if not p.is_file() or p.stat().st_size > 8_000_000:
        continue
    try:
        b = p.read_bytes()
    except OSError:
        continue
    m = PAT.search(b)
    if m:
        content_hits.append((rel, m.group(0)[:60].decode('utf-8', 'replace')))
print('内容命中可疑模式文件数:', len(content_hits))
for rel, g in content_hits[:25]:
    print('  ', rel, '|', g)
