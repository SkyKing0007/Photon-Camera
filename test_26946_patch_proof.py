#!/usr/bin/env python3
"""Exact original compiled 26945 source, 26946 forward/rollback full-index at abbrev 7/12/40."""
import argparse,pathlib,re,shutil,subprocess,tempfile,sys
from build_26946_incremental import R,BASE,scope,sha,fail

def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--payload',action='store_true');a.add_argument('--authority-dir');args=a.parse_args()
 ch,old,new=scope();forward=R/'26946_FORWARD_FULLINDEX.patch';rollback=R/'26946_ROLLBACK_FULLINDEX.patch'
 for p in (forward,rollback):
  s=p.read_text();names=re.findall(r'^diff --git a/(.*?) b/(.*?)$',s,re.M)
  if len(names)!=len(ch) or set(x for x,y in names)!=ch or any(x!=y for x,y in names):fail('unauthorized patch target')
  if len(re.findall(r'^index [0-9a-f]{40}\.\.[0-9a-f]{40} 100644$',s,re.M))!=len(ch):fail('full 40-hex index missing')
  if 'GIT binary patch' in s or 'rename from ' in s:fail('binary/rename patch unexpected')
 base=pathlib.Path(args.authority_dir) if args.authority_dir else BASE
 if not base.is_dir():
  print('PASS 26946 sealed 3-file full-index forward/rollback syntax, awaiting compiled 26945 authority');return
 for p in ch:
  if not (base/p).is_file() or sha(base/p)!=old[p]:fail('actual prior successful compiled source missing/mismatched '+p)
 for ab in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='26946_patch_') as d:
   d=pathlib.Path(d)
   for p in ch:
    out=d/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/p,out)
   for patch,want in ((forward,new),(rollback,old)):
    args=['git','-c',f'core.abbrev={ab}','apply','--whitespace=error']
    subprocess.run(args+['--check',str(patch)],cwd=d,check=True,capture_output=True)
    subprocess.run(args+[str(patch)],cwd=d,check=True,capture_output=True)
    for p in ch:
     if sha(d/p)!=want[p]:fail('patch byte mismatch '+p+' '+str(ab))
   # A second forward patch applied to an already patched candidate must fail.
   subprocess.run(['git','apply','--check',str(forward)],cwd=d,check=True,capture_output=True)
   subprocess.run(['git','apply',str(forward)],cwd=d,check=True,capture_output=True)
   r=subprocess.run(['git','apply','--check',str(forward)],cwd=d,capture_output=True)
   if r.returncode==0:fail('already patched/stale source accepted forward replay')
 print('PASS 26946 forward/rollback exact original 26945 source SHA at core.abbrev 7/12/40 and stale-patch negative')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
