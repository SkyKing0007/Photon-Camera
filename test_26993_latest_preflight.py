#!/usr/bin/env python3
"""Re-execute the exact successful 26992 latest-preflight against its original sealed versions.
Use only the latest published runtime plus its exact full-index rollback in an isolated historical fixture.
No historical test altered and no historical source installed into the live checkout.
"""
import pathlib,subprocess,sys,tempfile,shutil,os
import build_26993_incremental as b
R=b.R
if __name__=='__main__':
 before=b.exact(b.BASE,'26993_BASE_26992_FULL_APP.sha256','actual latest 26992 authority');b.exact(R,'26993_BASE_26992_FULL_APP.sha256','actual 26992 live baseline');b.exact(b.CAND,'26993_EXPECTED_FULL_APP.sha256','frozen 26993 successor')
 with tempfile.TemporaryDirectory(prefix='26993-exact-26992-history-') as td:
  t=pathlib.Path(td);subprocess.run(['git','init','-q',str(t)],check=True)
  # Copy original root scripts/manifests to preserve their __file__-relative roots.
  for p in R.iterdir():
   if p.is_file() and not p.is_symlink():shutil.copy2(p,t/p.name)
  # Historical payloads and fixtures are read-only test inputs, never new runtime sources.
  for p in R.iterdir():
   if p.is_dir() and (p.name in ('handoff_payload_26935','handoff_payload_26975','handoff_payload_26983','handoff_payload_26989','handoff_payload_26991','handoff_payload_26992','26985_host_fixtures','26986_host_fixtures','.github')):
    shutil.copytree(p,t/p.name)
  shutil.copytree(b.BASE/'app',t/'app')
  oldmanifest=b.parse(R/'26992_BASE_26991_FULL_APP.sha256');assert b.parse(R/'26992_EXPECTED_FULL_APP.sha256')==before
  patch=R/'26992_ROLLBACK_FULLINDEX.patch';cmd=['git','apply','--whitespace=nowarn'];subprocess.run(cmd+['--check',str(patch)],cwd=t,check=True);subprocess.run(cmd+[str(patch)],cwd=t,check=True)
  assert b.scan(t)==oldmanifest
  oldwork=t/'.photon_26992_work';oldwork.mkdir();shutil.copytree(t/'app',oldwork/'authority_26991'/'app');shutil.copytree(b.BASE/'app',oldwork/'candidate_26992'/'app')
  subprocess.run([sys.executable,'-S',str(t/'test_26992_latest_preflight.py')],cwd=t,check=True)
  assert b.scan(t)==oldmanifest and b.scan(oldwork/'authority_26991')==oldmanifest and b.scan(oldwork/'candidate_26992')==before
 b.exact(b.BASE,'26993_BASE_26992_FULL_APP.sha256','actual latest authority unchanged');b.exact(R,'26993_BASE_26992_FULL_APP.sha256','live baseline unchanged');b.exact(b.CAND,'26993_EXPECTED_FULL_APP.sha256','frozen successor unchanged')
 print('PASS original 26992 latest-preflight unchanged, exact historic rollback fixture, new live source never rolled back')
