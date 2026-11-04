import io,shutil,datetime,json
p='_学习/limitup判断_20261104.json'
shutil.copy2(p,p+'.bak_null'+datetime.datetime.now().strftime('%H%M'))
s=io.open(p,encoding='utf-8-sig').read()
n1=s.count('昨停溢价=null（源取数失败）'); n2=s.count('昨停溢价=null（取数失败）')
s=s.replace('昨停溢价=null（源取数失败）','昨停溢价=—（源取数失败）').replace('昨停溢价=null（取数失败）','昨停溢价=—（取数失败）')
io.open(p,'w',encoding='utf-8').write(s)
json.load(io.open(p,encoding='utf-8-sig'))  # validate
print('replaced',n1,n2,'| remaining null（:',s.count('null（'))
