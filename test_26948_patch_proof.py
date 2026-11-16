#!/usr/bin/env python3
"""Real original 26947 2054-file authority and 10-file full-index reversible patch (7/12/40)."""
import argparse,pathlib,re,shutil,subprocess,tempfile,sys
from build_26948_incremental import R,BASE,scope,sha,fail

def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--payload',action='store_true');a.add_argument('--authority-dir');args=a.parse_args()
 ch,old,new=scope();forward=R/'26948_FORWARD_FULLINDEX.patch';rollback=R/'26948_ROLLBACK_FULLINDEX.patch'
 for p in (forward,rollback):
  s=p.read_text();names=re.findall(r'^diff --git a/(.*?) b/(.*?)$',s,re.M)
  if len(names)!=len(ch) or set(x for x,y in names)!=ch or any(x!=y for x,y in names):fail('unauthorized patch targets')
  if len(re.findall(r'^index [0-9a-f]{40}\.\.[0-9a-f]{40} 100644$',s,re.M))!=len(ch):fail('40hex indexes missing')
  if 'GIT binary patch' in s or 'rename from' in s:fail('binary/rename patch')
 base=pathlib.Path(args.authority_dir) if args.authority_dir else BASE
 if not base.is_dir():
  print('PASS syntax strict 26948 10-file patch; exact published base must be checked after Actions fetch');return
 for p in ch:
  if sha(base/p)!=old[p]:fail('wrong 26947 compiled base '+p)
 for ab in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='p26948_forward_') as d:
   d=pathlib.Path(d)
   for p in ch:
    dest=d/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/p,dest)
   for patch,want in ((forward,new),(rollback,old),(forward,new)):
    cmd=['git','-c',f'core.abbrev={ab}','apply','--whitespace=error'];subprocess.run(cmd+['--check',str(patch)],cwd=d,check=True,capture_output=True)
    subprocess.run(cmd+[str(patch)],cwd=d,check=True,capture_output=True)
    for p in ch:
     if sha(d/p)!=want[p]:fail('patch replay mismatch '+p)
   if subprocess.run(['git','apply','--check',str(forward)],cwd=d,capture_output=True).returncode==0:fail('stale patch second replay accepted')
 print('PASS 26948 real 26947 published candidate 10-source forward/rollback/forward at git index 7/12/40, stale replay rejected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
