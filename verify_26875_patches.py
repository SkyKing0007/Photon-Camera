#!/usr/bin/env python3
"""Exact 26875 full-index forward/rollback proof 7/12/40 and no fuzz."""
from pathlib import Path
import argparse,hashlib,re,shutil,subprocess,tempfile
p=argparse.ArgumentParser()
for key in ('base','candidate','forward','rollback'):p.add_argument(key,type=Path)
a=p.parse_args()
def snap(d):return {str(x.relative_to(d)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (d/'app').rglob('*') if x.is_file()}
B=snap(a.base);C=snap(a.candidate)
assert len(B)==len(C)==1997
allow={x for x in B.keys()|C.keys() if B.get(x)!=C.get(x)};assert len(allow)==3
for patch in (a.forward,a.rollback):
 blob=patch.read_bytes();assert blob.startswith(b'diff --git ') and blob.count(b'diff --git ')==3
 assert not re.search(rb'^(rename|copy) (from|to) ',blob,re.M)
 assert all(len(m.group(1))==len(m.group(2))==40 for m in re.finditer(rb'^index ([0-9a-f]+)\.\.([0-9a-f]+)',blob,re.M))
 assert {m.group(1).decode() for m in re.finditer(rb'^diff --git a/(.+?) b/[^\n]+',blob,re.M)}==allow
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26875_{abbrev}_') as td:
  d=Path(td);shutil.copytree(a.base/'app',d/'app')
  def apply(*cmd):
   r=subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply',*cmd],cwd=d,capture_output=True)
   assert r.returncode==0,(cmd,r.stderr.decode())
  apply('--check',str(a.forward.resolve()));apply(str(a.forward.resolve()));assert snap(d)==C
  apply('--check',str(a.rollback.resolve()));apply(str(a.rollback.resolve()));assert snap(d)==B
  print('PASS 26875 full-index forward/rollback zero-fuzz at core.abbrev',abbrev)
