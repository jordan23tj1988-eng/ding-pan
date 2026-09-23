import subprocess,sys,os
R=r'D:\股票数据\市场数据'; env=dict(os.environ,LHB_SITE_ROOT=R+r'\复盘\盯盘台',PYTHONIOENCODING='utf-8',PYTHONUTF8='1'); cp=subprocess.run([sys.executable,R+r'\lhb数据核对.py','20260911'],cwd=R,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace');print('rc',cp.returncode);print('OUT',cp.stdout[-500:]);print('ERR',cp.stderr[-500:])
