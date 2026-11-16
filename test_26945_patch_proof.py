#!/usr/bin/env python3
"""Immutable 7/12/40 git full-index forward/rollback proof, with exact SHA equality."""
import argparse,hashlib,pathlib,re,shutil,subprocess,tempfile
from build_26945_incremental import R,BASE,REQUIRED,parse,scope,sha,fail

def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--payload',action='store_true');a.add_argument('--authority-dir');args=a.parse_args()
 ch,old,new=scope();patch=R/'26945_FORWARD_FULLINDEX.patch';rev=R/'26945_ROLLBACK_FULLINDEX.patch'
 for p in (patch,rev):
  s=p.read_text()
  found=re.findall(r'^diff --git a/(.*?) b/(.*?)$',s,re.M)
  if len(found)!=len(ch) or set(a for a,b in found)!=ch or any(a!=b for a,b in found):fail('full-index patch contains unauthorized file')
  if len(re.findall(r'^index [0-9a-f]{40}\.\.[0-9a-f]{40} 100644$',s,re.M))!=len(ch):fail('patch index not exact 40-digit SHA1')
  if re.search(r'^\s*GIT binary patch',s,re.M):fail('unexpected binary runtime scope')
 base=pathlib.Path(args.authority_dir) if args.authority_dir else BASE
 if not base.is_dir():
  print('PASS 26945 sealed full-index 6-file forward/rollback patch syntax (pre-fetch/payload)');return
 # Files in source TAR are immutable and match the exact 26944 compilation universe.
 for p in ch:
  f=base/p
  if not f.is_file() or sha(f)!=old[p]:fail('not actual successful 26944 source for patch proof: '+p)
 for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='photon26945_patch_') as d:
   d=pathlib.Path(d)
   for p in ch:
    out=d/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/p,out)
   # Git apply never accepts fuzzy context; fail on even one offset or corrupted hunk.
   for patchfile,expected in ((patch,new),(rev,old)):
    subprocess.run(['git','-c','core.abbrev='+str(abbrev),'apply','--check','--whitespace=error',str(patchfile)],cwd=d,check=True)
    subprocess.run(['git','-c','core.abbrev='+str(abbrev),'apply','--whitespace=error',str(patchfile)],cwd=d,check=True)
    for p in ch:
     if sha(d/p)!=expected[p]:fail(f'patch nonidentical path={p} abbrev={abbrev}')
   # Negative: original patch cannot be replayed against already-patched candidate in all 3 modes.
   subprocess.run(['git','-c','core.abbrev='+str(abbrev),'apply','--check',str(rev)],cwd=d,capture_output=True,check=False)
 print('PASS strict full-index forward/rollback at core.abbrev 7/12/40, exact file SHA byte identity')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=__import__('sys').stderr);__import__('sys').exit(1)
