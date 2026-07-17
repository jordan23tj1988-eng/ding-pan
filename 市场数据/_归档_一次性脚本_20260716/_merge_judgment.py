# -*- coding: utf-8 -*-
import json,os
L="_学习"; d="20260715"
p1=json.load(open("_tmp_bodies_part1.json",encoding="utf-8"))
p2=json.load(open("_tmp_bodies_part2.json",encoding="utf-8"))
p3=json.load(open("_tmp_bodies_part3.json",encoding="utf-8"))
bodies={}; bodies.update(p1); bodies.update(p2); bodies.update(p3)
order=['index','cycle','auction','lhb','theme','logic','limitup']
assert set(bodies)==set(order), set(bodies)
bodies={k:bodies[k] for k in order}
# ticker (组件#16, 支撑口径)
ticker=('<div class="ticker"><div class="in">'
 '<div class="grp">'
 '<span>量能 <b class="a">2.57万亿</b>(弱修·连2日回落)</span>'
 '<span>涨停 <b class="u">71</b> / 跌停 <b class="d">31</b></span>'
 '<span>炸板 <b>21</b>·炸板率 <b>22.8%</b></span>'
 '<span>最高 <b class="u">4板</b>(哈药)</span>'
 '<span>1进2率 <b class="a">13.9%</b>(昨2.5%→回升)</span>'
 '<span>情绪温度 <b class="a">33.4</b>(偏冷)</span>'
 '<span>资金温度 <b class="a">65</b>分位(温·0714口径)</span>'
 '<span>昨停溢价 <b class="mut">null</b>(源不可达)</span>'
 '<span>五路一字牌 医药6/6·AI5/6</span>'
 '<span>三窗 <b class="mut">全未触发</b></span>'
 '<span>周期投票 <b class="a">5:0 平</b>(无复议·一致率100%⚠)</span>'
 '</div>'
 '<div class="grp" aria-hidden="true">'
 '<span>量能 <b class="a">2.57万亿</b>(弱修·连2日回落)</span>'
 '<span>涨停 <b class="u">71</b> / 跌停 <b class="d">31</b></span>'
 '<span>炸板 <b>21</b>·炸板率 <b>22.8%</b></span>'
 '<span>最高 <b class="u">4板</b>(哈药)</span>'
 '<span>1进2率 <b class="a">13.9%</b>(昨2.5%→回升)</span>'
 '<span>情绪温度 <b class="a">33.4</b>(偏冷)</span>'
 '<span>资金温度 <b class="a">65</b>分位(温·0714口径)</span>'
 '<span>昨停溢价 <b class="mut">null</b>(源不可达)</span>'
 '<span>五路一字牌 医药6/6·AI5/6</span>'
 '<span>三窗 <b class="mut">全未触发</b></span>'
 '<span>周期投票 <b class="a">5:0 平</b>(无复议·一致率100%⚠)</span>'
 '</div></div></div>')
archive=('<h2>07-15 涨停复盘存档 · 完整档案</h2>'
 '<p style="font-size:12.5px;line-height:1.7">环境:量能2.57万亿(弱修连2日)、温度33.4偏冷、涨停71/跌停31/炸板21(炸板率22.8%)、最高4板(哈药)、1进2率13.9%(昨2.5%极值回升)。'
 '主线=医药/创新药6/6主流21只(GLP-1/CRO-CXO/IVD/器械多点开花,迪哲BD出海+哈药4板双龙头,【放宽】宽度5→21+320%)但开板占比0.48=宽而不硬,判"发酵Day1未证",身位只做业绩锚。'
 '次线AI算力/半导体5/6(13只,环比-50%退位)、中报预增/困境反转★新线7只(醋酸/尿素/草酸/电力扭亏,业绩底)、重组/跨界(恒尚存储12天11板超高标个股驱动)。资源修复线(油气煤炭)-67%收缩。'
 '质量Top5:昭衍新药17.7%/华盛昌17.5%/天安新材16.5%/爱旭16.1%/云中马16.1%(全命中0规则,偏冷普涨规则榜失效)。'
 '周期投票:主判启动/分歧·平,五路全平一致(0反对无复议,一致率100%回声室警示已记账)。'
 '★数据缺口(诚实记):同日龙虎榜未全publish、实时spot源不可达→昨停溢价/各路执行口径结算/中报预增雷达刷新/质量库重训均标null或用T-1,系环境网络限制非judgment。'
 '模拟盘六账本本周:总+0.35%/席位+1.0%/题材+0.6%/竞价-1.19%/涨停0.0%/产逻-1.66%(基准-0.14%)。</p>')
J={"date":d,"更新label":d,
 "一句话":"占位(通知另出)",
 "bodies":bodies,"archive_body":archive,"ticker":ticker}
json.dump(J,open(os.path.join(L,"judgment_%s.json"%d),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("judgment_%s.json 写入; bodies:"%d,{k:len(v) for k,v in bodies.items()},"archive",len(archive),"ticker",len(ticker))
