#!/usr/bin/env python3
"""Fail-closed 26919 SHA, prior successful 26918 runner, source and trigger mutations."""
from pathlib import Path
import tempfile,shutil
import verify_26919_handoff as v
R=Path(__file__).resolve().parent
stage=(R/'26919_STAGE1_PATHS.txt').read_text().splitlines()
paths=stage+[v.WF,'TRIGGER_26919.txt',v.PRIOR_WF,v.PRIOR_BUILDER]
with tempfile.TemporaryDirectory(prefix='26919_negative_') as tmp:
 root=Path(tmp)
 for p in paths:
  assert (R/p).is_file(),p
  q=root/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,q)
 old=v.R;v.R=root
 try:
  v.verify()
  tests=[
   ('source fcc','handoff_payload_26919/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt'),
   ('source router','handoff_payload_26919/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'),
   ('version','handoff_payload_26919/app/version.properties'),
   ('builder','build_26919_incremental.py'),
   ('shader compiler','compile_26919_fcc_glsl.sh'),
   ('new shader test','test_26919_clip_fcc.py'),
   ('new source test','test_26919_source.py'),
   ('patch proof','test_26919_patch_proof.py'),
   ('negative proof','test_26919_sealed_negatives.py'),
   ('new workflow',v.WF),
   ('prior workflow',v.PRIOR_WF),
   ('prior builder',v.PRIOR_BUILDER),
   ('base source seal','26919_BASE_26918_FULL_APP.sha256'),
   ('candidate source seal','26919_PRECOMPILE_EXPECTED_FULL_APP.sha256'),
   ('protected border','26919_FROZEN_26917_BORDER.sha256'),
   ('full-index patch','26919_FULL_INDEX_FORWARD.patch'),
   ('allowlist','26919_CHANGED_RUNTIME_ALLOWLIST.txt'),
   ('stage1 inventory','26919_STAGE1_PATHS.txt'),
   ('stage receipts','26919_HANDOFF_HASHES.sha256'),
   ('trigger','TRIGGER_26919.txt'),
   ('added files','26919_ADDED_RUNTIME_PATHS.txt'),
   ('deleted files','26919_DELETED_RUNTIME_PATHS.txt'),
  ]
  count=0
  for label,path in tests:
   q=root/path;before=q.read_bytes();q.write_bytes(before+b'\nTAMPER-26919\n')
   try:
    try:v.verify()
    except (AssertionError,ValueError,FileNotFoundError):count+=1
    else:raise AssertionError('accepted mutation: '+label)
   finally:q.write_bytes(before)
  v.verify()
  assert count==len(tests)
  print('PASS 26919',count,'sealed hostile tamper/missing receipt rejection tests')
 finally:v.R=old
