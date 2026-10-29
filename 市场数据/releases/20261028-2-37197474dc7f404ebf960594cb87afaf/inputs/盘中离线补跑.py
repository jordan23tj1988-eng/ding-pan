# -*- coding: utf-8 -*-
"""
盘中离线补跑 v2 (2026-08-13 重建) — 数据补跑 watchdog
================================================
原版(腾讯分钟K补跑→replay→结算) 8/11 前后丢失。
本版职责(最小可靠): 检测最近 N 个交易日缺 summary.json 的日期 → 逐个跑市场数据下载.py
  (akshare 主源 + iFinD iwencai 降级臂已在下载脚本内, 全自动)。
腾讯分钟K/replay/结算链: 由复盘 agent 消费数据时处理, 不在此脚本(诚实标注边界)。
用法: python 盘中离线补跑.py --days 8
输出: 有补跑→打印汇总(微信投递); 无候选→静默(exit 0 无输出)。
"""
import os, sys, subprocess, datetime, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据\市场数据"
DL = os.path.join(BASE, "市场数据下载.py")


def trading_days_guess(now, days):
    """最近 N 个工作日(简化: 周一前=周五), 节假日靠市场数据下载.py 自身 8 天探测容错"""
    out = []
    d = now
    while len(out) < days:
        if d.weekday() < 5:
            out.append(d.strftime("%Y%m%d"))
        d -= datetime.timedelta(days=1)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=8)
    args = ap.parse_args()
    candidates = []
    for d in trading_days_guess(datetime.date.today(), args.days):
        if not os.path.exists(os.path.join(BASE, d, "summary.json")):
            candidates.append(d)
    if not candidates:
        sys.exit(0)  # 无候选=静默
    env = dict(os.environ)
    env["PYTHONPATH"] = ""
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        env.pop(k, None)
    py = r"D:\股票数据\.venv312\Scripts\python.exe"
    if not os.path.exists(py):
        py = sys.executable
    results = []
    for d in candidates:
        try:
            r = subprocess.run([py, DL, d], capture_output=True, text=True,
                               timeout=900, env=env, encoding="utf-8", errors="replace")
            tail = (r.stdout or "").strip().splitlines()
            last = tail[-1] if tail else ("exit=%d" % r.returncode)
            results.append("%s: %s" % (d, last))
        except Exception as e:
            results.append("%s: 异常 %s" % (d, str(e)[:100]))
    print("离线补跑完成 %d 日:\n" % len(results) + "\n".join(results))


if __name__ == "__main__":
    main()
