# -*- coding: utf-8 -*-
"""验证_cycle_20260812.py — cycle 修复最终验证(2026-08-12 样式回归黄金版后)
用法: python 验证_cycle_20260812.py
覆盖: module_render_cycle.py 8/11完整页(黄金版形态) + 7/16整页body逐字节=黄金版 + 哨兵双日 + 负面注入 + 接线
"""
import io, os, re, subprocess, sys, tempfile

BASE = r'D:\股票数据\市场数据'
GOLDEN = r'D:\黄金对照版717\cycle.html'
sys.path.insert(0, BASE)
import module_render_cycle as mrc

ok_all, fails = [], 0

def chk(cond, label, det=''):
    global fails
    ok = bool(cond)
    ok_all.append(ok)
    if not ok: fails += 1
    print(('  ✓ ' if ok else '  ✗ ') + label + (f'  [{det}]' if det else ''))

# ===== 1. 8/11 完整页(黄金版形态: hero→七板块直连, 无机器折叠区) =====
p811 = mrc.build_page_full('20260811')
chk('判断断档·待投票恢复' in p811 and '最新主判=07-16' not in p811, '8/11 hero判断断档状态(无旧主判日期)', 'hero去7/16')
chk('07-16' not in p811[:p811.find('<h2>一')], '8/11 首屏(hero+KPI)无07-16', '旧日期全部下沉正文')
chk('量能 2.32 万亿' in p811 or re.search(r'2\.32 ?万亿', p811), '8/11 量能2.32万亿弱修档', '温度表23210亿→2.32万亿,<3.0弱修')
chk('百花医药' in p811, '8/11 最高6板=百花医药', 'zt_pool连板数6')
chk('投票断档' in p811 and '07-16' in p811, '8/11 投票断档标注07-16', '投票台账停7/16')
chk(re.search(r'15\.2 ?%', p811), '8/11 先行指标1进2率15.2%(THS补跑)', '情绪先行指标.py 20260811')
chk('<details class="chain">' not in p811, '8/11 无机器折叠区(黄金版形态)', 'hero→七板块直连')
for a in ('VOLSTEP', 'LEADIND', 'LADDER', 'MACHVOTE'):
    chk(f'<!--{a}-->' not in p811, f'8/11 机器锚{a}缺席', '有body黄金版形态')
chk(p811.count('<!--VOTEBOARD-->') == 1 and p811.count('<!--/VOTEBOARD-->') == 1, '8/11 LLM块VOTEBOARD成对', '1/1')
chk(len(re.findall(r'<h2>', p811)) == 7, '8/11 LLM七板块', '7个h2')
chk(p811.count('<div') == p811.count('</div>'), '8/11 div配平', f'{p811.count("<div")}/{p811.count("</div>")}')
# ===== 1b. 8/11 内容修正版(用户"页面内容大量错误"后) =====
chk('0709' not in p811 and '杀数量不杀赚钱效应' not in p811 and 'AI硬件' not in p811,
    '8/11 段二判读无7/16混入', '0709/杀数量/AI硬件已清')
chk('两口径并存为体系设计' in p811, '8/11 段四首板口径对照', '42=zt_pool全口径 vs 33=THS无ST')
chk('锚点撞名' not in p811, '8/11 段六无工程笔记', '8/12锚点撞名obs已清')
# 关联性: 首板占比42/58=72.4%, 炸板率17/75=22.7% (页面数字自洽)
chk('72.4%' in p811, '8/11 首板占比42/58=72.4%', '关联性自洽')
chk('22.7%' in p811, '8/11 炸板率17/75=22.7%', '关联性自洽')

# ===== 2. 7/16 整页 body 区(hero起) 逐字节 = 黄金版 =====
p716 = mrc.build_page_full('20260716')
g = io.open(GOLDEN, encoding='utf-8').read()
bp = p716[p716.find('<div class="hero">'):]
bg = g[g.find('<div class="hero">'):g.find('<div class="foot">')]  # 不含 shell 页脚
chk(bp == bg, '7/16 body区(hero起)逐字节=黄金版', f'{len(bp)}B vs {len(bg)}B')
chk('<details class="chain">' not in p716, '7/16 无机器折叠区', '黄金版形态')
chk(p716.count('<!--VOTEBOARD-->') == 1, '7/16 LLM块VOTEBOARD', '1/1(黄金版段三自带)')
chk(p716.count('<div') == p716.count('</div>'), '7/16 div配平', f'{p716.count("<div")}/{p716.count("</div>")}')

# ===== 3. 哨兵双日 PASS =====
for d in ('20260811', '20260716'):
    args = [sys.executable, os.path.join(BASE, 'cycle数据核对.py'), d]
    if d == '20260716':
        # 站点当前为8/11页, 7/16须用临时页(绝对路径)
        tmp = os.path.join(tempfile.gettempdir(), 'hv_cycle_716.html')
        io.open(tmp, 'w', encoding='utf-8').write(mrc.build_page_full('20260716'))
        args += ['--page', tmp]
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
    tail = r.stdout.strip().splitlines()[-2:]
    chk(r.returncode == 0, f'哨兵 {d} PASS', '; '.join(t.strip() for t in tail))
    if d == '20260716':
        os.remove(tmp)

# ===== 4. 负面注入: 改坏量能(全部出现) → 哨兵必须拦截 =====
bad = re.sub(r'[\d.]+ ?万亿', '9.99 万亿', p811)
bd = os.path.join(tempfile.gettempdir(), 'hv_cycle_bad.html')
io.open(bd, 'w', encoding='utf-8').write(bad)
r = subprocess.run([sys.executable, os.path.join(BASE, 'cycle数据核对.py'), '20260811', '--page', 'hv_cycle_bad.html'],
                   capture_output=True, text=True, encoding='utf-8')
os.remove(bd)
chk(r.returncode != 0, '负面注入拦截', f'改坏量能→哨兵FAIL(exit {r.returncode})')

# ===== 5. 接线 =====
gp = io.open(os.path.join(BASE, '生成盯盘台.py'), encoding='utf-8').read()
chk("k != 'cycle'" in gp and 'module_render_cycle' in gp, '生成盯盘台.py: cycle无body也渲染+模块化分支', '主循环+S2接线')

print()
print('PASS (%d项)' % len(ok_all) if fails == 0 else 'FAIL %d (%d项)' % (fails, len(ok_all)))
sys.exit(1 if fails else 0)
