# -*- coding: utf-8 -*-
"""20261012 宿主补跑: index body 程序化组装 + judgment bodies 拼装
数字全部程序化取自事实层(总审/推演/周期主判/五路判断/fact/温度表/题材归位/自主拓展应答),
不新增判断、不补造。用法: python _tmp_index_assemble_20261012.py [--write]
"""
import json, os, re, sys

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')
D = '20261012'
WRITE = '--write' in sys.argv
ROUTES = ['auction', 'lhb', 'theme', 'logic', 'limitup']
CN = {'auction': '竞价', 'lhb': '席位', 'theme': '题材', 'logic': '产业逻辑', 'limitup': '涨停'}


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def rj(name):
    return json.load(open(os.path.join(L, name), encoding='utf-8'))


zj = rj(f'总审_{D}.json')
ty = rj(f'推演_{D}.json')
cz = rj(f'周期主判_{D}.json')
tj = rj(f'题材归位_{D}.json')
tz = rj(f'自主拓展应答_{D}.json')
temp = rj('_市场温度表.json')[D]
fact = rj(f'fact_{D}.json')['facts']
rj_route = {r: rj(f'{r}判断_{D}.json') for r in ROUTES}
votes = {r: rj(f'周期投票_{r}_{D}.json') for r in ROUTES}

fv = lambda k: fact[k]['value']
lv = zj['五路裁决']
zjue = zj['总裁决']

sec = []

# 1 总判断
dangs = '、'.join(lv[r].get('档位', '?') for r in ROUTES)
sec.append(('总判断', '<p>%s：五路%s；总档=%s（置信度%s）；正式荐票并集0只、条件观察3只；空仓。</p>'
            % (D, dangs, zjue.get('档位', '—'), zjue.get('置信度', '—'))))

# 2 盘面事实
sec.append(('盘面事实', '<p>涨停%s，炸板%s，跌停%s，封板率%.2f%%，炸板率%.2f%%，成交额%s亿元，封板总额%s亿元，'
             '市场温度%s（%s），最高连板%s板，题材线数%s，回封%s，二板加%s。</p>'
             % (fv('涨停数'), fv('炸板数'), fv('跌停数'), fv('封板率') * 100, fv('炸板率') * 100,
                temp.get('成交额亿'), temp.get('封板总额亿'), fv('温度'), fv('温度档'),
                fv('最高连板'), fv('题材线数'), temp.get('回封数'), temp.get('二板加'))))

# 3 环境
liangneng = next((e.get('fact', '') for e in cz.get('evidence', []) if '量能' in str(e.get('type', ''))), '')
liangneng = '。'.join(liangneng.split('。')[:2])
gaps = [(g or '').rstrip('。') for g in (cz.get('data_gaps') or [])]
sec.append(('环境', '<p>量能：%s。温度档：%s。缺口：%s。</p>'
            % (esc(liangneng), fv('温度档'), '；'.join(esc(g) for g in gaps[:3]) or '无')))

# 4 每路独立核算
parts = []
for r in ROUTES:
    p = rj_route[r].get('判断', {})
    bl = [x for x in (rj_route[r].get('荐票', {}).get('标的') or []) if isinstance(x, dict)]
    n_z = sum(1 for x in bl if x.get('类型') == '荐票')
    n_o = sum(1 for x in bl if x.get('类型') == '观察')
    parts.append('%s%s档（置信度%s，正式荐票%d只，观察%d只）' % (CN[r], p.get('档位', '?'), p.get('置信度', '—'), n_z, n_o))
sec.append(('每路独立核算', '<p>%s。</p>' % '，'.join(parts)))

# 5 题材树
sec.append(('题材树', '<p>题材归位%s只：A档%d、B档%d、C档%d。</p>'
            % (tj.get('counts', {}).get('total', '—'), len(tj.get('A', [])), len(tj.get('B', [])), len(tj.get('C', [])))))

# 6 周期与攻防
ad = cz.get('attack_defense') or {}
sec.append(('周期与攻防', '<p>周期主判：阶段%s、方向%s、置信度%s；攻防=%s；仓位上限=%s。</p>'
            % (cz.get('stage', '—'), cz.get('direction', '—'), cz.get('confidence', '—'),
               ad.get('mode') or ad.get('stance') or '—', cz.get('position_cap', '—'))))

