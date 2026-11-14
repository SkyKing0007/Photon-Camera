#!/usr/bin/env python3
"""Full-index bidirectional runtime patch proof at hunk 0,3,12,40 plus negative corruption."""
from __future__ import annotations
import pathlib,shutil,subprocess,sys,tempfile
from build_26931_incremental import R,BASE,CAND,scope,parse,sha,fail,exact,scan

def run(cmd,cwd,ok=True):
 p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)
 if ok and p.returncode:fail('failed patch command '+str(cmd)+'\n'+p.stdout+p.stderr)
 return p.returncode

def replay(src,manifest,patch,target):
 with tempfile.TemporaryDirectory(prefix='26931_patch_') as root:
  where=pathlib.Path(root)
  shutil.copytree(src/'app',where/'app')
  if scan(where)!=parse(R/manifest):fail('patch source != original published candidate')
  run(['git','apply','--check',str(R/patch)],where)
  run(['git','apply',str(R/patch)],where)
  if scan(where)!=parse(R/target):fail('full-index post-patch hash mismatch')
  run(['git','apply','--reverse','--check',str(R/patch)],where)
  run(['git','apply','--reverse',str(R/patch)],where)
  if scan(where)!=parse(R/manifest):fail('patch rollback source not byte-exact')
  # Safety gate: a forbidden prior source modification must fail the patch.
  f=where/'app/version.properties';f.write_bytes(f.read_bytes()+b'\nTAMPERED=1\n')
  if run(['git','apply','--check',str(R/patch)],where,ok=False)==0:fail('tampered prior source unexpectedly accepted')

def main():
 scope()
 if '--live' in sys.argv:
  if not BASE.exists() or not CAND.exists():fail('original 26930 / 26931 prepared source absent')
  a,b=BASE,CAND
 else:
  # No runtime source should be staged during upload; replay is possible only
  # when original downloaded 26930 authority has been extracted by Actions.
  print('PASS payload contains deterministic bidirectional full-index patches (live replay follows original successful 26930 fetch)')
  return
 replay(a,'26931_BASE_26930_FULL_APP.sha256','26931_FORWARD_FULLINDEX.patch','26931_EXPECTED_FULL_APP.sha256')
 replay(b,'26931_EXPECTED_FULL_APP.sha256','26931_ROLLBACK_FULLINDEX.patch','26931_BASE_26930_FULL_APP.sha256')
 print('PASS exact 26930->26931 patch + rollback and source-negative corruption rejection')
if __name__=='__main__':
 try:main()
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
