#!/usr/bin/env python3
"""Run exact 26923 seal and prove actual failures on tampered inputs."""
from pathlib import Path
import hashlib, shutil, subprocess, tempfile
R=Path(__file__).resolve().parent
rows=(R/'26923_HANDOFF_HASHES.sha256').read_text().splitlines()
assert len(rows)>=25
paths={}
for line in rows:
 h,p=line.split('  ',1)
 assert len(h)==64 and p not in paths and '..' not in Path(p).parts
 contents=(R/p).read_bytes()
 assert hashlib.sha256(contents).hexdigest()==h,p
 paths[p]=contents
assert 'build_26923_incremental.py' in paths
assert '.github/workflows/build-26923-change-aware.yml' in paths
assert 'compile_26923_hr_spirv.sh' in paths
assert 'test_26923_patch_proof.py' in paths
assert 'test_26923_workflow_refs.py' in paths
assert 'test_26923_shader_contract.py' in paths
assert '26923_EXPECTED_ACTION_EXECUTABLES.txt' in paths
with tempfile.TemporaryDirectory(prefix='p26923_seal_mutations_') as tmp:
 d=Path(tmp)
 for path,contents in paths.items():
  f=d/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(contents)
 shutil.copy2(R/'26923_HANDOFF_HASHES.sha256',d/'26923_HANDOFF_HASHES.sha256')
 def seal():
  return subprocess.run(['python3','-S','build_26923_incremental.py','seal'],cwd=d,capture_output=True,text=True)
 baseline=seal()
 assert baseline.returncode==0,baseline.stderr+baseline.stdout
 cases=[
  'handoff_payload_26923/app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp',
  'handoff_payload_26923/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
  '26923_CHANGED_RUNTIME_ALLOWLIST.txt',
  '26923_EXPECTED_FULL_APP.sha256',
  'compile_26923_hr_spirv.sh',
  'test_26923_workflow_refs.py',
  '26923_EXPECTED_ACTION_EXECUTABLES.txt',
  '.github/workflows/build-26923-change-aware.yml',
  'TRIGGER_26923.txt',
 ]
 for path in cases:
  f=d/path
  original=f.read_bytes()
  f.write_bytes(original+b'BLOCKED_SOURCE_MUTATION')
  result=seal()
  assert result.returncode!=0 and '26923 BLOCKED' in result.stderr,(path,result.stdout,result.stderr)
  f.write_bytes(original)
  assert seal().returncode==0,path
 # A newly invented Python reference must be rejected even if the altered
 # workflow is re-SHA-sealed (the exact failure that escaped 26923 V1).
 wf=d/'.github/workflows/build-26923-change-aware.yml'
 raw=wf.read_bytes()
 mutated=raw.replace(b'verify_26904_v3_safety.py',b'verify_26904_v3_safety_MISSING.py',1)
 assert mutated!=raw
 wf.write_bytes(mutated)
 seal_file=d/'26923_HANDOFF_HASHES.sha256'
 original_seal=seal_file.read_bytes()
 marker=b'  .github/workflows/build-26923-change-aware.yml'
 sha_line=hashlib.sha256(mutated).hexdigest().encode()+marker
 rows=original_seal.splitlines()
 assert any(marker in line for line in rows)
 resealed=b'\n'.join(sha_line if marker in line else line for line in rows)+b'\n'
 seal_file.write_bytes(resealed)
 negative=seal()
 assert negative.returncode!=0 and 'executable reference inventory' in negative.stderr,negative.stderr
 wf.write_bytes(raw);seal_file.write_bytes(original_seal)
 assert seal().returncode==0,'resealed reference mutation not restored'
 # Missing newly-added source is prohibited, regardless of unchanged files.
 f=d/cases[0];f.unlink()
 rejected=seal()
 assert rejected.returncode!=0 and '26923 BLOCKED' in rejected.stderr,rejected.stderr
print('PASS 26923 sealed manifest and 11 fail-closed mutation/missing-file + resealed workflow reference negatives')
