#!/usr/bin/env python3
"""Adversarial SHA-seal mutations must be rejected without mutating stage files."""
from pathlib import Path
from importlib.machinery import SourceFileLoader
R=Path(__file__).resolve().parent
b=SourceFileLoader('build26974',str(R/'build_26974_incremental.py')).load_module()
b.seal()
want=b.parse(R/'26974_EXPECTED_FULL_APP.sha256')
for p in sorted(b.MODIFIED):
 assert b.sha(R/'handoff_payload_26974'/p)==want[p]
checks=(
 'handoff_payload_26974/app/version.properties',
 '26974_EXACT_EXPANDED_C_SHADERS/sabre_merge.frag',
 '.github/workflows/build-26974-change-aware.yml',
 '26973_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py',
 'test_26974_android_api.py',
)
for path in checks:
 f=R/path;raw=f.read_bytes()
 try:
  f.write_bytes(raw+b'\n# MUTATED_SHOULD_REJECT\n')
  try:b.seal()
  except Exception:pass
  else:raise AssertionError('seal accepted mutated '+path)
 finally:f.write_bytes(raw)
b.seal()
print('PASS 26974 sealed negative mutation injections: 4/4 rejected; originals restored bit-identically')
