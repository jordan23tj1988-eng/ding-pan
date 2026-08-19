# -*- coding: utf-8 -*-
"""logic_pool.py —— 第四路(产业逻辑)荐票池统一读取 (2026-08-14 方案B, 用户拍板"5b")

契约迁移背景: 逻辑路发出版 7/17 起由 逻辑荐票_{d}.json 迁移为 logic判断_{d}.json
  (SKILL.md 契约: 荐票=dict{结论,标的[]}, 标的中 类型=='荐票' 才是荐票, '观察级(非荐票)' 不是)。
下游三处(逻辑荐票结算.py / 模拟盘引擎.py / module_render_logic.py)统一经本函数读,
修复"下游仍读旧文件名 → 发出版断档、结算漏记、路内池基准缺失"。

零编造: 文件缺失/解析失败 = 返回 ([], None), 由调用方走各自兜底(如实标注, 不补造)。
"""
import os, json

def load_logic_picks(d, L):
    """返回 (picks, src):
      picks = 逻辑路'荐票'类型标的 list[dict], 字段含 代码/名称/类型/理由 (+链条/环节[旧契约] 或 历史对照[新契约]);
      src   = 实际读取的发出版文件名(新契约 logic判断_{d}.json / 旧契约 逻辑荐票_{d}.json), 无文件=None。
    新契约: 荐票.标的[] 过滤 类型=='荐票'; 旧契约: 荐票[] 全量(旧版无观察级, 全为荐票)。"""
    p_new = os.path.join(L, 'logic判断_%s.json' % d)
    if os.path.isfile(p_new):
        try:
            j = json.load(open(p_new, encoding='utf-8'))
            rec = j.get('荐票') or {}
            picks = [t for t in (rec.get('标的') or [])
                     if isinstance(t, dict) and str(t.get('类型', '')).strip() == '荐票']
            return picks, 'logic判断_%s.json' % d
        except Exception:
            pass
    p_old = os.path.join(L, '逻辑荐票_%s.json' % d)
    if os.path.isfile(p_old):
        try:
            j = json.load(open(p_old, encoding='utf-8'))
            picks = j.get('荐票') or []
            if isinstance(picks, dict):
                picks = picks.get('标的') or []
            return picks, '逻辑荐票_%s.json' % d
        except Exception:
            pass
    return [], None
