#!/usr/bin/env python3
"""Exact four-argument full-index forward rollback, actual success 26889 source."""
import pathlib,subprocess,tempfile,shutil,hashlib,sys
assert len(sys.argv)==5,('requires BASE CAND FORWARD ROLLBACK',sys.argv)
B,C=map(pathlib.Path,sys.argv[1:3]);R=pathlib.Path(__file__).resolve().parent
assert sys.argv[3:]==['26890_FORWARD_FULL_INDEX.patch','26890_ROLLBACK_FULL_INDEX.patch']
fw=(R/sys.argv[3]).read_bytes();rb=(R/sys.argv[4]).read_bytes()
paths=(R/'26890_CHANGED_ALLOWLIST.txt').read_text().splitlines()
def h(p):return hashlib.sha256(p.read_bytes()).digest()
def run(cwd,*args):return subprocess.run(['git',*args],cwd=cwd,capture_output=True,check=True).stdout
with tempfile.TemporaryDirectory(prefix='photon26890_') as t:
 w=pathlib.Path(t);shutil.copytree(B/'app',w/'app')
 run(w,'init','-q');run(w,'config','user.email','proof@example.invalid');run(w,'config','user.name','Photon Proof');run(w,'config','core.autocrlf','false')
 run(w,'add','-f','--all');run(w,'commit','-qm','success 26889 exact compiled source')
 for core in (7,12,40):
  run(w,'reset','--hard','HEAD')
  run(w,'apply','--check','--index',str(R/sys.argv[3]))
  run(w,'apply','--index',str(R/sys.argv[3]))
  assert run(w,'diff','--cached','--name-only').decode().splitlines()==paths
  assert all(h(w/k)==h(C/k) for k in paths)
  assert run(w,'-c',f'core.abbrev={core}','diff','--cached','--full-index','--binary','HEAD')==fw
  assert run(w,'-c',f'core.abbrev={core}','diff','--cached','--full-index','--binary','-R','HEAD')==rb
  run(w,'apply','--check','--index',str(R/sys.argv[4]))
  run(w,'apply','--index',str(R/sys.argv[4]))
  assert not run(w,'status','--porcelain')
print('PASS ACTUAL 26889 source, exact 8 changed files, 7/12/40 deterministic binary full-index forward/rollback fuzz=0')
