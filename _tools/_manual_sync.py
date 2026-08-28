# -*- coding: utf-8 -*-
"""复刻 同步到GitHub.bat 三步镜像 (Python 版, 绕开 git-bash/MSYS robocopy 坑)
1) /MIR: D:\股票数据\市场数据 -> REPO\市场数据  (删目标多余)
2) /E  : D:\股票数据\市场数据\复盘\盯盘台 -> REPO 根 (不删多余)
3) /E  : D:\股票数据\同步GitHub\_extras -> REPO 根 (不删多余)
排除: __pycache__/.git/*.pyc; 盯盘台->根 额外排除 push-to-github.bat
"""
import os, shutil, sys, time

REPO = r"D:\股票数据\ding-pan仓库"
SRC_MD = r"D:\股票数据\市场数据"
SRC_DP = os.path.join(SRC_MD, "复盘", "盯盘台")
SRC_EX = r"D:\股票数据\同步GitHub\_extras"
EXCL_DIRS = ("__pycache__", ".git")
EXCL_SUFFIX = (".pyc",)

def should_copy(s, t):
    if not os.path.exists(t):
        return True
    if os.path.getsize(s) != os.path.getsize(t):
        return True
    if os.path.getmtime(s) > os.path.getmtime(t) + 2:
        return True
    return False

def walk_copy(src, dst, delete_extra=False):
    """复制新增/更新; delete_extra=True 时删除目标多余(镜像语义)"""
    n_copy = n_del = 0
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dirs[:] = [d for d in dirs if d not in EXCL_DIRS]
        tgt = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in files:
            if os.path.splitext(f)[1] in EXCL_SUFFIX:
                continue
            s, t = os.path.join(root, f), os.path.join(tgt, f)
            if should_copy(s, t):
                shutil.copy2(s, t)
                n_copy += 1
    if delete_extra:
        for root, dirs, files in os.walk(dst, topdown=False):
            rel = os.path.relpath(root, dst)
            dirs[:] = [d for d in dirs if d not in EXCL_DIRS]
            sroot = src if rel == "." else os.path.join(src, rel)
            for f in files:
                if os.path.splitext(f)[1] in EXCL_SUFFIX:
                    continue
                if not os.path.exists(os.path.join(sroot, f)):
                    os.remove(os.path.join(root, f)); n_del += 1
            for d in dirs:
                p = os.path.join(root, d)
                if not os.path.exists(os.path.join(sroot, d)):
                    try: os.rmdir(p); n_del += 1
                    except OSError: pass
    return n_copy, n_del

t0 = time.time()
# 1) 市场数据 -> REPO\市场数据 (/MIR)
n1, d1 = walk_copy(SRC_MD, os.path.join(REPO, "市场数据"), delete_extra=True)
# 2) 盯盘台 -> REPO 根 (/E; 额外排除 push-to-github.bat)
for root, dirs, files in os.walk(SRC_DP):
    rel = os.path.relpath(root, SRC_DP)
    dirs[:] = [d for d in dirs if d not in EXCL_DIRS]
    tgt = REPO if rel == "." else os.path.join(REPO, rel)
    os.makedirs(tgt, exist_ok=True)
    for f in files:
        if os.path.splitext(f)[1] in EXCL_SUFFIX or f == "push-to-github.bat":
            continue
        s, t = os.path.join(root, f), os.path.join(tgt, f)
        if should_copy(s, t):
            shutil.copy2(s, t); n1 += 1
# 3) _extras -> REPO 根 (/E)
n3, d3 = walk_copy(SRC_EX, REPO, delete_extra=False)
print(f"复制 {n1+n3} (市场数据/盯盘台 {n1} + extras {n3}) | 删除 {d1+d3} | 耗时 {time.time()-t0:.1f}s")
