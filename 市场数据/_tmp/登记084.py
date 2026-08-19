# -*- coding: utf-8 -*-
"""append 登记 #084 到变更总账(CRLF 一致)"""
p = r"D:\股票数据\市场数据\_变更总账.md"
entry = (
"\r\n\r\n## #084 复盘一致性哨兵.py C4/C5 周末口径修复 (2026-08-16)\r\n"
"- 动机: 周日/盘前手动跑哨兵时 C4\"关键股bars未到今天\"、C5\"昨日荐票结算缺文件\"误报(实为周末无交易数据、T+1未到期), 非真实数据欠账。\r\n"
"- 改了什么(复盘一致性哨兵.py):\r\n"
"  1. dprev 计算后新增最后交易日加载: import trading_calendar 得 _CAL(交易日序列)/_LAST_TD(最后交易日), _EXPECT_D = d if d在日历 else _LAST_TD(周末/盘前用最后交易日)。\r\n"
"  2. C4 期望日期 dd 由\"今天 d\"改 _EXPECT_D, 报错信息 bars未到{_e}。\r\n"
"  3. C5 新增未到期跳过: dprev 荐票的 T+1(下一交易日)未发生或 > _LAST_TD 时 _c5_expired=False, 跳过 C5 检查(结算未到期非欠账)。\r\n"
"- 验证: py_compile OK; 周末 d=20260816 跑 C4/C5 全消失(仅剩 C8 未登记); 工作日 d=20260814 无回归(仅 C8); 断档日 d=20260813 与备份哨兵对比 C4 结果完全一致(无回归)。\r\n"
"- 级别: 小改(哨兵口径, 只影响周末/盘前行为, 工作日盘后不变)。\r\n"
"- 遗留: 无。\r\n"
)
with open(p, "a", encoding="utf-8", newline="") as f:
    f.write(entry)
print("已追加 #084, 新总行数:")
import subprocess
print(subprocess.run(["wc","-l",p], capture_output=True, text=True).stdout)
