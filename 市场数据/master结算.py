# -*- coding: utf-8 -*-
"""master结算.py {上一日d} —— Master 线索跟踪/指派清单/认知迭代 的 T+1 结算对账。

★定位(P2, 2026-08-15 总审升级Master): 傍晚场跑(Master 下一轮总审前)。
  机械化账本管理 = ①指派响应查证(读五路body"承接Master指派[ID]"响应) ②线索/认知状态流转对账(时间到期标记)。
  ★判定条件的最终判断由 Master 下一轮总审做(自然语言判定, 非本脚本硬编码)。
★铁律: 零编造, 读不到标 null; 只做账本管理, 不替 Master 下判断。
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


def main(dprev):
    zj = _load('总审_%s.json' % dprev)
    if not zj:
        print('无总审_%s.json, 跳过' % dprev)
        return
    tracks = zj.get('线索跟踪') or []
    assigns = zj.get('指派清单') or []
    cog = zj.get('认知迭代') or []
    if not (tracks or assigns or cog):
        print('总审无 Master 4字段(旧数据), 跳过')
        return

    # ① 指派响应查证(机械化): ★2026-08-17 修正时序——总审第7步晚于五路第6步生成指派,
    #    dprev当天五路不可能承接, 须按指派"截止"日查对应 judgment_{截止日}.json bodies
    #    (8/17 五条指派截止=20260818复盘场 → 查 judgment_20260818.json)
    assign_rows = []
    for a in assigns:
        if not isinstance(a, dict):
            continue
        aid = str(a.get('指派ID', '—'))
        cut = _cut_date(a, dprev)
        jf_cut = _load('judgment_%s.json' % cut)
        bodies_cut = (jf_cut or {}).get('bodies', {})
        resp = check_assign_response(bodies_cut, aid)
        new_status = '承接中' if resp else (a.get('状态', '待承接'))
        assign_rows.append(dict(
            指派ID=aid, 指派给=a.get('指派给', '—'), 深挖任务=a.get('深挖任务', '—'),
            原状态=a.get('状态', '待承接'), 响应路=resp, 结算状态=new_status,
            截止=a.get('截止', '—'), 查证日=cut))

    # ② 线索/认知状态流转对账(账本管理, 判定条件最终判断交 Master 下一轮)
    track_rows = [dict(线索ID=t.get('线索ID', '—'), 来源路=t.get('来源路', '—'),
                       内容=t.get('内容', '—'), 原状态=t.get('状态', '待验证'),
                       判定条件=t.get('判定条件', '—'), 下次验证点=t.get('下次验证点', '—'),
                       结算状态=t.get('状态', '待验证')) for t in tracks if isinstance(t, dict)]
    cog_rows = [dict(认知点=c.get('认知点', '—'), 依据=c.get('依据', '—'),
                     可证伪条件=c.get('可证伪条件', '—'), 结算状态='待验证') for c in cog if isinstance(c, dict)]

    out = dict(结算日=dprev, 指派=assign_rows, 线索=track_rows, 认知=cog_rows)
    # 写对账单
    with open(os.path.join(L, '_master结算.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(out, ensure_ascii=False) + '\n')

    n_done = sum(1 for r in assign_rows if r['响应路'])
    print('master结算 %s: 指派 %d(已承接 %d) / 线索 %d / 认知 %d → _master结算.jsonl'
          % (dprev, len(assign_rows), n_done, len(track_rows), len(cog_rows)))
    for r in assign_rows:
        print('  [指派%s] %s → %s %s' % (r['指派ID'], r['指派给'],
                                          ('已承接(%s)' % r['响应路']) if r['响应路'] else '未承接',
                                          r['深挖任务'][:30]))


if __name__ == '__main__':
    main(sys.argv[1])
