# -*- coding: utf-8 -*-
"""重建 20260901 index body：补齐 obs/obs-head/hb/rowE 黄金版组件。"""
import json

D = '20260901'
L = '_学习'

def esc(s):
    return (s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))

z = json.load(open(f'{L}/总审_{D}.json', encoding='utf-8'))
summ = json.load(open(f'{D}/summary.json', encoding='utf-8'))
h = json.load(open(f'{L}/子agent增强/_战绩画像汇总_{D}.json', encoding='utf-8'))

# ---- 六路战绩 ----
w = h['五路']
def rt(route, label):
    tot = (w.get(route) or {}).get('合计') or {}
    return tot
six = [
    ('auction', '竞价auction', rt('auction','竞价')),
    ('lhb', '龙虎榜席位', rt('lhb','席位')),
    ('theme', '主线题材', rt('theme','题材')),
    ('logic', '产业逻辑', rt('logic','产逻')),
    ('limitup', '涨停质量', rt('limitup','质量')),
]
def hb_bars():
    out = []
    for route, label, tot in six:
        n = tot.get('n') or tot.get('样本') or tot.get('胜次数')
        m = tot.get('m') or tot.get('总次数') or tot.get('分母')
        wr = tot.get('胜率')
        ar = tot.get('均收') or tot.get('均涨')
        # 兼容不同字段名
        if wr is None and m and n is not None:
            wr = n/m if m else 0
        arv = ar if ar is not None else 0.0
        try:
            arv = float(arv)
        except Exception:
            arv = 0.0
        wd = min(98, round(abs(arv) * 40))
        cls = 'pos' if arv >= 0 else 'neg'
        hv = 'up' if arv >= 0 else 'dn'
        sign = '+' if arv >= 0 else ''
        pct = (wr*100) if wr is not None else None
        if n is not None and m:
            hs = f'{n}/{m}={pct:.1f}%'
        else:
            hs = '—'
        out.append(
            f'<div class="hb"><span class="hbl">{label}</span>'
            f'<div class="hbt"><i class="{cls}" style="width:{wd}%"></i></div>'
            f'<span class="hbv {hv}">{sign}{arv:.2f}%</span>'
            f'<span class="hbs">{hs}</span></div>'
        )
    out.append(
        '<div class="hb"><span class="hbl">总控master</span>'
        '<div class="hbt"><i class="pos" style="width:0%"></i></div>'
        '<span class="hbv">0成空仓</span>'
        '<span class="hbs">C档72</span></div>'
    )
    return ''.join(out)

# ---- 结论 ----
concl = z.get('结论','')
总裁决 = z.get('总裁决', {})
档位 = 总裁决.get('档位','C')
置信 = 总裁决.get('置信度', 72)
依据 = 总裁决.get('依据','')
昨日验收 = 总裁决.get('昨日战绩验收','')
验证点 = 总裁决.get('次日验证点', [])
环境加权 = 总裁决.get('环境加权依据','')

五路裁决 = z.get('五路裁决', {})
检查四项 = z.get('检查四项', {})
深挖 = z.get('综合深挖', [])
线索 = z.get('线索跟踪', [])
指派 = z.get('指派清单', [])
认知 = z.get('认知迭代', [])
分歧 = z.get('分歧裁决', {})

# ---- 五路裁决 routes ----
route_map = [
    ('auction', '01 / 第一路', '竞价·时机', 'auction.html'),
    ('lhb', '02 / 第二路', '龙虎榜·席位', 'lhb.html'),
    ('theme', '03 / 第三路', '主线·题材', 'theme.html'),
    ('logic', '04 / 第四路', '产业逻辑', 'logic.html'),
    ('limitup', '05 / 第五路', '涨停复盘', 'limitup.html'),
]
def badge(档):
    if 档 == 'A':
        return 's-strong', '采纳·A'
    if 档 == 'B':
        return 's-mid', '保留·B'
    return 's-weak', '采纳·C'

def build_routes():
    out = []
    for route, n, name, href in route_map:
        v = 五路裁决.get(route, {})
        档 = v.get('档位', 'C')
        conf = v.get('置信度') or (v.get('置信度') if isinstance(v, dict) else None)
        # 置信度从依据里取不到就空
        if conf is None:
            conf = ''
        else:
            conf = str(conf)
        bcls, btxt = badge(档)
        依据短 = (v.get('依据') or '')[:60]
        out.append(
            f'<a class="rt" href="{href}"><span class="rtn">{n}</span>'
            f'<span class="rtm">{name}</span><b class="rtt {bcls}">{btxt}</b>'
            f'<span class="rtd">{档}{conf} · {esc(依据短)}</span></a>'
        )
    return ''.join(out)

