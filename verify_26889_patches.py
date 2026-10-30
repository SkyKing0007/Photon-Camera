#!/usr/bin/env python3
"""Exact 4-argument REAL full-index forward/rollback, 7/12/40, fuzz=0."""
import pathlib,sys,subprocess,tempfile,hashlib,shutil
assert len(sys.argv)==5,'USAGE base-root candidate-root forward.patch rollback.patch'
base,cand,fwd,rev=map(pathlib.Path,sys.argv[1:])
base=base.resolve();cand=cand.resolve();fwd=fwd.resolve();rev=rev.resolve()
assert base!=cand and fwd!=rev

def scan(p):return {str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file() and '.git' not in x.parts}
def call(args,cwd):
 r=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
 assert r.returncode==0,(args,r.stdout,r.stderr)
 return r
A=scan(base);B=scan(cand)
assert len(A)==2024 and len(B)==2025
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory() as tmp:
  t=pathlib.Path(tmp);shutil.copytree(base/'app',t/'app')
  call(['git','init','-q'],t)
  call(['git','-c','core.abbrev='+str(abbrev),'apply','--check',str(fwd)],t)
  call(['git','-c','core.abbrev='+str(abbrev),'apply',str(fwd)],t)
  assert scan(t)==B,('fwd sha mismatch',abbrev)
  call(['git','-c','core.abbrev='+str(abbrev),'apply','--check',str(rev)],t)
  call(['git','-c','core.abbrev='+str(abbrev),'apply',str(rev)],t)
  assert scan(t)==A,('rev sha mismatch',abbrev)
  print('PASS full index 26889 '+str(abbrev)+' exact 2025 forward/2024 byte-perfect rollback')
