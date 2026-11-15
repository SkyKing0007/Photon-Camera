#!/usr/bin/env python3
"""Source-identity and full-index forward/rollback native git apply proof.
After Actions previous official artifact extraction, verifies exact old/new bytes.
Before fetch, verifies sealed patch syntax/strict allowed headers, not fake compiled proof.
"""
import subprocess,sys,tempfile,shutil,re
from pathlib import Path
from build_26936_incremental import R,BASE,scope,sha,fail

def git(root,*args):
 p=subprocess.run(['git',*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:fail('actual git '+str(args)+' failed: '+p.stderr[-600:])
 return p.stdout

def main():
 changed,added,old,new=scope()
 forward=R/'26936_FORWARD_FULLINDEX.patch';backward=R/'26936_ROLLBACK_FULLINDEX.patch'
 if not forward.is_file() or not backward.is_file():fail('missing separate forward/rollback patches')
 for file in (forward,backward):
  s=file.read_text()
  hdr=re.findall(r'^diff --git a/(\S+) b/(\S+)$',s,re.M)
  if len(hdr)!=len(changed) or {a for a,b in hdr}!=changed or any(a!=b for a,b in hdr):fail('unexpected modified paths in patch')
  if s.count('@@ ')<len(changed)*2:fail('truncated patch hunks')
 if '--live' not in sys.argv:
  print('PASS 26936 package forward/rollback strict seven-file path and header guards (compiled 26935 replay later)')
  return
 if not BASE.is_dir():fail('cannot prove rollback without actual official successful 26935 compiled base')
 with tempfile.TemporaryDirectory(prefix='26936_git_fullrollback_') as td:
  scratch=Path(td)
  git(scratch,'init','-q')
  for path in sorted(changed):
   old_path=BASE/path
   if not old_path.is_file() or sha(old_path)!=old[path]:fail('old successful 26935 SHA mismatch '+path)
   q=scratch/path;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old_path,q)
  for abbreviated in (7,12,40):
   git(scratch,'config','core.abbrev',str(abbreviated))
   git(scratch,'apply','--check','--whitespace=nowarn',str(forward))
   git(scratch,'apply','--whitespace=nowarn',str(forward))
   for path in changed:
    if sha(scratch/path)!=new[path]:fail('forward application SHA mismatch '+path)
   git(scratch,'apply','--check','--reverse','--whitespace=nowarn',str(forward))
   git(scratch,'apply','--reverse','--whitespace=nowarn',str(forward))
   for path in changed:
    if sha(scratch/path)!=old[path]:fail('reverse application SHA mismatch '+path)
   git(scratch,'apply','--whitespace=nowarn',str(forward))
   git(scratch,'apply','--check','--whitespace=nowarn',str(backward))
   git(scratch,'apply','--whitespace=nowarn',str(backward))
   for path in changed:
    if sha(scratch/path)!=old[path]:fail('separate rollback SHA mismatch '+path)
 print('PASS original official 26935 full-index forward and reverse and independent rollback at core.abbrev 7/12/40, fuzz=0')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
