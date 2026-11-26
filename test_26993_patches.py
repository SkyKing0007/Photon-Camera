#!/usr/bin/env python3
"""Full-index deterministic forward/rollback with isolated git root and original silent parent skip regression."""
import argparse,importlib.util,pathlib,shutil,subprocess,tempfile,re
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26993_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--frozen',action='store_true');p.add_argument('--live',action='store_true');o=p.parse_args();assert sum((o.payload,o.frozen,o.live))==1
forward=R/'26993_FORWARD_FULLINDEX.patch';reverse=R/'26993_ROLLBACK_FULLINDEX.patch'
changed,base,expected=b.scope()
for patch in (forward,reverse):
 s=patch.read_bytes();paths=re.findall(rb'^diff --git a/(app/.*?) b/app/.*$',s,re.M)
 assert len(paths)==len(set(paths))==b.NCHANGE and set(x.decode() for x in paths)==changed
 assert len(re.findall(rb'^index [0-9a-f]{40}\.\.[0-9a-f]{40}(?: [0-9]+)?$',s,re.M))==b.NCHANGE
 assert b'a/candidate/app/' not in s and b'b/base/app/' not in s
if o.frozen:
 b.exact(b.BASE,'26993_BASE_26992_FULL_APP.sha256','patch base');b.exact(b.CAND,'26993_EXPECTED_FULL_APP.sha256','patch expected')
 with tempfile.TemporaryDirectory(prefix='26993patch_') as td:
  t=pathlib.Path(td);outer=t/'parent';outer.mkdir();subprocess.run(['git','init','-q',str(outer)],check=True)
  nested=outer/'.photon_26993_work'/'nested';nested.mkdir(parents=True)
  for rel in changed:dest=nested/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b.BASE/rel,dest)
  for extra in (['--check'],[]):subprocess.run(['git','apply','--whitespace=nowarn',*extra,str(forward)],cwd=nested,check=True)
  assert all(b.sha(nested/rel)==base[rel] for rel in changed),'historical parent silent-skip regression not reproduced'
  t=t/'isolated';t.mkdir();subprocess.run(['git','init','-q',str(t)],check=True);shutil.copytree(b.BASE/'app',t/'app')
  for abbrev in (7,12,40):
   for name,patch,manifest in [('forward',forward,'26993_EXPECTED_FULL_APP.sha256'),('rollback',reverse,'26993_BASE_26992_FULL_APP.sha256')]:
    cmd=['git','-c',f'core.abbrev={abbrev}','apply','--whitespace=nowarn']
    subprocess.run(cmd+['--check',str(patch)],cwd=t,check=True);subprocess.run(cmd+[str(patch)],cwd=t,check=True);b.exact(t,manifest,name+f' exact SHA abbrev={abbrev}')
  target=t/'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java';target.write_bytes(target.read_bytes()+b'\n// NEGATIVE-only test\n')
  try:b.exact(t,'26993_BASE_26992_FULL_APP.sha256','negative protected source')
  except RuntimeError:pass
  else:raise AssertionError('protected mutation unexpectedly accepted')
 print('PASS byte-exact forward/rollback and original parent silent-skip / protected mutation regressions')
elif o.live:b.exact(R,'26993_EXPECTED_FULL_APP.sha256','patch live source')
else:print('PASS exact full-index patch metadata and payload scope')
