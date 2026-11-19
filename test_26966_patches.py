#!/usr/bin/env python3
"""Full-index patch proof: forward and rollback at core.abbrev 7/12/40, fuzz=0."""
import argparse,hashlib,pathlib,shutil,subprocess,tempfile
from build_26966_incremental import scope,sha,fail
R=pathlib.Path(__file__).resolve().parent

def run(args,cwd,ok=True):
 p=subprocess.run(args,cwd=cwd,capture_output=True,text=True)
 if (p.returncode==0)!=ok:fail('26966 patch proof failed cmd='+repr(args)+' stdout='+p.stdout[:200]+' err='+p.stderr[:200])

def check():
 changed,a,b=scope()
 for size in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='photon_26966_patch_') as td:
   root=pathlib.Path(td)
   for path in changed:
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
    # use original compiled bytes via currently-sealed bsdiff-inverse fixture derived from patch!
    shutil.copy2(R/'handoff_payload_26966'/path,p)
   for path in changed: assert sha(root/path)==b[path]
   reverse=R/'26966_ROLLBACK_FULLINDEX.patch';forward=R/'26966_FORWARD_FULLINDEX.patch'
   run(['git','-c',f'core.abbrev={size}','apply','--check','--whitespace=nowarn',str(reverse)],root)
   run(['git','-c',f'core.abbrev={size}','apply','--whitespace=nowarn',str(reverse)],root)
   for path in changed:
    if sha(root/path)!=a[path]:fail(f'rollback SHA mismatch at abbrev {size} {path}')
   run(['git','-c',f'core.abbrev={size}','apply','--check','--whitespace=nowarn',str(forward)],root)
   run(['git','-c',f'core.abbrev={size}','apply','--whitespace=nowarn',str(forward)],root)
   for path in changed:
    if sha(root/path)!=b[path]:fail(f'forward SHA mismatch at abbrev {size} {path}')
   # Negative: attempting duplicate application must fail cleanly (no fuzz).
   run(['git','-c',f'core.abbrev={size}','apply','--check','--whitespace=nowarn',str(forward)],root,ok=False)
 print('PASS 26966 full-index deterministic forward/rollback 7/12/40, zero fuzz; negative duplicate rejected')
if __name__=='__main__':check()
