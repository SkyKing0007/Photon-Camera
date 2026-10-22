#!/usr/bin/env python3
"""Deterministic full-index binary patch replay of real 26866 authority bytes."""
from pathlib import Path
import argparse,hashlib,subprocess,tempfile,shutil,re
P=argparse.ArgumentParser()
for name in ('base','candidate','forward','rollback'):P.add_argument(name,type=Path)
a=P.parse_args()
def files(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
base=files(a.base);cand=files(a.candidate)
assert len(base)==1991 and len(cand)==1991
allowed={p for p in cand if p not in base or cand[p]!=base[p]}
assert len(allowed)==5 and not set(base)-set(cand)
for p in (a.forward,a.rollback):
 b=p.read_bytes()
 assert b.startswith(b'diff --git ') and b.count(b'\ndiff --git ')+1==len(allowed),(p,'file changes')
 assert not re.search(rb'^(?:rename|copy) (?:to|from) ',b,flags=re.M),(p,'rename inference')
 assert all(len(x.group(1))==40 and len(x.group(2))==40 for x in re.finditer(rb'^index ([0-9a-f]+)\.\.([0-9a-f]+)',b,flags=re.M)),(p,'short-index')
for ab in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26867patch_{ab}_') as td:
  r=Path(td);shutil.copytree(a.base/'app',r/'app')
  def run(*args):subprocess.run(['git','-c',f'core.abbrev={ab}','apply',*args],cwd=r,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  run('--check',str(a.forward.resolve()))
  run(str(a.forward.resolve()))
  assert files(r)==cand,('forward',ab)
  run('--check',str(a.rollback.resolve()))
  run(str(a.rollback.resolve()))
  assert files(r)==base,('rollback',ab)
 print(f'PASS 26867 canonical full-index forward/rollback exact, fuzz=0, core.abbrev={ab}')
