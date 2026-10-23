#!/usr/bin/env python3
"""Exact 26871-inherited 7/12/40 full-index binary zero-fuzz forward/rollback."""
from pathlib import Path
import argparse,hashlib,re,shutil,subprocess,tempfile
p=argparse.ArgumentParser()
for n in ('base','candidate','forward','rollback'):p.add_argument(n,type=Path)
a=p.parse_args()
def hashes(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B=hashes(a.base);C=hashes(a.candidate)
assert len(B)==1994 and len(C)==1995
allowed={k for k in B.keys()|C.keys() if B.get(k)!=C.get(k)}
assert len(allowed)==5 and not set(B)-set(C)
for patch in (a.forward,a.rollback):
 b=patch.read_bytes()
 assert b.startswith(b'diff --git ') and b.count(b'diff --git ')==5
 assert not re.search(rb'^(rename|copy) (from|to) ',b,re.M)
 assert all(len(x.group(1))==40 and len(x.group(2))==40 for x in re.finditer(rb'^index ([0-9a-f]+)\.\.([0-9a-f]+)',b,re.M))
 paths={x.group(1).decode() for x in re.finditer(rb'^diff --git [ab]/([^\n]+) [ab]/[^\n]+',b,re.M)}
 assert paths==allowed,(patch,paths^allowed)
for ab in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26872_{ab}_') as td:
  wd=Path(td);shutil.copytree(a.base/'app',wd/'app')
  def go(*args):
   r=subprocess.run(['git','-c',f'core.abbrev={ab}','apply','--whitespace=nowarn',*args],cwd=wd,capture_output=True)
   assert r.returncode==0,(args,r.stderr.decode(errors='replace'))
  go('--check',str(a.forward.resolve()));go(str(a.forward.resolve()))
  assert hashes(wd)==C,('forward mismatch',ab)
  go('--check',str(a.rollback.resolve()));go(str(a.rollback.resolve()))
  assert hashes(wd)==B,('rollback mismatch',ab)
  print('PASS 26872 inherited full-index binary forward/rollback fuzz=0 core.abbrev='+str(ab))
