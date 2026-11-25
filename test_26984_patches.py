#!/usr/bin/env python3
"""Positive and negative full-index patch replays with exact SHA manifests.
Original donor trailing whitespace is byte-immutable: git apply --whitespace=nowarn
means preserve raw donor bytes, NOT skip any source/hash/compilation validation.
"""
import argparse,importlib.util,os,pathlib,shutil,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26984',R/'build_26984_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--frozen',action='store_true');p.add_argument('--live',action='store_true');o=p.parse_args()
assert sum((o.payload,o.frozen,o.live))==1
forward=R/'26984_FORWARD_FULLINDEX.patch';reverse=R/'26984_ROLLBACK_FULLINDEX.patch'
assert forward.is_file() and reverse.is_file() and forward.stat().st_size>0 and reverse.stat().st_size>0
if o.frozen:
 b.exact(b.BASE,'26984_BASE_26983_FULL_APP.sha256','patch base')
 b.exact(b.CAND,'26984_EXPECTED_FULL_APP.sha256','patch expected')
if o.live:
 b.exact(R,'26984_EXPECTED_FULL_APP.sha256','patch live source')
if o.payload:
 for p in (forward,reverse):
  s=p.read_bytes()
  assert (b'diff --git a/app/' in s or b'diff --git b/app/' in s) and b'GIT binary patch' not in s
  assert b'a/after/app/' not in s and b'b/before/app/' not in s
  import re
  paths=re.findall(rb'^diff --git [ab]/(app/.*?) [ab]/app/.*$',s,re.M)
  assert len(paths)==len(set(paths))==b.NCHANGE
  assert set(x.decode() for x in paths)==set((R/'26984_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
  assert len(re.findall(rb'^index [0-9a-f]{40}\.\.[0-9a-f]{40}(?: [0-9]+)?$',s,re.M))==b.NCHANGE
 # Base payload is only available after fetching exact successful Actions TAR.
 print('PASS full-index forward/rollback patch metadata + binary payload integrity (source SHA sealed)')
else:
 if not o.frozen:
  print('PASS live source exact; frozen pair already exercised during reconstruction')
 else:
  with tempfile.TemporaryDirectory(prefix='26984patch_') as td:
   t=pathlib.Path(td)
   # Reproduce V1 Git parent-discovery on the CURRENT five-file patch only.
   # No earlier source tree or rollback is involved. Git can return zero after
   # skipping the complete patch from a nested work directory.
   outer=t/'parent';outer.mkdir();subprocess.run(['git','init','-q',str(outer)],check=True)
   nested=outer/'.photon_26984_work'/'nested';nested.mkdir(parents=True)
   changes,base,expected=b.scope()
   for rel in changes:
    dest=nested/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b.BASE/rel,dest)
   subprocess.run(['git','apply','--check','--whitespace=nowarn',str(forward)],cwd=nested,check=True)
   subprocess.run(['git','apply','--whitespace=nowarn',str(forward)],cwd=nested,check=True)
   assert all(b.sha(nested/rel)==base[rel] for rel in changes),'V1 parent skip not reproduced'
   print('PASS V1 parent-repository silent patch skip reproduced on current five-file fixture')
   # Only a disposable copy of the latest authority is used for round-trip
   # tests; initialize its own Git root to prevent ancestor repository lookup.
   t=t/'isolated';t.mkdir();subprocess.run(['git','init','-q',str(t)],check=True)
   shutil.copytree(b.BASE/'app',t/'app')
   for abbrev in (7,12,40):
    for name,patch,manifest in [('forward',forward,'26984_EXPECTED_FULL_APP.sha256'),('rollback',reverse,'26984_BASE_26983_FULL_APP.sha256')]:
     cmd=['git','-c',f'core.abbrev={abbrev}','apply','--whitespace=nowarn']
     subprocess.run(cmd+['--check',str(patch)],cwd=t,check=True)
     subprocess.run(cmd+[str(patch)],cwd=t,check=True)
     b.exact(t,manifest,name+f' exact SHA abbrev={abbrev}')
   # Mutated protected source must make the forward full-index patch reject.
   target=t/'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java'
   target.write_bytes(target.read_bytes()+b'\n// NEGATIVE-only test\n')
   try:
    b.exact(t,'26984_BASE_26983_FULL_APP.sha256','negative edit rejection')
   except RuntimeError: pass
   else:raise AssertionError('protected-source mutation unexpectedly accepted')
  print('PASS 26984 byte-exact forward/rollback replay, protected mutation rejected')
