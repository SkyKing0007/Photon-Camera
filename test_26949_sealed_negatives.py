#!/usr/bin/env python3
"""Reject any staged file/hash/source/trigger tampering before fetching authority."""
import pathlib,tempfile,shutil,subprocess,sys
R=pathlib.Path(__file__).resolve().parent
from build_26949_incremental import seal,STAGE1_FILES

def run_neg(rel,operation):
 with tempfile.TemporaryDirectory(prefix='26949_seal_negative_') as d:
  root=pathlib.Path(d)
  files=set(STAGE1_FILES)|{'26949_HANDOFF_HASHES.sha256','TRIGGER_26949.txt','.github/workflows/build-26949-change-aware.yml'}
  files.update('handoff_payload_26949/'+x for x in (R/'26949_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
  for q in files:
   p=root/q;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/q,p)
  p=root/rel
  if operation=='remove':p.unlink()
  elif operation=='append':p.write_bytes(p.read_bytes()+b'\nNOT_ORIGINAL\n')
  else:raise ValueError(operation)
  r=subprocess.run([sys.executable,'-S','build_26949_incremental.py','seal'],cwd=root,capture_output=True,text=True)
  assert r.returncode!=0 and '26949 BLOCKED' in r.stderr,(rel,operation,r.stdout,r.stderr)
seal()
for q,op in [('handoff_payload_26949/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt','append'),
 ('handoff_payload_26949/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','append'),
 ('26949_EXPECTED_FULL_APP.sha256','append'),('26949_CHANGED_RUNTIME_ALLOWLIST.txt','append'),
 ('26949_FORWARD_FULLINDEX.patch','append'),('26949_STAGE_1_UPLOAD_PATHS.txt','append'),
 ('TRIGGER_26949.txt','remove'),('.github/workflows/build-26949-change-aware.yml','append')]:run_neg(q,op)
print('PASS 26949 sealed negatives: source/manifest/scope/patch/stage/trigger/workflow fail-closed')
