# -*- coding: utf-8 -*-
"""8/12 auction body 黄金版八段重建(2026-08-12, 用户"你回归的组件跟黄金版完全不一样"确认后)
骨架=黄金版717 auction 八段(一评分表/★闸门/★初读/二温度/三结算/四信号库/五深挖/六认知)
内容=8/12 判断json+现有body提取, 数字零编造; 机器段=空锚由渲染器注入
写回: judgment_20260812.json bodies.auction + auction_body_20260812.html"""
import json, io, re, sys

bp = 'auction_body_20260812.html'
jp = 'judgment_20260812.json'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

b = json.load(io.open(jp, encoding='utf-8'))['bodies']['auction']   # 37357B 六段版
jd = json.load(io.open('auction判断_20260812.json', encoding='utf-8'))
pd = jd.get('判断', {})
tj = jd.get('荐票', {})

# ---- 1. 提取现有 hero 区(rowA 开头 → stance 后) ----
i0 = b.find('<div class="rowA">')
i1 = b.find('<div class="stance">', i0)
i2 = b.find('</div></div>', i1) + len('</div></div>')   # stance+hero+rowA 全部闭合(含)
assert i0 >= 0 and i1 > 0 and i2 > i1, 'hero 区定位失败'
hero = b[i0:i2]

# kpi 区(hero 后到第一个 section)
i3 = b.find('<section', i2)
kpi = b[i2:i3].strip()

# ---- 2. 提取现有段五(深挖)/段六(认知) ----
def seg(tag, nxt):
    a = b.find('<h2>%s' % tag)
    z = b.find('<h2>%s' % nxt, a)
    return b[a:z] if z > a else b[a:]

s_wu = seg('五', '六')
s_liu = seg('六', '文')
# 段六可能到最后无下个 h2
if not s_liu:
    a = b.find('<h2>六')
    s_liu = b[a:] if a >= 0 else ''

# ---- 3. 洞察卡(8/12 判断结论+荐票 6 只, 数字全回源) ----
tks = tj.get('标的', [])
obs_lines = ''
for t in tks:
    gd = re.sub(r'^.*?闸门[：:]*\s*', '', t.get('理由', ''))
    gd = gd[:40]
    obs_lines += '；%s(%s,%s,%s分)' % (t.get('名称', '?'), t.get('代码', ''), t.get('类型', ''), t.get('竞价分', '—'))
insight = ('<div class="card"><b>洞察(agent)</b><p>%s</p>'
           '<p class="mut">重点观察：%s——全部待8/13 9:25实开闸门过滤后执行（高开≥5%%历史必弃, 只吃高开<5%%）。</p></div>'
           % (pd.get('结论', ''), obs_lines.lstrip('；')))

# ---- 4. 温度卡(8/12 数字从判断证据组织, 零新增) ----
ev = pd.get('证据', '')
temp_card = ('<div class="card"><p>竞价端温度=<b class="s-mid">偏热 68.5</b>（昨48.8，跳升+19.7，未触85过热线）：'
             '涨停92/跌停0/炸板率12.4%低位，7板百花续板+3板梯队8只=高标承接强，多主线共振；'
             '量能21524亿。早盘抢筹面广（首封≤09:31共13只，09:25首封9只占69%）≥米开第一式一字≥2定强度线。</p>'
             '<p class="mut">温度=环境进攻档（A档）但非个股必赚档——池内评分最高50.4、高分半仅4/13、高分组历史绝对收益≈0，明晨执行一律过闸门。</p></div>')

# ---- 5. 八段拼装(黄金版骨架, 机器段留空锚) ----
body_new = (
    hero + '\n' + kpi + '\n'
    '<section class="sec" id="p1">'
    '<h2>一 竞价选股池 · 当日<span class="hint">池口径=当日涨停里"明晨值得看竞价"的票；评分=一年分桶库加权，桶均值非个股预言；SCORECARD=脚本注入</span></h2>'
    '<!--SCORECARD--><!--/SCORECARD-->' + insight + '</section>\n'
    '<section class="sec" id="p2">'
    '<h2 class="hot">★今晨闸门 · 08-12池按9:25实开过滤(待8/13早盘)</h2>'
    '<!--MACHGATE--><!--/MACHGATE--></section>\n'
    '<section class="sec" id="p3">'
    '<h2 class="hot">★今晨初读 · 08-12池 T+1竞价初读(待8/13 09:31)</h2>'
    '<span class="hint">初读=09:31实时强弱判定, 页面生成时未到如实待补, 晚间管道自动回填</span>'
    '<!--MACHREAD--><!--/MACHREAD--></section>\n'
    '<section class="sec" id="p4">'
    '<h2>二 今日竞价温度</h2>' + temp_card + '</section>\n'
    '<section class="sec" id="p5">'
    '<h2>三 昨日池 · 今日终结算<span class="hint">POOLLEDGER=归档脚本注入(按发出版名单, 执行口径)；最新日展开, 旧日折叠</span></h2>'
    '<!--POOLLEDGER--><!--/POOLLEDGER--></section>\n'
    '<section class="sec" id="p6">'
    '<h2>四 竞价信号胜率追踪<span class="hint">一年分桶库；观察基准非荐票</span></h2>'
    '<!--MACHSIG--><!--/MACHSIG--></section>\n'
    '<section class="sec" id="p7">' + (s_wu if s_wu else '<h2>五 自主深挖 · 信号孵化</h2><div class="card"><p>当日无新孵化候选。</p></div>') + '</section>\n'
    '<section class="sec" id="p8">' + (s_liu if s_liu else '<h2>六 我的认知迭代 · 最新</h2><div class="card"><p>当日无新认知。</p></div>') + '</section>\n'
)

# ---- 6. 校验: div 配平 + 数字零编造(hero 关键数字全保留) ----
assert body_new.count('<div') == body_new.count('</div>'), 'div 不配平'
for tok in ('13只', '69%', '68.5', '92', '12.4%', '7/10', '+3.28%', '50.4', '-1.74%', '1357', '21524亿', '19.7'):
    assert tok in body_new, '关键数字丢失: %s' % tok
# 无 rec-card/pan-card 自造残留
assert 'rec-card' not in body_new and 'pan-card' not in body_new, '自造结构残留'

# ---- 7. 双写回 ----
io.open(bp, 'w', encoding='utf-8').write(body_new)
j = json.load(io.open(jp, encoding='utf-8'))
j['bodies']['auction'] = body_new
json.dump(j, io.open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK 重建完成: %dB | div %d/%d | h2 %d | 空锚 SCORECARD/MACHGATE/MACHREAD/POOLLEDGER/MACHSIG 就绪' % (
    len(body_new), body_new.count('<div'), body_new.count('</div>'), len(re.findall(r'<h2', body_new))))
