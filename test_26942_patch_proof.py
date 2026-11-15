#!/usr/bin/env python3
"""Actual successful 26941 source -> 26942 exact forward/reverse/rollback core.abbrev 7/12/40."""
import re,subprocess,sys,tempfile,shutil
from pathlib import Path
from build_26942_incremental import R,BASE,scope,sha,fail

def git(root,*args):
 p=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True)
 if p.returncode:fail('git '+str(args)+' failed '+p.stderr[-600:])
 return p.stdout

def main():
 changed,old,new=scope()
 fw=R/'26942_FORWARD_FULLINDEX.patch';rb=R/'26942_ROLLBACK_FULLINDEX.patch'
 for f in (fw,rb):
  if not f.is_file():fail('missing full-index patch')
  s=f.read_text();pairs=re.findall(r'^diff --git a/(\S+) b/(\S+)$',s,re.M)
  if len(pairs)!=2 or {x for x,y in pairs}!=changed or any(x!=y for x,y in pairs):fail('patch escaped exact 2-file allowlist')
  if s.count('index ')!=2 or s.count('@@ ')<2:fail('truncated patch')
  for line in s.splitlines():
   if line.startswith('index ') and not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40} [0-7]{6}',line):
    fail('patch untrusted abbreviated/noncanonical SHA index')
 if '--base' not in sys.argv and '--live' not in sys.argv:
  print('PASS strict two-file patch metadata; real previous 26941 replay in Actions');return
 base=Path(sys.argv[sys.argv.index('--base')+1]) if '--base' in sys.argv else BASE
 if not base.is_dir():fail('successful 26941 actual compiled source missing')
 with tempfile.TemporaryDirectory(prefix='26942_real_patch_') as d:
  tmp=Path(d);git(tmp,'init','-q')
  for p in changed:
   src=base/p
   if not src.is_file() or sha(src)!=old[p]:fail('unverified 26941 baseline '+p)
   dst=tmp/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  for abbrev in (7,12,40):
   git(tmp,'config','core.abbrev',str(abbrev))
   git(tmp,'apply','--check','--whitespace=nowarn',str(fw))
   git(tmp,'apply','--whitespace=nowarn',str(fw))
   for p in changed:
    if sha(tmp/p)!=new[p]:fail('forward mismatch '+p)
   git(tmp,'apply','--check','--reverse','--whitespace=nowarn',str(fw))
   git(tmp,'apply','--reverse','--whitespace=nowarn',str(fw))
   for p in changed:
    if sha(tmp/p)!=old[p]:fail('reverse mismatch '+p)
   git(tmp,'apply','--whitespace=nowarn',str(fw))
   git(tmp,'apply','--check','--whitespace=nowarn',str(rb))
   git(tmp,'apply','--whitespace=nowarn',str(rb))
   for p in changed:
    if sha(tmp/p)!=old[p]:fail('independent rollback mismatch '+p)
 print('PASS compiled successful 26941 -> 26942 exact full-index forward/reverse/rollback, 2 files, core.abbrev=7/12/40, fuzz=0')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
