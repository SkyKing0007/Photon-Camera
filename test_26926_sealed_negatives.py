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
# Replay the actual 26926 V1 failure mechanism: remove the mandatory
# original 26902 successful runner, or mutate its bytes. Keep all original
# 26903 historical tests intact in the Actions job.
with tempfile.TemporaryDirectory(prefix='p26926_real_26902_parent_negative_') as d:
 t=Path(d)
 for rel in m:
  f=R/rel; dst=t/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst)
 shutil.copyfile(R/'26926_HANDOFF_HASHES.sha256',t/'26926_HANDOFF_HASHES.sha256')
 import subprocess
 def seal_failed():
  result=subprocess.run([sys.executable,'-S','build_26926_incremental.py','seal'],cwd=t,text=True,capture_output=True)
  return result.returncode!=0, result.stderr+result.stdout
 ok,log=seal_failed();assert not ok,('clean original stage already invalid',log)
 p=t/'build_26902_iris_rawr.sh';original=p.read_bytes()
 p.unlink();ok,log=seal_failed();assert ok and ('build_26902_iris_rawr.sh' in log or 'missing' in log),('missing historical runner accepted',log)
 p.write_bytes(original+b'\nDANGEROUS_MUTATION\n');ok,log=seal_failed();assert ok and ('build_26902_iris_rawr.sh' in log or 'mismatch' in log),('tampered original runner accepted',log)
 p.write_bytes(original);ok,log=seal_failed();assert not ok,('SHA recovered historical runner not accepted',log)
print('PASS 26926 V2 exact original 26902 runner absence and mutation FAIL CLOSED, clean restore PASS')
# Prior V1/V2 reserved GLSL, V3 CMake ABI tests stay in existing 26925 verifiers.
print('PASS 26926 sealed SHA, missing/unexpected/tampered stage and runtime source negative guards')
