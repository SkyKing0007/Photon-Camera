#!/usr/bin/env python3
"""Mutation replay against actually staged 26915 complete SHA-sealed payload.
Old successful 26914 V2 builder/workflow are copied from verified Actions
receipts for local tests, never rewritten or substituted with a fixture.
"""
from pathlib import Path
import tempfile,shutil,sys
import verify_26915_handoff as v
R=Path(__file__).resolve().parent
base_paths=(R/'26915_STAGE1_PATHS.txt').read_text().splitlines()
paths=base_paths+[v.WF,'TRIGGER_26915.txt',v.PREV_WF,'build_26914_v2_incremental.py']
with tempfile.TemporaryDirectory(prefix='26915_negative_') as td:
 root=Path(td)
 for name in paths:
  src=R/name;assert src.is_file(),name
  out=root/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,out)
 prev=v.R;v.R=root
 try:
  v.verify()
  mutations=[
   ('corrupt full-index patch','26915_FULL_INDEX_FORWARD.patch',lambda b:b+b'\n'),
   ('corrupt payload Kotlin','handoff_payload_26915/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',lambda b:b+b'\n'),
   ('corrupt native JNI','handoff_payload_26915/app/src/main/cpp/motionv2_jpeg444_jni.cpp',lambda b:b+b'X'),
   ('corrupt native guide header','handoff_payload_26915/app/src/main/cpp/iris26915_rgba16f_guide.h',lambda b:b.replace(b'stridePixels',b'badPixels',1)),
   ('corrupt Java capture','handoff_payload_26915/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',lambda b:b+b' '),
   ('corrupt version','handoff_payload_26915/app/version.properties',lambda b:b.replace(b'26915',b'26914')),
   ('corrupt builder','build_26915_incremental.py',lambda b:b+b'\n'),
   ('corrupt current workflow',v.WF,lambda b:b+b'\n'),
   ('wrong trigger','TRIGGER_26915.txt',lambda b:b+b'\n'),
   ('tampered manifest','26915_PRECOMPILE_EXPECTED_FULL_APP.sha256',lambda b:b+b'invalid\n'),
   ('changed source allowlist','26915_CHANGED_RUNTIME_ALLOWLIST.txt',lambda b:b+b'new.java\n'),
   ('missing source in stage1','26915_STAGE1_PATHS.txt',lambda b:b.replace(b'test_26915_capture.py\n',b'')),
   ('corrupt predecessor runner','build_26914_v2_incremental.py',lambda b:b+b'\n'),
   ('corrupt predecessor workflow',v.PREV_WF,lambda b:b+b'\n'),
  ]
  for label,name,mutate in mutations:
   path=root/name;orig=path.read_bytes();modified=mutate(orig)
   assert modified!=orig,label
   path.write_bytes(modified)
   try:
    try:v.verify()
    except (AssertionError,ValueError,FileNotFoundError):pass
    else:raise RuntimeError('INVALID SOURCE ACCEPTED: '+label)
   finally:path.write_bytes(orig)
  v.verify()
  print('PASS 26915 clean staged originals and 14 fail-closed real-byte mutations')
 finally:v.R=prev
