#!/usr/bin/env python3
"""Exact forward/reverse and separate rollback against previous published 26933 source."""
import shutil,subprocess,sys,tempfile
from pathlib import Path
from build_26934_incremental import R,BASE,scope,sha,fail

def call(*cmd,cwd):
 p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)
 if p.returncode:fail('real git patch command failed '+' '.join(cmd)+' '+p.stderr[-800:])

def main():
 ch,ad,old,new=scope()
 if not BASE.is_dir():fail('26933 exact published source MUST be recovered before patch testing')
 with tempfile.TemporaryDirectory(prefix='26934_rollback_') as td:
  t=Path(td)
  for p in sorted(ch):
   src=BASE/p
   if not src.is_file() or sha(src)!=old[p]:fail('published previous compiled source mismatch '+p)
   dest=t/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
  forward=R/'26934_FORWARD_FULLINDEX.patch';rollback=R/'26934_ROLLBACK_FULLINDEX.patch'
  call('git','apply','--check',str(forward),cwd=t)
  call('git','apply',str(forward),cwd=t)
  for p in ch:
   if sha(t/p)!=new[p]:fail('forward modified source hash mismatch '+p)
  call('git','apply','--check','-R',str(forward),cwd=t)
  call('git','apply','-R',str(forward),cwd=t)
  for p in ch:
   if sha(t/p)!=old[p]:fail('reverse restored wrong 26933 source '+p)
  call('git','apply',str(forward),cwd=t)
  call('git','apply',str(rollback),cwd=t)
  for p in ch:
   if sha(t/p)!=old[p]:fail('separate rollback patch restored wrong 26933 source '+p)
 print('PASS exact SUCCESSFUL 26933 source -> 26934 two edits -> rollback 26933; no stale repository files')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
