#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
B,C,F,R=map(Path,sys.argv[1:5]); B=B.resolve(); C=C.resolve(); F=F.resolve(); R=R.resolve()
def U(r): return {p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def run(cmd,cwd): subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
base,cand=U(B),U(C)
for ab in (7,12,40):
    with tempfile.TemporaryDirectory() as td:
        t=Path(td); shutil.copytree(B/'app',t/'app'); run(['git','init','-q'],t); run(['git','config','user.email','x@y.invalid'],t); run(['git','config','user.name','x'],t); run(['git','config','core.abbrev',str(ab)],t); run(['git','add','app'],t); run(['git','commit','-q','-m','base'],t)
        run(['git','apply','--index','--whitespace=nowarn',str(F)],t); assert U(t)==cand,('forward',ab)
        run(['git','reset','--hard','-q','HEAD'],t)
        run(['git','apply','--whitespace=nowarn',str(F)],t); assert U(t)==cand
        run(['git','apply','--whitespace=nowarn',str(R)],t); assert U(t)==base,('rollback',ab)
        print(f'PASS 26835 patch core.abbrev={ab} forward/rollback exact fuzz=0')
print('PASS 26835 canonical patch proof')
