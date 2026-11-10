#!/usr/bin/env python3
"""Fail-closed 26918 stage, native frozen borders, original successful
26917 real compiler/workflow, three-path B-only shader/owner source.
"""
from pathlib import Path
import tempfile,shutil
import verify_26918_handoff as v
R=Path(__file__).resolve().parent
stage=(R/'26918_STAGE1_PATHS.txt').read_text().splitlines()
paths=stage+[v.WF,'TRIGGER_26918.txt',v.PRIOR_WF,v.PRIOR_BUILDER]
with tempfile.TemporaryDirectory(prefix='photon26918_negative_') as td:
 root=Path(td)
 for p in paths:
  src=R/p;assert src.is_file(),p
  target=root/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
 previous=v.R;v.R=root
 try:
  v.verify()
  mutations=[
   ('post-AMaZE shader', 'handoff_payload_26918/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt',b'\n'),
   ('B-only owner', 'handoff_payload_26918/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',b'\n'),
   ('version', 'handoff_payload_26918/app/version.properties',b'BAD'),
   ('frozen 26917 border SPV and source hashes','26918_FROZEN_26917_BORDER.sha256',b' BAD'),
   ('baseline authority manifest','26918_BASE_26917_FULL_APP.sha256',b'\n'),
   ('candidate source manifest','26918_PRECOMPILE_EXPECTED_FULL_APP.sha256',b'\n'),
   ('changed allowlist','26918_CHANGED_RUNTIME_ALLOWLIST.txt',b'app/src/main/cpp/attack.cpp\n'),
   ('added file','26918_ADDED_RUNTIME_PATHS.txt',b'app/src/extra.java\n'),
   ('deleted file','26918_DELETED_RUNTIME_PATHS.txt',b'app/src/old.java\n'),
   ('forward patch','26918_FULL_INDEX_FORWARD.patch',b'\n'),
   ('stage inventory','26918_STAGE1_PATHS.txt',b'fake.txt\n'),
   ('SHA seal','26918_HANDOFF_HASHES.sha256',b'BAD\n'),
   ('builder','build_26918_incremental.py',b'\n'),
   ('shader compiler','compile_26918_post_amaze_glsl.sh',b'\n'),
   ('semantic source regression','test_26918_source.py',b'\n'),
   ('bypass regression','test_26918_bypass.py',b'\n'),
   ('patch regression','test_26918_patch_proof.py',b'\n'),
   ('new workflow',v.WF,b'\n'),
   ('trigger','TRIGGER_26918.txt',b' WRONG'),
   ('executed 26917 builder',v.PRIOR_BUILDER,b'\n'),
   ('executed 26917 workflow',v.PRIOR_WF,b'\n'),
  ]
  ok=0
  for label,p,change in mutations:
   f=root/p;old=f.read_bytes();f.write_bytes(old+change)
   try:
    try:v.verify()
    except (AssertionError,ValueError,FileNotFoundError):ok+=1
    else:raise AssertionError('mutation accepted '+label)
   finally:f.write_bytes(old)
  # Negative hard removal on a historical compiled base file must be rejected.
  for p in [v.PRIOR_BUILDER,'26918_FROZEN_26917_BORDER.sha256']:
   f=root/p;old=f.read_bytes();f.unlink()
   try:
    try:v.verify()
    except (AssertionError,FileNotFoundError):ok+=1
    else:raise AssertionError('removed historical evidence accepted '+p)
   finally:f.write_bytes(old)
  v.verify();assert ok==len(mutations)+2
  print('PASS 26918 exactly',ok,'SHA-fail-closed mutations (including frozen border and original 26917 runner)')
 finally:v.R=previous
