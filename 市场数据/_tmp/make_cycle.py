import json
from pathlib import Path
r=Path(r"D:\股票数据\市场数据"); L=r/'_学习'; d='20260911';
obj={'日期':d,'路':'cycle','判断':{'结论':'冰点防守，五路均偏谨慎。','证据':['温度12.7冰点','五路判断完成，盘中连续tick缺口不可用'],'档位':'C','置信度':0.82,'可证伪条件':'温度回升至40且晋级率与封板质量同步改善','独立盲区声明':'盘中连续tick缺失，三项盘中能力unavailable'},'周期投票':{'direction':'降','理由':'冰点与五路防守结论'},'来源':['五路判断_'+d]}
(L/f'周期主判_{d}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
print('cycle master written')
