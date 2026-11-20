#!/usr/bin/env python3
"""Full-index forward/rollback zero-fuzz and SHA replay for 7/12/40 abbreviations."""
import pathlib,tempfile,subprocess,sys,hashlib,shutil
R=pathlib.Path(__file__).resolve().parent
changed=(R/'26968_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
assert len(changed)==6
A={};B={}
for name,target in (('26968_BASE_26965_FULL_APP.sha256',A),('26968_EXPECTED_FULL_APP.sha256',B)):
 for line in (R/name).read_text().splitlines():h,n=line.split('  ',1);target[n]=h
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in changed:assert sha(R/'handoff_payload_26968'/n)==B[n]
for abbrev in ('7','12','40'):
 with tempfile.TemporaryDirectory() as d:
  root=pathlib.Path(d);(root/'app').mkdir();
  for n in changed:
   p=root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26968'/n,p)
  def run(patch):
   subprocess.run(['git','-c','core.abbrev='+abbrev,'apply','--check','--unidiff-zero',str(R/patch)],cwd=root,check=True,stdout=subprocess.DEVNULL)
   subprocess.run(['git','-c','core.abbrev='+abbrev,'apply','--unidiff-zero',str(R/patch)],cwd=root,check=True,stdout=subprocess.DEVNULL)
  run('26968_ROLLBACK_FULLINDEX.patch');assert all(sha(root/n)==A[n] for n in changed)
  run('26968_FORWARD_FULLINDEX.patch');assert all(sha(root/n)==B[n] for n in changed)
  run('26968_ROLLBACK_FULLINDEX.patch');assert all(sha(root/n)==A[n] for n in changed)
for patch in ('26968_ROLLBACK_FULLINDEX.patch','26968_FORWARD_FULLINDEX.patch'):
 s=(R/patch).read_text();assert s.count('diff --git ')==6 and s.count('index ')==6
print('PASS 26968 full-index forward+rollback 7/12/40, zero fuzz, byte-identical SHA')
