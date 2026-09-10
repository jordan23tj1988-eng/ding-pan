# -*- coding: utf-8 -*-
"""P2 Master 审计薄适配：d 为审计截至日，不再代表旧的发行日参数。
用法：python -B master结算.py YYYYMMDD --root INPUT_ROOT --out NEW_RUN_ROOT
仅写独立新 run。按原指派截止交易日查证；ID 仅 acknowledged，原判据与证据齐备才 validated。
下面保留旧只读辅助函数供历史代码导入；P2 main/CLI 统一委托 review_learning。
"""
import os, sys, json, glob, re

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')

ROUTES = ['auction', 'lhb', 'theme', 'logic', 'limitup']


def _load(fname):
    p = os.path.join(L, fname)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None


def check_assign_response(bodies, aid):
    """查五路 body 是否出现 '承接Master指派[aid]' 响应。返回响应片段或 None。"""
    for r in ROUTES:
        body = (bodies or {}).get(r) or ''
        m = re.search(r'承接\s*Master\s*指派\s*[\s\S]{0,20}?%s' % re.escape(aid), body)
        if m:
            return r
    return None


def _cut_date(a, dprev):
    """指派截止日: 优先解析 截止 字段(如 '20260818复盘场'→20260818), 否则下一工作日兜底。"""
    import re as _re
    import datetime as _dt
    cut = str(a.get('截止', '') or '')
    m = _re.search(r'(\d{8})', cut)
    if m:
        return m.group(1)
    # 日历回退(日历可能不含未来交易日): 用 datetime 找下一工作日(周一~周五), 节假日由总审截止字段覆盖
    try:
        d0 = _dt.datetime.strptime(str(dprev), '%Y%m%d')
        for _ in range(7):
            d0 += _dt.timedelta(days=1)
            if d0.weekday() < 5:
                return d0.strftime('%Y%m%d')
    except Exception:
        pass
    return dprev


def main(d, *, root, out):
    """P2 只写独立审计；出现 ID 仅 acknowledged，证据与原判据齐备才 validated。"""
    from pathlib import Path
    from review_learning import settle_master
    return settle_master(Path(root), d, Path(out))


if __name__ == '__main__':
    from review_learning import main as learning_main
    raise SystemExit(learning_main(["master", *sys.argv[1:]]))
