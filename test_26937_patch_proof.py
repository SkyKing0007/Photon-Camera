#!/usr/bin/env python3
"""Exact 26936 compiled source forward, reverse and independent 26937 rollback proof."""
import subprocess,sys,tempfile,shutil,re
from pathlib import Path
from build_26937_incremental import R,BASE,scope,sha,fail

def git(root,*args):
 p=subprocess.run(['git',*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:fail('actual git '+str(args)+' failed: '+p.stderr[-600:])
 return p.stdout

def main():
 changed,added,old,new=scope()
 fw=R/'26937_FORWARD_FULLINDEX.patch';rb=R/'26937_ROLLBACK_FULLINDEX.patch'
 if not fw.is_file() or not rb.is_file():fail('missing deterministic forward/rollback')
 for f in (fw,rb):
  txt=f.read_text()
  h=re.findall(r'^diff --git a/(\S+) b/(\S+)$',txt,re.M)
  if len(h)!=4 or {x for x,y in h}!=changed or any(x!=y for x,y in h):fail('patch path escaped four-file exact allowlist')
  if txt.count('@@ ')<8 or txt.count('index ')!=4:fail('truncated full-index patch')
 if '--live' not in sys.argv:
  print('PASS strict four-file current source patch metadata (real compiled 26936 replay required in Actions)')
  return
 if not BASE.is_dir():fail('official compiled 26936 base required for real replay')
 with tempfile.TemporaryDirectory(prefix='26937_fullindex_') as td:
  q=Path(td);git(q,'init','-q')
  for name in sorted(changed):
   src=BASE/name
   if not src.is_file() or sha(src)!=old[name]:fail('official prior source mismatch '+name)
   dst=q/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  for abbreviated in (7,12,40):
   git(q,'config','core.abbrev',str(abbreviated))
   git(q,'apply','--check','--whitespace=nowarn',str(fw))
   git(q,'apply','--whitespace=nowarn',str(fw))
   for name in changed:
    if sha(q/name)!=new[name]:fail('forward byte hash mismatch '+name)
   git(q,'apply','--check','--reverse','--whitespace=nowarn',str(fw))
   git(q,'apply','--reverse','--whitespace=nowarn',str(fw))
   for name in changed:
    if sha(q/name)!=old[name]:fail('reverse byte hash mismatch '+name)
   git(q,'apply','--whitespace=nowarn',str(fw))
   git(q,'apply','--check','--whitespace=nowarn',str(rb))
   git(q,'apply','--whitespace=nowarn',str(rb))
   for name in changed:
    if sha(q/name)!=old[name]:fail('independent rollback byte hash mismatch '+name)
 print('PASS authentic 26936 compiled base -> 26937 forward, reverse and independent rollback core.abbrev=7/12/40 fuzz=0')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
