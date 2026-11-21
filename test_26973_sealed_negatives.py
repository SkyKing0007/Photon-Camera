#!/usr/bin/env python3
"""Physical negative tests: altered source, header seal, stage list & authority reference."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import build_26973_incremental as b
b.seal()
cases=[b.R/'handoff_payload_26973/app/version.properties',b.R/'26973_STAGE_3_UPLOAD_PATHS.txt',b.R/'26972_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml',b.R/'26973_EXPANDED_SHADER_HASHES.sha256']
for f in cases:
 old=f.read_bytes()
 try:
  f.write_bytes(old+b'X')
  try:b.seal()
  except Exception:pass
  else:b.fail('negative changed file accepted '+f.name)
 finally:f.write_bytes(old)
 b.seal()
print('PASS 26973 4 fail-closed source/stage/provenance/shader negative mutations plus exact restore')
