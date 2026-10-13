#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile,shutil,sys,hashlib
B,C,F,R=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4])
def U(r): return {p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
u0,u1=U(B),U(C)
for ab in (7,12,40):
  with tempfile.TemporaryDirectory() as td:
    t=Path(td); shutil.copytree(B/'app',t/'app'); subprocess.run(['git','init','-q'],cwd=t,check=True); subprocess.run(['git','config','user.email','x@y.z'],cwd=t); subprocess.run(['git','config','user.name','x'],cwd=t); subprocess.run(['git','config','core.abbrev',str(ab)],cwd=t,check=True); subprocess.run(['git','add','app'],cwd=t,check=True); subprocess.run(['git','commit','-qm','b'],cwd=t,check=True)
    cp=subprocess.run(['git','apply','--index','--whitespace=nowarn',str(F.resolve())],cwd=t,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); assert cp.returncode==0,cp.stdout; assert U(t)==u1
    subprocess.run(['git','commit','-qm','c'],cwd=t,check=True); cp=subprocess.run(['git','apply','--index','--whitespace=nowarn',str(R.resolve())],cwd=t,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); assert cp.returncode==0,cp.stdout; assert U(t)==u0
    print(f'PASS 26824 patch core.abbrev={ab} fuzz=0 exact rollback')
print('PASS 26824 canonical patch proof')
