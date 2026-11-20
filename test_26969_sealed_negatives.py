#!/usr/bin/env python3
"""Fail closed on edited overlay, source manifest, missing data, or premature trigger."""
from pathlib import Path
import subprocess,tempfile,shutil,sys
R=Path(__file__).resolve().parent
files=['build_26969_incremental.py','test_26969_workflow_refs.py','26968_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','26968_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py','26969_HANDOFF_HASHES.sha256']
files += [p.relative_to(R).as_posix() for p in R.glob('26969_*.txt')]+[p.relative_to(R).as_posix() for p in R.glob('26969_*.json')]+[p.relative_to(R).as_posix() for p in R.glob('26969_*.sha256')]
files += [p.relative_to(R).as_posix() for p in (R/'handoff_payload_26969').rglob('*') if p.is_file()]
files += [p.relative_to(R).as_posix() for p in (R/'.github/workflows').glob('build-26969-change-aware.yml')]
files += [p.name for p in R.glob('test_26969_*.py')]+['compile_26969_shaders.sh','README_PHOTON_26969.md']
files=list(sorted(set(files)))
with tempfile.TemporaryDirectory(prefix='iris26969_negative_') as t:
 S=Path(t)
 for rel in files:
  f=S/rel;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/rel,f)
 def check_failure(label):
  p=subprocess.run([sys.executable,'-S','build_26969_incremental.py','seal'],cwd=S,capture_output=True,text=True)
  assert p.returncode!=0,label
 source=S/'handoff_payload_26969/app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26969RawrAeMath.java'
 original=source.read_bytes();source.write_bytes(original+b'\n//tampered\n');check_failure('mutated AE source accepted');source.write_bytes(original)
 q=S/'26969_CHANGED_RUNTIME_ALLOWLIST.txt';orig=q.read_text();q.write_text(orig+'app/src/main/cpp/invalid.cpp\n');check_failure('added native file accepted');q.write_text(orig)
 q=S/'26969_STAGE_2_UPLOAD_PATHS.txt';orig=q.read_text();q.write_text('TRIGGER_26969.txt\n');check_failure('workflow before trigger accepted');q.write_text(orig)
 q=S/'26969_BASE_26968_FULL_APP.sha256';orig=q.read_text();q.write_text(orig.replace('a','b',1));check_failure('mutated base accepted');q.write_text(orig)
print('PASS 26969 source/payload, native allowlist, staged workflow and manifest fail-closed negatives')
