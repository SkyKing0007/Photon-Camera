#!/usr/bin/env python3
"""Strict full-index independent forward/reverse/rollback from exact 26943 V5 compiled authority."""
import re,subprocess,sys,tempfile,shutil
from pathlib import Path
from build_26944_incremental import R,BASE,scope,sha,fail,REQUIRED,ADDED

def git(root,*args):
 p=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True)
 if p.returncode:fail('git '+str(args)+' failed '+p.stderr[-800:])
 return p.stdout

def main():
 changed,old,new=scope();fw=R/'26944_FORWARD_FULLINDEX.patch';rb=R/'26944_ROLLBACK_FULLINDEX.patch'
 for f in (fw,rb):
  if not f.is_file():fail('missing independent full-index patch')
  s=f.read_text();pairs=re.findall(r'^diff --git a/(\S+) b/(\S+)$',s,re.M)
  if len(pairs)!=7 or {x for x,y in pairs}!=changed or any(x!=y for x,y in pairs):fail('not exact seven source allowlist')
  if s.count('index ')!=7 or s.count('@@ ')<7:fail('truncated full-index patch')
  for line in s.splitlines():
   if line.startswith('index ') and not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40}(?: [0-7]{6})?',line):fail('abbreviated/fuzzy/noncanonical SHA patch index')
 if '--base' not in sys.argv and '--live' not in sys.argv:
  print('PASS strict 26944 7-source full-index forward/rollback metadata; actual 26943 replay mandatory on Actions')
  return
 base=Path(sys.argv[sys.argv.index('--base')+1]) if '--base' in sys.argv else BASE
 if not base.is_dir():fail('actual successful 26943 V5 compiled source missing')
 with tempfile.TemporaryDirectory(prefix='photon_26944_patch_') as td:
  tmp=Path(td);git(tmp,'init','-q')
  for p in REQUIRED:
   src=base/p
   if not src.is_file() or sha(src)!=old[p]:fail('not exact successful 26943 V5 file '+p)
   dst=tmp/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  for abbrev in (7,12,40):
   git(tmp,'config','core.abbrev',str(abbrev))
   git(tmp,'apply','--check','--whitespace=nowarn',str(fw))
   git(tmp,'apply','--whitespace=nowarn',str(fw))
   for p in changed:
    if not (tmp/p).is_file() or sha(tmp/p)!=new[p]:fail('forward content wrong '+p)
   git(tmp,'apply','--check','--reverse','--whitespace=nowarn',str(fw))
   git(tmp,'apply','--reverse','--whitespace=nowarn',str(fw))
   for p in REQUIRED:
    if sha(tmp/p)!=old[p]:fail('reverse content wrong '+p)
   git(tmp,'apply','--whitespace=nowarn',str(fw))
   git(tmp,'apply','--check','--whitespace=nowarn',str(rb))
   git(tmp,'apply','--whitespace=nowarn',str(rb))
   for p in REQUIRED:
    if sha(tmp/p)!=old[p]:fail('independent rollback content wrong '+p)
 print('PASS actual successful 26943 V5 -> 26944 independent seven full-index patches, 2047 protected, forward/reverse/rollback 7/12/40')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
