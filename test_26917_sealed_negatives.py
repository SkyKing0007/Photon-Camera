#!/usr/bin/env python3
"""26917 fail closed: historical successful 26916 authority, 5-source payload,
real shader/NDK/build gates, stage ordering and every uploaded byte.
"""
from pathlib import Path
import shutil,tempfile
import verify_26917_handoff as v
R=Path(__file__).resolve().parent
stage=(R/'26917_STAGE1_PATHS.txt').read_text().splitlines()
files=stage+[v.WF,'TRIGGER_26917.txt',v.PRIOR_WF,v.PRIOR_BUILDER]
with tempfile.TemporaryDirectory(prefix='26917_sealed_negatives_') as td:
 root=Path(td)
 for p in files:
  f=R/p;assert f.is_file(),p
  dst=root/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
 oldR=v.R;v.R=root
 try:
  v.verify()
  cases=[
   ('source header','handoff_payload_26917/app/src/main/cpp/iris26856/amaze/include/amaze/Amaze.hpp'),
   ('source tiles','handoff_payload_26917/app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp'),
   ('source compiler','handoff_payload_26917/app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp'),
   ('source B owner','handoff_payload_26917/app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc'),
   ('Java native method ownership','handoff_payload_26917/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java'),
   ('Kotlin Night and SR guard','handoff_payload_26917/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'),
   ('version','handoff_payload_26917/app/version.properties'),
   ('prior manifest','26917_BASE_26916_FULL_APP.sha256'),
   ('new manifest','26917_PRECOMPILE_EXPECTED_FULL_APP.sha256'),
   ('allowed files','26917_CHANGED_RUNTIME_ALLOWLIST.txt'),
   ('staged files','26917_STAGED_RUNTIME_ALLOWLIST.txt'),
   ('generated only','26917_GENERATED_RUNTIME_PATHS.txt'),
   ('added','26917_ADDED_RUNTIME_PATHS.txt'),
   ('deleted','26917_DELETED_RUNTIME_PATHS.txt'),
   ('patch','26917_FULL_INDEX_FORWARD.patch'),
   ('builder','build_26917_incremental.py'),
   ('workflow',v.WF),
   ('new shader compiler','compile_26917_amaze_import.sh'),
   ('new shader regression','test_26917_border.py'),
   ('new source regression','test_26917_source.py'),
   ('patch regression','test_26917_patch_proof.py'),
   ('stage1 paths','26917_STAGE1_PATHS.txt'),
   ('inventory SHA','26917_HANDOFF_HASHES.sha256'),
   ('trigger','TRIGGER_26917.txt'),
   ('successful prior workflow',v.PRIOR_WF),
   ('successful prior builder',v.PRIOR_BUILDER),
  ]
  count=0
  for label,p in cases:
   f=root/p;before=f.read_bytes();f.write_bytes(before+b'\nBAD26917\n')
   try:
    try:v.verify()
    except (AssertionError,ValueError,FileNotFoundError,UnicodeDecodeError):count+=1
    else:raise AssertionError('26917 unsafe mutated file accepted: '+label)
   finally:f.write_bytes(before)
  v.verify()
  assert count==len(cases)
  print('PASS 26917 sealed mutation rejection:',count,'real source, shader, proof, builder, workflow, authority, trigger fail-closed cases')
 finally:v.R=oldR
