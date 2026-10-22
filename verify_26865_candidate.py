#!/usr/bin/env python3
"""26865 real 26864-compiled-candidate authority seeding and strict scope proof."""
from pathlib import Path
import argparse, hashlib, shutil, sys
P=argparse.ArgumentParser()
P.add_argument('base',type=Path)
P.add_argument('candidate',type=Path)
P.add_argument('--payload',type=Path,default=Path('handoff_payload_26865'))
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
prior=parse('26865_BASE_26864_FULL_APP.sha256')
post=parse('26865_EXPECTED_CANDIDATE_FULL_APP.sha256')
allowed=set((a.root/'26865_CHANGED_ALLOWLIST.txt').read_text().splitlines())
change_h=parse('26865_NEW_CHANGED_SHA256.txt')
assert allowed==set(change_h) and len(allowed)==2
assert len(prior)==1991 and len(post)==1991 and set(prior)==set(post)
assert allowed=={p for p in post if p not in prior or post[p]!=prior[p]},'strict delta vs compiled candidate'
assert not any(p.startswith(('app/build/','app/.cxx/')) for p in allowed)
assert allowed == {'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
assert post['app/version.properties']!=prior['app/version.properties']
def snapshot(r):
 return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
assert snapshot(a.base)==prior,'26864 runtime authority bytes did not match persisted successful manifest'
if a.transform:
 assert a.base!=a.candidate
 shutil.rmtree(a.candidate,ignore_errors=True)
 shutil.copytree(a.base,a.candidate)
 for p in sorted(allowed):
  src=a.payload/p;assert src.is_file(),('missing replacement',p)
  dst=a.candidate/p;dst.parent.mkdir(parents=True,exist_ok=True)
  assert hashlib.sha256(src.read_bytes()).hexdigest()==post[p],('replacement hash',p)
  shutil.copyfile(src,dst)
assert snapshot(a.candidate)==post,'26865 candidate exact full file hashes/universe mismatch'
for p in sorted(set(prior)-allowed):
 assert post[p]==prior[p],('protected changed',p)
assert (a.candidate/'app/version.properties').read_text().count('VERSION_BUILD=26865')==1
assert 'VERSION_NAME=0.9726865' in (a.candidate/'app/version.properties').read_text()
print('PASS authority-seeded 26864(1991) -> 26865(1991), exact allowlist(2), all protected & DNG/native/vendor bytes and guarded version')
