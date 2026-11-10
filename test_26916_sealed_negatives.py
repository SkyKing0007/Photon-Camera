#!/usr/bin/env python3
"""Fail closed against staged actual source bytes, historical runner/workflow and workflow trigger."""
from pathlib import Path
import tempfile,shutil
import verify_26916_handoff as v
R=Path(__file__).resolve().parent
stage=(R/'26916_STAGE1_PATHS.txt').read_text().splitlines()
paths=stage+[v.WF,'TRIGGER_26916.txt',v.PRIOR_WF,v.PRIOR_BUILDER]
with tempfile.TemporaryDirectory(prefix='26916_sealed_negative_') as tmp:
 root=Path(tmp)
 for p in paths:
  assert (R/p).is_file(),p
  dst=root/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,dst)
 previous=v.R;v.R=root
 try:
  v.verify()
  mutations=[
   ('hue shader cannot change','handoff_payload_26916/app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl',lambda b:b+b'\n'),
   ('calibration cannot change','handoff_payload_26916/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java',lambda b:b+b' '),
   ('manifest mismatch','26916_PRECOMPILE_EXPECTED_FULL_APP.sha256',lambda b:b+b'invalid\n'),
   ('old manifest mismatch','26916_BASE_26915_FULL_APP.sha256',lambda b:b+b'corrupt\n'),
   ('allowlist extension','26916_CHANGED_RUNTIME_ALLOWLIST.txt',lambda b:b+b'app/src/main/cpp/hijack.cpp\n'),
   ('patch corruption','26916_FULL_INDEX_FORWARD.patch',lambda b:b+b'\n'),
   ('builder corruption','build_26916_incremental.py',lambda b:b+b'\n'),
   ('workflow corruption',v.WF,lambda b:b+b'\n'),
   ('wrong last trigger','TRIGGER_26916.txt',lambda b:b+b'BAD\n'),
   ('stage list corruption','26916_STAGE1_PATHS.txt',lambda b:b+b'fake.txt\n'),
   ('seal corruption','26916_HANDOFF_HASHES.sha256',lambda b:b+b'BAD\n'),
   ('predecessor builder corruption',v.PRIOR_BUILDER,lambda b:b+b'\n'),
   ('predecessor workflow corruption',v.PRIOR_WF,lambda b:b+b'\n'),
   ('removed Kotlin/Java regression','test_26916_source.py',lambda b:b+b'\n'),
   ('changed hue regression','test_26916_hue.py',lambda b:b+b'\n'),
   ('newer Java code alteration','tests_26916/Photon26916HueRegression.java',lambda b:b+b'\n'),
  ]
  count=0
  for label,p,mutate in mutations:
   q=root/p;old=q.read_bytes();new=mutate(old);assert new!=old
   q.write_bytes(new)
   try:
    try:v.verify()
    except (AssertionError,ValueError,FileNotFoundError):count+=1
    else:raise AssertionError('mutation accepted: '+label)
   finally:q.write_bytes(old)
  v.verify()
  assert count==len(mutations)
  print('PASS 26916 exact SHA-staged malicious change rejection:',count,'fail-closed mutations')
 finally:v.R=previous
