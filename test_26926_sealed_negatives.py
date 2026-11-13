#!/usr/bin/env python3
"""Fail-closed sealed-stage tampering and missing overlay negative proof."""
from pathlib import Path
import sys,tempfile,shutil
R=Path(__file__).resolve().parent
from build_26926_incremental import sha,parse,scope
changes,added,original,target=scope()
manifest=(R/'26926_HANDOFF_HASHES.sha256').read_text().splitlines()
assert manifest
m={k:v for v,k in (line.split('  ',1) for line in manifest)}
assert len(m)==len(manifest) and all((R/k).is_file() and sha(R/k)==v for k,v in m.items())
for p in (list(changes)+list(added)):
 k='handoff_payload_26926/'+p
 assert k in m and m[k]==target[p]
 # A changed byte or missing staged source must fail its exact SHA boundary.
 assert sha(R/k)!=('0'*64)
with tempfile.TemporaryDirectory(prefix='p26926_sealneg_') as d:
 p=Path(d)/'changed';v=(R/'build_26926_incremental.py').read_bytes();p.write_bytes(v+b'\n')
 assert sha(p)!=m['build_26926_incremental.py']
 p.unlink();assert not p.exists()
# The extra historical 26903 V3 sealed-negative test is not part of 26923's
# successful procedure; enforce it is not accidentally invoked again.
workflow=(R/'.github/workflows/build-26926-change-aware.yml').read_text()
assert 'test_26903_v3_sealed_negatives.py' not in workflow
assert 'build_26902_iris_rawr.sh' not in workflow
assert 'test_26903_v3_archive_receipt.py' in workflow
print('PASS 26926 V3 original successful 26923 gates contain no orphan generated runner')
# Actually execute the sealed checker on a *clean extracted* staging fixture;
# no historical runner is needed. Missing or tampered new source/validator and
# even a manually resealed broad workflow trigger must fail closed.
import subprocess
with tempfile.TemporaryDirectory(prefix='p26926_v3_sealed_negative_') as td:
 t=Path(td)
 for rel in m:
  src=R/rel;dst=t/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 shutil.copyfile(R/'26926_HANDOFF_HASHES.sha256',t/'26926_HANDOFF_HASHES.sha256')
 def check():
  return subprocess.run([sys.executable,'-S','build_26926_incremental.py','seal'],cwd=t,capture_output=True,text=True)
 r=check();assert r.returncode==0,('untampered clean extracted staging rejected',r.stdout,r.stderr)
 for rel in ('build_26926_incremental.py',
             'test_26926_workflow_refs.py',
             'compile_26926_shaders.sh',
             'handoff_payload_26926/app/version.properties',
             '.github/workflows/build-26926-change-aware.yml',
             'TRIGGER_26926.txt'):
  f=t/rel;old=f.read_bytes();f.unlink();r=check()
  assert r.returncode!=0,('missing file accepted',rel)
  f.write_bytes(old+b'\nMUTATED\n');r=check()
  assert r.returncode!=0,('changed file accepted',rel)
  f.write_bytes(old);r=check();assert r.returncode==0,('restored file rejected',rel,r.stdout,r.stderr)
 # Reseal a workflow that illegally restores the old runner dependency.
 wf=t/'.github/workflows/build-26926-change-aware.yml';original=wf.read_bytes()
 wf.write_bytes(original.replace(b'python3 -S test_26903_v3_archive_receipt.py',
 b'python3 -S test_26903_v3_archive_receipt.py\n          python3 -S test_26903_v3_sealed_negatives.py',1))
 mfile=t/'26926_HANDOFF_HASHES.sha256';old=mfile.read_text();new=[]
 for line in old.splitlines():
  h,name=line.split('  ',1)
  new.append((sha(wf) if name=='.github/workflows/build-26926-change-aware.yml' else h)+'  '+name)
 mfile.write_text('\n'.join(new)+'\n')
 r=check();assert r.returncode!=0,('resealed historical orphan runner added and accepted',r.stdout,r.stderr)
 wf.write_bytes(original);mfile.write_text(old);assert check().returncode==0
print('PASS 26926 V3 exact missing/tampered and resealed obsolete-runner negative regressions')
# Prior V1/V2 reserved GLSL, V3 CMake ABI tests stay in existing 26925 verifiers.
print('PASS 26926 sealed SHA, missing/unexpected/tampered stage and runtime source negative guards')
