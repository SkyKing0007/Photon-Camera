#!/usr/bin/env python3
"""26864 real 26863-compiled-candidate authority seeding and strict scope proof."""
from pathlib import Path
import argparse, hashlib, shutil, sys
P=argparse.ArgumentParser()
P.add_argument('base',type=Path)
P.add_argument('candidate',type=Path)
P.add_argument('--payload',type=Path,default=Path('handoff_payload_26864'))
P.add_argument('--root',type=Path,default=Path('.'))
P.add_argument('--transform',action='store_true')
a=P.parse_args();a.root=a.root.resolve();a.base=a.base.resolve();a.candidate=a.candidate.resolve();a.payload=(a.root/a.payload).resolve()
def parse(name):
 lines=(a.root/name).read_text().splitlines();out={}
 for line in lines:
  val,path=line.split('  ',1)
  assert len(val)==64 and len(bytes.fromhex(val))==32 and path.startswith('app/') and path not in out,(name,line)
  out[path]=val
 return out
prior=parse('26864_BASE_26863_FULL_APP.sha256')
post=parse('26864_EXPECTED_CANDIDATE_FULL_APP.sha256')
allowed=set((a.root/'26864_CHANGED_ALLOWLIST.txt').read_text().splitlines())
change_h=parse('26864_NEW_CHANGED_SHA256.txt')
assert allowed==set(change_h) and len(allowed)==161
assert len(prior)==1841 and len(post)==1991 and set(prior)<=set(post)
assert allowed=={p for p in post if p not in prior or post[p]!=prior[p]},'strict delta vs compiled candidate'
assert not any(p.startswith(('app/build/','app/.cxx/')) for p in allowed)
assert post['app/version.properties']!=prior['app/version.properties']
def snapshot(r):
 return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
assert snapshot(a.base)==prior,'26863 runtime authority bytes did not match persisted successful manifest'
if a.transform:
 assert a.base!=a.candidate
 shutil.rmtree(a.candidate,ignore_errors=True)
 shutil.copytree(a.base,a.candidate)
 for p in sorted(allowed):
  src=a.payload/p;assert src.is_file(),('missing replacement',p)
  dst=a.candidate/p;dst.parent.mkdir(parents=True,exist_ok=True)
  assert hashlib.sha256(src.read_bytes()).hexdigest()==post[p],('replacement hash',p)
  shutil.copyfile(src,dst)
assert snapshot(a.candidate)==post,'26864 candidate exact full file hashes/universe mismatch'
for p in sorted(set(prior)-allowed):
 assert post[p]==prior[p],('protected changed',p)
assert (a.candidate/'app/version.properties').read_text().count('VERSION_BUILD=26864')==1
assert 'VERSION_NAME=0.9726864' in (a.candidate/'app/version.properties').read_text()
print('PASS authority-seeded 26863(1841) -> 26864(1991), exact allowlist(161), all protected & DNG/native/vendor bytes and guarded version')
