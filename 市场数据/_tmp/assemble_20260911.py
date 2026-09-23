import json
from pathlib import Path
r=Path(r"D:\股票数据\市场数据"); L=r/'_学习'; d='20260911'
routes=['auction','lhb','theme','logic','limitup']
jud=[]
for x in routes:
 p=L/f'{x}判断_{d}.json'; jud.append(json.loads(p.read_text(encoding='utf-8')))
facts=json.loads((L/f'fact_{d}.json').read_text(encoding='utf-8'))
summary={'日期':d,'路':'master','来源':'五路判断汇总+fact_'+d+'.json','判断':{'结论':'冰点防守，五路一致偏谨慎；仅保留观察，不形成进攻仓位。','证据':['温度12.7、最高连板4、涨停40、炸板18、跌停21，均来自fact_'+d+'.json','竞价/席位/题材/逻辑/涨停质量五路均未形成可交易的强共振'],'档位':'C','置信度':0.82,'可证伪条件':'次日温度回升至40以上且连板晋级、封板质量和至少两路荐票同时改善，否则维持防守。','独立盲区声明':'20260911缺少连续盘中tick，开盘验证、日内温度曲线、日内轮动图谱不可用；题材归位全为B档行业兜底，不能当公告催化。'},'荐票':{'结论':'空仓观察','标的':[]},'认知迭代':[],'深挖':{},'指派清单':[],'环境加权依据':'冰点温度与多项硬门禁缺口下，降低进攻权重。'}
(L/f'总审_{d}.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
pred={'日期':d,'次日可证伪预测':[{'预测':'维持冰点防守，接力修复不足','判定条件':'次日温度仍低于25且一进二率低于10%'},{'预测':'瑞尔特4板若无法继续晋级则高度承压','判定条件':'次日未晋级或开盘跌幅超过-5%'},{'预测':'电力/通信/元件分支难形成统一主线','判定条件':'上述至少两行业涨停数未增加且炸板率不降'},{'预测':'竞价高开追涨胜率偏低','判定条件':'竞价池高开5%以上标的次日封板率低于历史基准'},{'预测':'双源强矛盾票继续打折','判定条件':'强矛盾票次日平均收益低于全场涨停均收'}],'来源':['五路判断_'+d,'总审_'+d+'.json','fact_'+d+'.json'],'状态':'可结算'}
(L/f'推演_{d}.json').write_text(json.dumps(pred,ensure_ascii=False,indent=2),encoding='utf-8')
# judgment skeleton for renderer
j={'date':d,'更新label':d,'一句话':'冰点防守，五路判断完成；盘中连续tick缺口如实保留。','ticker':[],'bodies':{x:(L/f'{x}_body_{d}.html').read_text(encoding='utf-8') for x in routes},'archive_body':'<p>20260911补跑：五路判断均完成，盘中tick能力缺口保持unavailable。</p>','master':summary}
(L/f'judgment_{d}.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
print('assembled')
