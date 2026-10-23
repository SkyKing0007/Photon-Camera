#!/usr/bin/env python3
"""Canonical binary full-index forward/rollback under 7/12/40 and GNU patch fuzz=0."""
from pathlib import Path
import argparse,hashlib,re,shutil,subprocess,tempfile
ap=argparse.ArgumentParser()
for k in ('base','candidate','forward','rollback'):ap.add_argument(k,type=Path)
a=ap.parse_args()
def snapshot(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B=snapshot(a.base);C=snapshot(a.candidate);allow={k for k in B if B[k]!=C[k]}
assert len(B)==len(C)==1994 and set(B)==set(C) and len(allow)==3
for patch in (a.forward,a.rollback):
 data=patch.read_bytes();assert data.startswith(b'diff --git ') and data.count(b'diff --git ')==3
 assert not re.search(rb'^(?:rename|copy) (?:from|to) ',data,re.M)
 indices=list(re.finditer(rb'^index ([0-9a-f]+)\.\.([0-9a-f]+)',data,re.M))
 assert len(indices)==3 and all(len(m.group(1))==len(m.group(2))==40 for m in indices)
 names={m.group(1).decode() for m in re.finditer(rb'^diff --git a/([^\n]+) b/[^\n]+',data,re.M)}
 assert names==allow,(patch,names^allow)
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='26871_patch_') as td:
  r=Path(td);shutil.copytree(a.base/'app',r/'app')
  for patch,expected in ((a.forward,C),(a.rollback,B)):
   for args in (['--check','--whitespace=error'],['--whitespace=error']):
    p=subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply',*args,str(patch.resolve())],cwd=r,capture_output=True)
    assert p.returncode==0,(abbrev,patch,p.stderr.decode(errors='replace'))
   assert snapshot(r)==expected,('mismatched patch',abbrev,patch)
for patch,original,expected in ((a.forward,a.base,C),(a.rollback,a.candidate,B)):
 with tempfile.TemporaryDirectory(prefix='26871_fuzz0_') as td:
  r=Path(td);shutil.copytree(original/'app',r/'app')
  p=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch.resolve())],cwd=r,capture_output=True)
  assert p.returncode==0,(patch,p.stdout.decode(errors='replace'),p.stderr.decode(errors='replace'))
  assert snapshot(r)==expected,(patch,'GNU fuzz=0 mismatch')
print('PASS full-index exact 3-file forward/rollback core.abbrev 7/12/40 + GNU fuzz=0')
