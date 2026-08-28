# -*- coding: utf-8 -*-
"""生成 中报预增成色判定_20260826.json —— logic路对雷达A共振池186只逐只三档复核。
口径(可机械复现): 见输出文件 '口径' 字段。"""
import json, io, sys, os, csv
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'; X = os.path.join(B, '_学习'); D = '20260826'
R = json.load(open(os.path.join(X, '中报预增雷达_%s.json' % D), 'r', encoding='utf-8'))
A = R['A共振池(重要度排序)']
zt = {r['代码'] for r in csv.DictReader(open(os.path.join(B, D, 'zt_pool.csv'), 'r', encoding='utf-8-sig'))}

NONREC = ['投资收益','资产处置','股权转让','公允价值','政府补助','债务重组','联营','合营','理财',
          '税收返还','拆迁','补偿款','非经常','出售子公司','转让子公司','退税','减值冲回','诉讼',
          '债务豁免','重组收益','处置收益']
MAIN = ['销量','产量','产销','订单','出货','交付','产能','价格上涨','量价','需求增长','营业收入增长',
        '收入增长','毛利','放量','满产','中标','新增装机','销售增长','市场份额','降本增效','客户拓展',
        '量增','价格同比上涨','开工率','销售规模','营收增长','订单增长','排产','销售收入增长',
        '主营业务收入','量价齐升','价格中枢','产品结构','成本管控','产销量']

# 改归类规则(保守: 仅在主类关键词与原因/概念文本明确冲突时改)
IND = {
    '铜': '有色/工业金属类', '铝': '有色/工业金属类', '锌': '有色/工业金属类',
    '镍': '有色/工业金属类', '钼': '有色/工业金属类', '锆': '有色/新材料类',
    '稀土': '有色/稀土磁材类', '磁材': '有色/稀土磁材类',
}
def reclass(e):
    zl = e.get('主类') or ''; txt = (e.get('原因') or '') + ' ' + ' '.join(e.get('概念板块') or []) + e.get('名称', '')
    if zl == '有色/贵金属类' and not any(w in txt for w in ['黄金', '白银', '金价', '贵金属', '黄金珠宝']):
        for w, t in IND.items():
            if w in txt and t != zl:
                return t, '主类"有色/贵金属类"但原因/概念/名称无黄金白银词、含"%s"=归类污染' % w
    if zl == '锂电/固态电池类' and not any(w in txt for w in ['锂', '电池', '正极', '负极', '隔膜', '电解液', '储能']):
        if any(w in txt for w in ['风电', '光伏发电', '发电量', '新能源发电', '上网电价']):
            return '电力/新能源发电类', '主类"锂电/固态电池类"但文本无锂电环节词、含发电运营词=归类污染'
    return None, None

verd = {}; cnt = Counter(); rec_n = 0; samples = []
for e in A:
    c = str(e['代码']).zfill(6); txt = e.get('原因') or ''
    nr = [w for w in NONREC if w in txt]; mn = [w for w in MAIN if w in txt]
    r250 = e.get('r250'); imp = e.get('重要度分')
    if nr and not mn:
        g = 'C'; dep = '原因文本仅命中非经常性词(%s)、无主业量价词=业绩非主业驱动' % ','.join(nr[:3])
    elif mn:
        if r250 is not None and r250 >= 100:
            g = 'B'; dep = '主业量价词(%s)成立但r250=%.1f%%≥100%%=位置已被定价、预期差消失' % (','.join(mn[:3]), r250)
        else:
            g = 'A'; dep = '主业量价兑现词(%s)+r250=%s%%未透支=题材业务即业绩来源' % (','.join(mn[:3]), r250)
            if nr:
                dep += ';含非经常项(%s)幅度打折' % ','.join(nr[:2])
    else:
        g = 'B'; dep = '原因文本无主业量价可核动因(仅概念tag共振/扭亏未给量价)=概念蹭'
    rc, rr = reclass(e)
    item = {'档': g, '依据': dep + ';重要度分%s;当日涨停=%s' % (imp, '是' if c in zt else '否')}
    if rc:
        item['改归类'] = rc; item['改归类依据'] = rr; rec_n += 1
    verd[c] = item; cnt[g] += 1
    if len(samples) < 8: samples.append((c, e['名称'], g, dep[:70]))

out = {
    '日期': D, '路': 'logic', '来源': '产业逻辑命门',
    '对象': '中报预增雷达_%s.json A共振池(重要度排序) 全量%d只' % (D, len(A)),
    '口径': ('规则化三档复核(可机械复现,非逐条手写): C=原因文本仅命中非经常性词库且无主业量价词; '
           'A=命中主业量价词库且r250<100%; B=命中量价但r250≥100%(位置已定价)或两库均未命中(仅概念tag共振)。'
           '词库与代码见 _tmp_logic_grade2.py。雷达原成色来源=自动初判(186/186),无人工复核、无双源交叉字段,'
           '故本判定=logic路单路复核,不宣称双源。改归类仅在主类关键词与原因/概念/名称明确冲突时给出。'),
    '统计': {'A': cnt['A'], 'B': cnt['B'], 'C': cnt['C'], '改归类只数': rec_n,
             '池内当日涨停只数': len([c for c in verd if c in zt])},
    '判定': verd,
}
p = os.path.join(X, '中报预增成色判定_%s.json' % D)
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('写出', p, '判定n=', len(verd))
print('分布', dict(cnt), '改归类', rec_n)
print('样例:')
for s in samples: print('  ', s)
print('改归类明细:')
for c, v in verd.items():
    if '改归类' in v:
        nm = [e['名称'] for e in A if str(e['代码']).zfill(6) == c][0]
        print('  ', c, nm, '->', v['改归类'], '|', v['改归类依据'][:60])
