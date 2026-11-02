# -*- coding: utf-8 -*-
"""trading_calendar.py —— 连续交易日序列(含停机期),源=_bars_cache 日线 date 并集,缓存 _学习/_交易日历.json。
用途:各复盘脚本求"池日下一交易日",防跨断档错配(如停机期 7/16→8/11 曾把 7/16 的溢价 -2.53 错配到 8/11)。
★缓存自动刷新:bars_cache 有比缓存文件更新的数据时重建(新交易日入 bars 后自动跟上)。
"""
import os, json, glob, csv

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")


def load_trading_calendar():
    """返回排序好的交易日列表(YYYYMMDD str);缓存缺失/过期则从 bars_cache 重建。"""
    fp = os.path.join(L, "_交易日历.json")
    cd = os.path.join(L, "_bars_cache")
    cal = None
    if os.path.isfile(fp):
        try:
            cal = json.load(open(fp, encoding="utf-8"))
            if not (isinstance(cal, list) and cal):
                cal = None
        except Exception:
            cal = None
        if cal is not None:
            # 过期判断:bars_cache 最新 mtime 是否晚于缓存 mtime(有新 bar 就重建)
            try:
                newest = max((os.path.getmtime(f) for f in glob.glob(os.path.join(cd, "*.csv"))), default=0)
                if os.path.getmtime(fp) >= newest:
                    return [str(x) for x in cal]
            except Exception:
                pass
    cal = _build(cd)
    if cal:
        try:
            json.dump(cal, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass
    return cal


def _build(cd):
    dates = set()
    for f in glob.glob(os.path.join(cd, "*.csv")):
        try:
            for row in csv.DictReader(open(f, encoding="utf-8", errors="ignore")):
                d = (row.get("date") or "").strip()
                if d:
                    dates.add(d.replace("-", ""))
        except Exception:
            continue
    return sorted(dates)


def next_trading_day(d, cal=None):
    """返回 d(YYYYMMDD) 的紧邻下一交易日;d 不在日历或无下一日则 None。"""
    cal = cal or load_trading_calendar()
    d = str(d)
    if d not in cal:
        return None
    i = cal.index(d)
    return cal[i + 1] if i + 1 < len(cal) else None
