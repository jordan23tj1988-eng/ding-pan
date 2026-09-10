import json, iFinDPy
p=r'D:/股票数据/_ifind_auth.json'; a=json.load(open(p,encoding='utf-8'))
print('LOGIN',iFinDPy.THS_iFinDLogin(a['account'],a['password']))
for code in ['HSI.HK','USDCNH.FX','NDX.GI']:
 try:
  r=iFinDPy.THS_RealtimeQuotes(code,'latest;preClose;change;changeRatio;time')
  print(code,json.dumps(r,ensure_ascii=False))
 except Exception as e: print(code,'ERR',repr(e))