# ---- 检查四项 cards ----
def build_check4():
    items = []
    items.append(('A档编造检查', (检查四项.get('A档编造') or '')[:240]))
    items.append(('零后视镜检查', (检查四项.get('后视镜') or '')[:240]))
    items.append(('趋同盲区检查', (检查四项.get('趋同盲区') or '')[:240]))
    items.append(('矛盾检查', (检查四项.get('矛盾') or '')[:240]))
    out = []
    for title, txt in items:
        out.append(f'<div class="card"><b>{esc(title)}</b><p class="mut" style="margin:4px 0 0">{esc(txt)}</p></div>')
    return ''.join(out)

# ---- 深挖 cards ----
def build_deep():
    out = []
    for x in 深挖[:3]:
        out.append(f'<div class="card"><b>深挖 {esc(x.get("主题",""))[:50]}</b><p class="mut" style="margin:4px 0 0">{esc(x.get("深挖结论",""))[:220]}</p></div>')
    return ''.join(out)

# ---- 线索 obs ----
def build_obs():
    观察中 = ' · '.join([f'{x.get("线索ID","")}→{x.get("来源路","")}{x.get("内容","")[:45]}' for x in 线索])
    下次 = '20260902收盘'
    return (
        '<div class="obs"><div class="obs-head">'
        f'<span class="obs-nm">线索跟踪 <span class="mut">{len(线索)}条·覆盖五路</span></span>'
        '<span class="obs-pos tag">看板</span></div>'
        f'<div class="obs-watch"><span class="obs-lab">观察中</span>{esc(观察中)}</div>'
        f'<div class="obs-rec"><span class="obs-lab2">下次验证</span>{下次}</div></div>'
    )

# ---- 指派清单 tli ----
def build_assign():
    out = []
    for x in 指派:
        out.append(
            f'<div class="tli"><b>{esc(x.get("指派ID",""))}→{esc(x.get("指派给",""))}</b>'
            f'{esc(x.get("深挖任务",""))[:150]}<span class="mut">·截止{x.get("截止","")}·{x.get("状态","待承接")}</span></div>'
        )
    return ''.join(out)

# ---- 认知迭代 tli ----
def build_cog():
    out = []
    for x in 认知[:4]:
        out.append(
            f'<div class="tli"><b>09-01</b>{esc(x.get("认知点",""))[:150]}。可证伪:{esc(x.get("可证伪条件",""))[:80]}</div>'
        )
    return ''.join(out)

# ---- 组装 ----
# rowA 保留现有 hero/kpi（从 judgment 读取原 rowA 段）
old = json.load(open(f'{L}/judgment_{D}.json', encoding='utf-8'))
old_idx = old['bodies'].get('index','')
rowA_end = old_idx.find('<h2>一 总判断</h2>')
rowA = old_idx[:rowA_end] if rowA_end > 0 else ''

body = rowA + (
    '<h2>一 总判断</h2>\n<div class="rowC">\n'
    f'<div class="card"><b>总裁决 {档位}档·防守 置信{置信}</b><p class="mut" style="margin:4px 0 0">{esc(concl)}</p></div>\n'
    f'<div class="card"><b>昨日战绩验收</b><p class="mut" style="margin:4px 0 0">{esc(昨日验收[:420])}</p></div>\n'
    f'<div class="card"><b>次日验证点(可证伪)</b><p class="mut" style="margin:4px 0 0">'
    + ''.join([f'<p class="mut">{esc(v[:180])}</p>' for v in 验证点[:3]])
    + '</p></div>\n</div>\n'
    '<h2>二 五路裁决</h2>\n<div class="routes">\n'
    + build_routes() + '\n</div>\n'
    '<h2>三 检查四项</h2>\n<div class="rowC">\n'
    + build_check4() + '\n</div>\n'
    '<h2>四 总裁决 · 自主进化</h2>\n<div class="rowE">\n'
    f'<div class="card"><b>六路独立核算 · 战绩画像</b>\n{hb_bars()}\n<p class="mut" style="margin:6px 0 0">{esc(环境加权[:200])}</p></div>\n'
    f'<div class="card"><b>总裁决 {档位}档·防守 置信{置信}</b><p class="mut" style="margin:4px 0 0">{esc(依据[:500])}</p></div>\n'
    '</div>\n'
    '<h2>五 深挖与线索</h2>\n<div class="rowC">\n'
    + build_deep() + '\n</div>\n'
    + build_obs() + '\n'
    '<h2>六 指派清单 · 认知迭代</h2>\n<div class="rowE">\n'
    f'<div class="card"><b>指派清单 · {len(指派)}条新增(每路1条)</b>\n{build_assign()}</div>\n'
    f'<div class="card"><b>我的认知迭代 · 最新</b>\n{build_cog()}</div>\n'
    '</div>'
)

old['bodies']['index'] = body
json.dump(old, open(f'{L}/judgment_{D}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 自检
import re
dopen = len(re.findall(r'<div[\s>]', body))
dclose = len(re.findall(r'</div>', body))
print(f'index body 重建完成 len={len(body)} div开={dopen} div闭={dclose} 平衡={dopen==dclose}')
print('obs=', body.count('class="obs"'), 'obs-head=', body.count('obs-head'),
      'hb=', body.count('class="hb"'), 'rowE=', body.count('rowE'))
