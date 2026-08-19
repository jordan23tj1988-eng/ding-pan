# -*- coding: utf-8 -*-
"""哨兵 C4/C5 周末口径修复补丁(整读整写, 防挂载盘截断)。
C4: 期望日期从"今天 d"改为"最后交易日"(周末/盘前 bars 只到最近交易日)。
C5: dprev 荐票的 T+1 尚未到期(>最后交易日)时跳过(结算未到期非欠账)。
"""
import sys
p = r"D:\股票数据\市场数据\复盘一致性哨兵.py"
s = open(p, encoding="utf-8").read()
orig = s

def rep(old, new, tag):
    global s
    n = s.count(old)
    assert n == 1, f"{tag} 匹配数={n}(应=1)"
    s = s.replace(old, new)

# 1. dprev 后插入最后交易日计算
rep("dprev=dprev_dirs[-1] if dprev_dirs else None",
    "dprev=dprev_dirs[-1] if dprev_dirs else None\n"
    "# ★2026-08-16 周末口径: C4/C5 期望日期用最后交易日(bars最多到最近交易日), 非\"今天\"(周末/盘前 d 无交易数据)\n"
    "_LAST_TD=None; _CAL=None\n"
    "try:\n"
    "    sys.path.insert(0, R)\n"
    "    from trading_calendar import load_trading_calendar, next_trading_day\n"
    "    _CAL=load_trading_calendar()\n"
    "    if _CAL: _LAST_TD=_CAL[-1]\n"
    "except Exception:\n"
    "    _CAL=None; _LAST_TD=None\n"
    "_EXPECT_D = d if (_CAL and d in _CAL) else (_LAST_TD or d)",
    "1")

# 2. C4 dd 行
rep("dd=f'{d[:4]}-{d[4:6]}-{d[6:]}';miss=[]",
    "_e=_EXPECT_D; dd=f'{_e[:4]}-{_e[4:6]}-{_e[6:]}';miss=[]", "2")

# 3. C4 ok 判断
rep("ok=last.split(',')[0] in (dd,d)", "ok=last.split(',')[0] in (dd,_e)", "3")

# 4. C4 报错信息
rep("lvl.append(f'C4 关键股{len(need)}只中{len(miss)}只bars未到{d}: {miss[:8]}",
    "lvl.append(f'C4 关键股{len(need)}只中{len(miss)}只bars未到{_e}: {miss[:8]}", "4")

# 5. C5 未到期跳过(最小侵入: 只改 if dprev 条件, 循环体缩进不动)
rep("# ---------- C5 昨日结算有效性 ----------\nif dprev:\n    empty=[]",
    "# ---------- C5 昨日结算有效性 ----------\n"
    "_c5_expired=True\n"
    "if dprev and _CAL and _LAST_TD:\n"
    "    _dn=next_trading_day(dprev,_CAL)\n"
    "    if _dn and _dn>_LAST_TD: _c5_expired=False  # ★2026-08-16: T+1尚未到期(如8/14荐票需8/17数据), 结算未到期, 跳过C5\n"
    "if dprev and _c5_expired:\n"
    "    empty=[]", "5")

open(p, "w", encoding="utf-8").write(s)
print("补丁完成, 改动", len(s)-len(orig), "字符")
