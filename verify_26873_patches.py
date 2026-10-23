#!/usr/bin/env python3
"""Deterministic 26873 full-index forward/rollback proof at 7,12,40 with zero fuzz."""
from pathlib import Path
import argparse,hashlib,re,shutil,subprocess,tempfile
p=argparse.ArgumentParser()
for key in ('base','candidate','forward','rollback'):p.add_argument(key,type=Path)
a=p.parse_args()
def snap(d):return {str(x.relative_to(d)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (d/'app').rglob('*') if x.is_file()}
B=snap(a.base);C=snap(a.candidate);assert len(B)==len(C)==1995
allow={x for x in B if B[x]!=C[x]};assert len(allow)==6
for patch in (a.forward,a.rollback):
 blob=patch.read_bytes();assert blob.startswith(b'diff --git ') and blob.count(b'diff --git ')==6
 assert not re.search(rb'^(rename|copy) (from|to) ',blob,re.M)
 assert all(len(m.group(1))==len(m.group(2))==40 for m in re.finditer(rb'^index ([0-9a-f]+)\.\.([0-9a-f]+)',blob,re.M))
 assert {m.group(1).decode() for m in re.finditer(rb'^diff --git a/(.+?) b/[^\n]+',blob,re.M)}==allow
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26873_{abbrev}_') as td:
  dest=Path(td);shutil.copytree(a.base/'app',dest/'app')
  def patch_it(*commands):
   r=subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--whitespace=nowarn',*commands],cwd=dest,capture_output=True)
   assert r.returncode==0,(commands,r.stderr.decode())
  patch_it('--check',str(a.forward.resolve()));patch_it(str(a.forward.resolve()));assert snap(dest)==C
  patch_it('--check',str(a.rollback.resolve()));patch_it(str(a.rollback.resolve()));assert snap(dest)==B
  print('PASS 26873 binary forward/rollback zero-fuzz at core.abbrev',abbrev)
