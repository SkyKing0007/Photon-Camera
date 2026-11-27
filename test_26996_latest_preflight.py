#!/usr/bin/env python3
"""Replay original 26995 tests only in exact isolated historical fixtures. Never build an old APK."""
import pathlib,subprocess,sys,tempfile,shutil,os
import build_26996_incremental as b
R=b.R

def run(t,*args):subprocess.run([sys.executable,'-S',*map(str,args)],cwd=t,check=True)

def historical(t,preflight=True):
 for p in R.iterdir():
  if p.is_file() and not p.is_symlink() and p.suffix!='.apk':shutil.copy2(p,t/p.name)
  elif p.is_dir() and (p.name in ('.github','26985_host_fixtures','26986_host_fixtures') or p.name in tuple('handoff_payload_'+str(n) for n in (26935,26975,26983,26989,26991,26992,26993,26994,26995))):shutil.copytree(p,t/p.name)
 subprocess.run(['git','init','-q',str(t)],check=True)
 shutil.copytree(b.BASE/'app',t/'app')
 oldwork=t/'.photon_26995_work';oldwork.mkdir();shutil.copytree(b.BASE/'app',oldwork/'candidate_26995'/'app')
 patch=t/'26995_ROLLBACK_FULLINDEX.patch';cmd=['git','apply','--whitespace=nowarn'];subprocess.run(cmd+['--check',str(patch)],cwd=t,check=True);subprocess.run(cmd+[str(patch)],cwd=t,check=True)
 old=b.parse(R/'26995_BASE_26994_FULL_APP.sha256');assert b.scan(t)==old
 shutil.copytree(t/'app',oldwork/'authority_26994'/'app')
 if preflight:
  run(t,'test_26995_latest_preflight.py')
 # Original exact live 26995 regressions, including 26992/26991 processing, owner and Spektra.
 (t/'photon_26995_outputs').mkdir(exist_ok=True);shutil.rmtree(t/'app');shutil.copytree(b.BASE/'app',t/'app');run(t,'build_26995_incremental.py','regress')
 assert b.scan(t)==b.parse(R/'26996_BASE_26995_FULL_APP.sha256') and b.scan(oldwork/'authority_26994')==old

if __name__=='__main__':
 b.exact(b.BASE,'26996_BASE_26995_FULL_APP.sha256','actual latest 26995 authority');b.exact(R,'26996_BASE_26995_FULL_APP.sha256','actual 26995 live baseline');b.exact(b.CAND,'26996_EXPECTED_FULL_APP.sha256','frozen 26996 successor')
 with tempfile.TemporaryDirectory(prefix='26996-exact-26995-history-') as td:historical(pathlib.Path(td))
 b.exact(b.BASE,'26996_BASE_26995_FULL_APP.sha256','actual 26995 unchanged');b.exact(R,'26996_BASE_26995_FULL_APP.sha256','live baseline unchanged');b.exact(b.CAND,'26996_EXPECTED_FULL_APP.sha256','frozen successor unchanged')
 print('PASS original 26995 preflight and runtime regressions on exact historical inputs; no previous APK rebuild')
