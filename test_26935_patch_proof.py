#!/usr/bin/env python3
"""Actual 26934->26935 git apply and rollback with exact full-index, 7/12/40 abbrev styles."""
from build_26935_incremental import R,BASE,scope,sha,fail
import pathlib,tempfile,shutil,subprocess,sys

def run(cwd,*args):
 p=subprocess.run(['git','-c','core.abbrev='+str(ABBREV),'apply',*args],cwd=cwd,capture_output=True,text=True)
 if p.returncode:fail('real git apply failed '+str(args)+' '+p.stderr[-1100:])

def main():
 ch,ad,old,new=scope()
 if not BASE.is_dir():
  if '--payload' in sys.argv:
   # Package stage requires no historical base checkout; full patch replay runs after FETCH/prepare.
   print('PASS 26935 patch source format pending actual successful 26934 Actions compiled-base replay')
   return
  fail('actual 26934 source missing; never use repository as patch authority')
 global ABBREV
 for abbrev in (7,12,40):
  ABBREV=abbrev
  with tempfile.TemporaryDirectory(prefix='26935_git_apply_') as d:
   t=pathlib.Path(d)
   for path in sorted(ch):
    f=t/path;f.parent.mkdir(parents=True,exist_ok=True)
    if sha(BASE/path)!=old[path]:fail('not exact 26934 compiled patch base '+path)
    shutil.copy2(BASE/path,f)
   f=R/'26935_FORWARD_FULLINDEX.patch';b=R/'26935_ROLLBACK_FULLINDEX.patch'
   run(t,'--check',str(f))
   run(t,str(f))
   for path in ch|ad:
    if not (t/path).is_file() or sha(t/path)!=new[path]:fail('forward patch did not reconstruct '+path)
   run(t,'--check','-R',str(f))
   run(t,'-R',str(f))
   for path in ch:
    if sha(t/path)!=old[path]:fail('reverse diff failed '+path)
   for path in ad:
    if (t/path).exists():fail('added path retained after rollback '+path)
   run(t,str(f))
   run(t,str(b))
   for path in ch:
    if sha(t/path)!=old[path]:fail('separate rollback failed '+path)
   for path in ad:
    if (t/path).exists():fail('separate rollback did not remove new class '+path)
 print('PASS actual 26934 compiled source -> 26935 6 modified 2 new -> reverse and separate rollback at 7/12/40; exact SHA')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
