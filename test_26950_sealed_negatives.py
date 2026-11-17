#!/usr/bin/env python3
"""Historical-type hostile source, workflow, shader, seal and trigger mutants."""
from pathlib import Path
import tempfile,shutil,subprocess,sys
from build_26950_incremental import R,STAGE1_FILES,seal
seal()
files=set(STAGE1_FILES)|{'26950_HANDOFF_HASHES.sha256','TRIGGER_26950.txt','.github/workflows/build-26950-change-aware.yml'}
files.update('handoff_payload_26950/'+x for x in (R/'26950_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
checks=[('26950_EXPECTED_FULL_APP.sha256','append'),('26950_CHANGED_RUNTIME_ALLOWLIST.txt','append'),
 ('26950_FORWARD_FULLINDEX.patch','append'),('26950_ROLLBACK_FULLINDEX.patch','append'),
 ('replay_26950_inherited_26949_glsl.py','append'),('compile_26950_shaders.sh','append'),
 ('test_26950_source.py','append'),('test_26950_highlight.py','append'),('compile_26950_sdr_shaders.sh','append'),('26950_STAGE_1_UPLOAD_PATHS.txt','append'),
 ('TRIGGER_26950.txt','remove'),('.github/workflows/build-26950-change-aware.yml','append')]
checks += [('handoff_payload_26950/'+p,'append') for p in (R/'26950_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()]
for name,kind in checks:
 with tempfile.TemporaryDirectory(prefix='26950_negative_') as tmp:
  d=Path(tmp)
  for f in files:
   target=d/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,target)
  p=d/name
  if kind=='remove':p.unlink()
  else:p.write_bytes(p.read_bytes()+b'\nMUTATED\n')
  out=subprocess.run([sys.executable,'-S','build_26950_incremental.py','seal'],cwd=d,capture_output=True,text=True)
  if out.returncode==0 or '26950 BLOCKED' not in out.stderr:raise SystemExit('FAILED mutation rejection '+name+' '+out.stdout+' '+out.stderr)
print('PASS 26950 '+str(len(checks))+' sealed failures rejected')
