#!/usr/bin/env python3
"""26927 actual SHA sealed handoff reject missing/tampered stages and altered runtime scope."""
from pathlib import Path
import hashlib,sys,shutil,tempfile,subprocess
R=Path(__file__).resolve().parent
from build_26927_incremental import scope,sha
changes,added,original,target=scope()
assert len(changes)==4 and not added
manifest=(R/'26927_HANDOFF_HASHES.sha256').read_text().splitlines()
assert len(manifest)>15
listed={}
for row in manifest:
 h,name=row.split('  ',1);assert name not in listed and sha(R/name)==h;listed[name]=h
assert {n.removeprefix('handoff_payload_26927/') for n in listed if n.startswith('handoff_payload_26927/')}==changes
# Exercise exact builder seal against an actual copied three-stage package;
# no mutation touches the user's working tree or GitHub.
with tempfile.TemporaryDirectory(prefix='26927_hostile_') as t:
 home=Path(t)/'p';shutil.copytree(R,home,ignore=shutil.ignore_patterns('__pycache__','.photon_26927_work','photon_26927_outputs'))
 assert subprocess.run(['python3','-S','build_26927_incremental.py','seal'],cwd=home,capture_output=True).returncode==0
 attacks=[
  ('runtime_shader',next(p for p in listed if p.endswith('GlesIris26870PostAmazeChroma.kt'))),
  ('runtime_gl',next(p for p in listed if p.endswith('GlesMgcRawSpatialStacker.kt'))),
  ('runner','build_26927_incremental.py'),
  ('workflow','.github/workflows/build-26927-change-aware.yml'),
  ('trigger','TRIGGER_26927.txt'),
  ('patch','26927_FORWARD_FULLINDEX.patch'),
  ('manifest','26927_EXPECTED_FULL_APP.sha256'),
  ('allowlist','26927_CHANGED_RUNTIME_ALLOWLIST.txt'),
  ('stage_order','26927_V1_STAGE_3_UPLOAD_PATHS.txt'),
  ('script','test_26927_chroma_math.py'),
 ]
 for name,rel in attacks:
  p=home/rel;originalbytes=p.read_bytes();p.write_bytes(originalbytes+b'\n# bad mutation\n')
  rc=subprocess.run(['python3','-S','build_26927_incremental.py','seal'],cwd=home,capture_output=True).returncode
  assert rc!=0,(name,'accepted corrupted stage')
  p.write_bytes(originalbytes)
  assert sha(p)==listed[rel]
 for rel in ('TRIGGER_26927.txt','compile_26927_shaders.sh','26927_FORWARD_FULLINDEX.patch'):
  p=home/rel;originalbytes=p.read_bytes();p.unlink()
  rc=subprocess.run(['python3','-S','build_26927_incremental.py','seal'],cwd=home,capture_output=True).returncode
  assert rc!=0,(rel,'accepted missing staged file')
  p.write_bytes(originalbytes)
  assert sha(p)==listed[rel]
 print('PASS 26927 full three-stage, 10 hostile mutations + 3 missing-file negative tests reject; pristine restored')
