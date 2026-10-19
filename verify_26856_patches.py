#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
B,C,F,R=map(Path,sys.argv[1:5])
def U(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
wantB,wantC=U(B),U(C)
for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory() as td:
    w=Path(td)/'w'; shutil.copytree(B,w); subprocess.run(['git','init','-q'],cwd=w,check=True); subprocess.run(['git','config','user.email','x@x'],cwd=w,check=True); subprocess.run(['git','config','user.name','x'],cwd=w,check=True); subprocess.run(['git','add','-A'],cwd=w,check=True); subprocess.run(['git','commit','-q','-m','b'],cwd=w,check=True)
    subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--index','--whitespace=nowarn','--unidiff-zero',str(F.resolve())],cwd=w,check=True); assert U(w)==wantC,('forward',abbrev)
    subprocess.run(['git','commit','-q','-m','c'],cwd=w,check=True)
    subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--index','--whitespace=nowarn','--unidiff-zero',str(R.resolve())],cwd=w,check=True); assert U(w)==wantB,('rollback',abbrev)
print('PASS 26856 canonical patch proof: full-index deterministic forward/rollback at core.abbrev 7/12/40, fuzz=0, exact bytes')
