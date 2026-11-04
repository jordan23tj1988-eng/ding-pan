import json,io,shutil,datetime
p='_学习/judgment_20261104.json'
shutil.copy2(p,p+'.bak_addmods'+datetime.datetime.now().strftime('%H%M'))
j=json.load(io.open(p,encoding='utf-8-sig'))
b=j['bodies']['lhb']
if '五 自主深挖' in b:
    print('already'); raise SystemExit
sd=json.load(io.open('_学习/lhb判断_20261104.json',encoding='utf-8-sig'))['深挖']
cog=json.load(io.open('_学习/lhb判断_20261104.json',encoding='utf-8-sig'))['认知迭代']
sec5 = ("<section>\n<h2>五 自主深挖 · 无 Master 指派可承接 + 一项独立深挖</h2>\n"
 "<div class=\"card\">\n<p><b>① 承接Master指派：无。</b>总审_20261103 的四项指派分别给 theme（MA-20261103-01）、limitup（MA-20261103-02）、logic（MA-20261103-03）、auction（MA-20261103-04），<b>lhb 路无指派</b>；上一项本路指派 MA-20261102-04（截至 20261103）已于昨日完成并落盘（席位荐票结算_20261030.json 闸门未落口径回写）。本段承接情况如实声明，不虚构任务。</p>\n</div>\n"
 "<div class=\"card\">\n<p><b>② 独立深挖 · 方法：</b>" + sd['方法'] + "</p>\n</div>\n"
 "<div class=\"card\">\n<p><b>③ 独立深挖 · 发现：</b>" + sd['发现'] + "</p>\n</div>\n"
 "<div class=\"card\">\n<p><b>④ 独立深挖 · 可结算判定条件：</b>" + sd['可结算判定条件'] + "</p>\n</div>\n</section>\n")
tli = "".join('<div class="tli"><div class="d">11-04</div><div class="b">%s</div></div>\n' % c for c in cog)
sec6 = ("<section>\n<h2>六 我的认知迭代</h2>\n<div class=\"tl\">\n" + tli + "</div>\n</section>")
j['bodies']['lhb'] = b + sec5 + sec6
nb=j['bodies']['lhb']
print('div balance:', nb.count('<div'), nb.count('</div>'), '| sections:', nb.count('<section>'))
json.dump(j, io.open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok len',len(nb))
