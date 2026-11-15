#!/usr/bin/env python3
"""Full-index deterministic forward/reverse/independent rollback, 7/12/40, fuzz=0."""
import re,subprocess,sys,tempfile,shutil
from pathlib import Path
from build_26940_incremental import R,BASE,scope,sha,fail

def git(root,*args):
 x=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True)
 if x.returncode:fail('git '+str(args)+' failed '+x.stderr[-500:])
 return x.stdout

def main():
 changed,old,new=scope()
 fw=R/'26940_FORWARD_FULLINDEX.patch';rb=R/'26940_ROLLBACK_FULLINDEX.patch'
 for f in (fw,rb):
  if not f.is_file():fail('missing full-index patch '+f.name)
  s=f.read_text();pairs=re.findall(r'^diff --git a/(\S+) b/(\S+)$',s,re.M)
  if len(pairs)!=len(changed) or {x for x,y in pairs}!=changed or any(x!=y for x,y in pairs):fail('patch escaped exactly seven-file scope')
  if s.count('index ')!=len(changed) or s.count('@@ ')<len(changed):fail('truncated git patch index/hunks')
  if not all(re.fullmatch(r'index [a-f0-9]{40}\.\.[a-f0-9]{40} [0-7]{6}',line) for line in s.splitlines() if line.startswith('index ')):
   fail('patch index is not unshortened original Git SHA-1')
 if '--live' not in sys.argv and '--base' not in sys.argv:
  print('PASS exact 26940 seven-file source full-index forward+rollback metadata (real replay in Actions)');return
 if '--base' in sys.argv:
  ix=sys.argv.index('--base');base=Path(sys.argv[ix+1])
 else:base=BASE
 if not base.is_dir():fail('authentic successful 26939 compiled authority missing for patch replay')
 with tempfile.TemporaryDirectory(prefix='26940_fullindex_') as td:
  q=Path(td);git(q,'init','-q')
  for p in changed:
   src=base/p
   if not src.is_file() or sha(src)!=old[p]:fail('authentic prior 26939 compiled source wrong '+p)
   dst=q/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  for ab in (7,12,40):
   git(q,'config','core.abbrev',str(ab))
   git(q,'apply','--check','--whitespace=nowarn',str(fw))
   git(q,'apply','--whitespace=nowarn',str(fw))
   for p in changed:
    if sha(q/p)!=new[p]:fail('forward exact source bytes diverged '+p)
   git(q,'apply','--check','--reverse','--whitespace=nowarn',str(fw))
   git(q,'apply','--reverse','--whitespace=nowarn',str(fw))
   for p in changed:
    if sha(q/p)!=old[p]:fail('reverse exact source bytes diverged '+p)
   git(q,'apply','--whitespace=nowarn',str(fw))
   git(q,'apply','--check','--whitespace=nowarn',str(rb))
   git(q,'apply','--whitespace=nowarn',str(rb))
   for p in changed:
    if sha(q/p)!=old[p]:fail('independent exact rollback source bytes diverged '+p)
 print('PASS 26939 official compiled source -> 26940 forward/reverse/independent rollback core.abbrev=7/12/40 fuzz=0 all seven files')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
