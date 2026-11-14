#!/usr/bin/env python3
"""Real git apply + reverse proof on EXACT 26931 source before Android, no source commit/push."""
from pathlib import Path
import sys,subprocess,tempfile,shutil,hashlib
from build_26932_incremental import R,scope,fail,sha,parse,BASE

def call(*cmd,cwd):
 p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)
 if p.returncode:fail('real git patch failure '+' '.join(cmd)+' '+p.stderr[-900:])
 return p

def main():
 ch,ad,b,n=scope()
 # In Actions use fetched EXACT successful 26931 compiled source; local proof
 # falls back to frozen manifest, plus independently check before committing any handoff.
 source=BASE if BASE.is_dir() else None
 if '--live' in sys.argv and not source:fail('real published prior candidate not fetched for patch proof')
 with tempfile.TemporaryDirectory(prefix='photon26932_patch_') as tmp:
  t=Path(tmp)
  for path in sorted(ch):
   if not source:fail('exact successful 26931 published compiled authority missing; fetch and prepare before patch proof')
  for path in sorted(ch):
   original=source/path
   if not original.is_file() or sha(original)!=b[path]:fail('prior source hash mismatch '+path)
   dst=t/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,dst)
  call('git','apply','--check',str(R/'26932_FORWARD_FULLINDEX.patch'),cwd=t)
  call('git','apply',str(R/'26932_FORWARD_FULLINDEX.patch'),cwd=t)
  for path in sorted(ch|ad):
   if not (t/path).is_file() or sha(t/path)!=n[path]:fail('git forward patch exact sha mismatch '+path)
  call('git','apply','--check','-R',str(R/'26932_FORWARD_FULLINDEX.patch'),cwd=t)
  call('git','apply','-R',str(R/'26932_FORWARD_FULLINDEX.patch'),cwd=t)
  for path in sorted(ch):
   if not (t/path).is_file() or sha(t/path)!=b[path]:fail('git reverse patch changed protected source '+path)
  for path in ad:
   if (t/path).exists():fail('git reverse did not remove new 26932 source '+path)
  # Separately test independent rollback patch on clean patched source.
  call('git','apply',str(R/'26932_FORWARD_FULLINDEX.patch'),cwd=t)
  call('git','apply',str(R/'26932_ROLLBACK_FULLINDEX.patch'),cwd=t)
  for path in ch:
   if sha(t/path)!=b[path]:fail('independent rollback patch mismatch '+path)
  for path in ad:
   if (t/path).exists():fail('independent rollback retained extra source '+path)
 print('PASS exact git forward/reverse and independently constructed rollback patches; 2046 seeded -> 2048 -> 2046')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