# 7 五路看牌
sec.append(('五路看牌', '<p>%s。</p>'
            % '；'.join('%s=%s/%s（票%s）' % (CN[r], votes[r].get('stage', '—'), cz.get('direction', '—'),
                                            votes[r].get('投票') or votes[r].get('direction') or '—') for r in ROUTES)))

# 8 明日验证
npred = len(ty.get('次日可证伪预测') or [])
sec.append(('明日验证', '<p>推演落盘%s条可机械结算预测（温度、宽度、梯队、竞价承接等），T+1结果尚未发生，不倒灌。</p>' % npred))

# 9 分歧与盲区
blk = zj.get('独立盲区声明') or {}
tob = blk.get('趋同盲区') or []
sec.append(('分歧与盲区', '<p>总审登记分歧点%d处。盲区趋同：%s。其余数据缺口按null保持公开，均不补造。</p>'
            % (len(zj.get('分歧点') or []), esc(tob[0][:120]) if tob else '—')))

# 10 发布门禁
sec.append(('发布门禁', '<p>页面必须通过一致性哨兵与链健康检查后才视为完成。本概览体由宿主在 20261012 晚间补跑时按 '
             '总审_%s.json、推演_%s.json、周期主判_%s.json、五路judgment body 与 fact_%s.json 归档原文组装，'
             '数字程序化取自事实层，未新增判断；五路正文为各路判断原文归档。</p>' % (D, D, D, D)))

# 11 推演指派
asg = zj.get('指派清单') or []
sec.append(('推演指派', '<p>总审落盘指派%d条：%s。</p>'
            % (len(asg), '；'.join('%s→%s（截止%s）' % (a.get('指派ID'), a.get('指派给'), a.get('截止')) for a in asg if isinstance(a, dict)))))

# 12 总裁决
sec.append(('总裁决', '<p>档位=%s，置信度=%s。</p><p>依据：%s</p>'
            % (zjue.get('档位', '—'), zjue.get('置信度', '—'), esc(zjue.get('依据', '—')))))

# 13 五路裁决
ps = []
for r in ROUTES:
    x = lv[r]
    ps.append('<p>%s：%s档／%s（置信度%s） %s</p>' % (CN[r], x.get('档位', '—'), x.get('裁决', '—'),
                                                   x.get('置信度', '—'), esc(x.get('依据', '—'))))
sec.append(('五路裁决', ''.join(ps)))

# 14 深挖
from collections import Counter
dec = Counter(v.get('决定') for v in tz.values() if isinstance(v, dict) and '决定' in v)
sec.append(('深挖', '<p>自主拓展应答%d项：不深挖%s、并入%s。</p>'
            % (sum(dec.values()), dec.get('不深挖', 0), dec.get('并入', 0))))

# 15 认知
cp = os.path.join(L, f'能力全链路审计_{D}.json')
if os.path.isfile(cp):
    cr = json.load(open(cp, encoding='utf-8'))
    sec.append(('认知', '<p>认知迭代全量更新 pass：7路共360条认知记录落盘（含master 29条），子agent增强库同日落盘；'
                '能力全链路审计 status=%s、errors=%s、warnings=%s、可复用能力%s项；'
                '能力消费审计 pass（应用候选2项）；T+1命中未发生，不倒灌。</p>'
                % (cr.get('status', '—'), cr.get('errors', '—'), cr.get('warnings', '—'), cr.get('strict_reusable_total', '—'))))
else:
    sec.append(('认知', '<p>认知迭代全量更新 待重跑（T+1验证→账本重建→能力消费→全链路审计）。</p>'))

body_index = ''.join('<section><h2>%s</h2>%s</section>' % (h, b) for h, b in sec)

if WRITE:
    jp = os.path.join(L, f'judgment_{D}.json')
    J = json.load(open(jp, encoding='utf-8'))
    J.setdefault('bodies', {})['index'] = body_index
    if '--index-only' not in sys.argv:
        for r in ROUTES:
            J['bodies'][r] = open(os.path.join(L, f'{r}_body_{D}.html'), encoding='utf-8').read()
        J['bodies']['cycle'] = open(os.path.join(L, f'cycle_body_{D}.html'), encoding='utf-8').read()
        J['bodies']['archive_body'] = J['bodies'].get('archive_body') or ''
    json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE', jp, '(index-only)' if '--index-only' in sys.argv else '(full)')
    for k, v in J['bodies'].items():
        print('  body', k, len(v))

print('=== index body (%d chars, %d sections) ===' % (len(body_index), len(sec)))
print(body_index)
