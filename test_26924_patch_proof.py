#!/usr/bin/env python3
"""26924 deterministic full-index forward/rollback 7/12/40 and failure cases.
Use only actual downloaded successful 26923 authority and frozen 26924 candidate.
"""
from pathlib import Path
import subprocess,hashlib,tempfile,shutil
R=Path(__file__).resolve().parent
A=R/'.photon_26924_work/authority_26923';B=R/'.photon_26924_work/candidate_26924'
CHANGE=set((R/'26924_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
ADD=set((R/'26924_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
P=R/'26924_FORWARD_FULLINDEX.patch';RB=R/'26924_ROLLBACK_FULLINDEX.patch'
assert len(CHANGE)==9 and len(ADD)==9 and A.is_dir() and B.is_dir()
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='p26924_patch_') as d:
  base=Path(d)
  for name in CHANGE:
   f=base/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(A/name,f)
  def git(p,*args):
   return subprocess.run(['git','-c','core.abbrev='+str(n),'apply',*args,str(p)],cwd=base,text=True,capture_output=True)
  for args in [('--check',),(),('--reverse','--check'),('--reverse',)]:
   result=git(P,*args)
   assert result.returncode==0,(n,args,result.stderr)
   if args==():assert all(H(base/name)==H(B/name) for name in CHANGE|ADD)
   if args==('--reverse',):assert all(H(base/name)==H(A/name) for name in CHANGE) and all(not (base/name).exists() for name in ADD)
  # The separately supplied rollback must agree with the forward inverse.
  assert git(RB,'--check').returncode!=0,'rollback must not apply to original prior source'
  # Negative missing source and altered hunk never silently succeed.
  victim='app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp';source=base/victim;text=source.read_text();assert text.count('wronski.fallbackChromaGain=4.0f;')==1
  source.write_text(text.replace('wronski.fallbackChromaGain=4.0f;','wronski.fallbackChromaGain=4.0001f;',1))
  assert git(P,'--check').returncode!=0,'mutation ignored'
  source.unlink();assert git(P,'--check').returncode!=0,'deleted baseline ignored'
print('PASS 26924 forward/reverse full-index 7/12/40, 9 changed, 9 added, mutation/deletion rejected')
