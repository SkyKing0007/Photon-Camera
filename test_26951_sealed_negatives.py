#!/usr/bin/env python3
"""Genuine isolated mutations: reject missing/stale/injected source, script, shader, workflow or trigger."""
import pathlib,tempfile,shutil,subprocess,sys
from build_26951_incremental import R,STAGE1_FILES,seal
seal()
files=set(STAGE1_FILES)|{'26951_HANDOFF_HASHES.sha256','TRIGGER_26951.txt','.github/workflows/build-26951-change-aware.yml'}
files.update('handoff_payload_26951/'+p for p in (R/'26951_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
checks=[('26951_EXPECTED_FULL_APP.sha256','append'),('26951_BASE_26949_FULL_APP.sha256','append'),
 ('26951_CHANGED_RUNTIME_ALLOWLIST.txt','append'),('26951_FORWARD_FULLINDEX.patch','append'),
 ('26951_ROLLBACK_FULLINDEX.patch','append'),('replay_26951_inherited_26949_glsl.py','append'),
 ('compile_26951_shaders.sh','append'),('compile_26951_sdr_shaders.sh','append'),
 ('test_26951_source.py','append'),('test_26951_highlight.py','append'),
 ('test_26951_descriptor_abi.py','append'),('26951_STAGE_1_UPLOAD_PATHS.txt','append'),
 ('26951_EXPECTED_ACTION_EXECUTABLES.txt','append'),('TRIGGER_26951.txt','remove'),
 ('.github/workflows/build-26951-change-aware.yml','append')]
checks += [('handoff_payload_26951/'+p,'append') for p in (R/'26951_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()]
for target,op in checks:
 with tempfile.TemporaryDirectory(prefix='26951_sealed_negative_') as folder:
  temp=pathlib.Path(folder)
  for n in files:
   p=temp/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
  p=temp/target
  if op=='remove':p.unlink()
  else:p.write_bytes(p.read_bytes()+b'\nMUTATED\n')
  ret=subprocess.run([sys.executable,'-S','build_26951_incremental.py','seal'],cwd=temp,capture_output=True,text=True)
  if ret.returncode==0 or '26951 BLOCKED' not in ret.stderr:raise SystemExit('FAILED 26951 negative: '+target+' '+ret.stdout+' '+ret.stderr)
print(f'PASS 26951 {len(checks)} independent isolated seal-source/workflow/compiler/trigger negative regressions')
