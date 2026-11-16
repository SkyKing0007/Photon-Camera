#!/usr/bin/env python3
"""Full staged three-stage SHA/fail-closed adversarial replay, including V1 stale TAR typo."""
import pathlib,shutil,tempfile,sys
import build_26946_incremental as b

def main():
 original=b.R
 files=[pathlib.Path(x.split('  ',1)[1]) for x in (original/'26946_HANDOFF_HASHES.sha256').read_text().splitlines()]
 files.append(pathlib.Path('26946_HANDOFF_HASHES.sha256'))
 cases=[
 ('missing builder','build_26946_incremental.py','missing'),
 ('altered front gain','handoff_payload_26946/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java','append'),
 ('altered crop route','handoff_payload_26946/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','append'),
 ('altered version','handoff_payload_26946/app/version.properties','append'),
 ('altered patch','26946_FORWARD_FULLINDEX.patch','append'),
 ('missing rollback','26946_ROLLBACK_FULLINDEX.patch','missing'),
 ('wrong prior successful source','26946_BASE_26945_FULL_APP.sha256','append'),
 ('altered 2051 protection','26946_PROTECTED_SOURCE.sha256','append'),
 ('unexpected changed path','26946_CHANGED_RUNTIME_ALLOWLIST.txt','append'),
 ('unused executable','26946_EXPECTED_ACTION_EXECUTABLES.txt','append'),
 ('wrong stage1 list','26946_STAGE_1_UPLOAD_PATHS.txt','append'),
 ('wrong stage2 list','26946_STAGE_2_UPLOAD_PATHS.txt','append'),
 ('wrong stage3 list','26946_STAGE_3_UPLOAD_PATHS.txt','append'),
 ('removed historical 26904 V3',' .github/workflows/build-26946-change-aware.yml'.strip(),'historic'),
 ('removed successful 26945 historical',' .github/workflows/build-26946-change-aware.yml'.strip(),'prior'),
 ('duplicate compile',' .github/workflows/build-26946-change-aware.yml'.strip(),'duplicate'),
 ('wrong trigger','TRIGGER_26946.txt','append'),
 ('missing Java host test','test_26946_java_host.py','missing'),
 ('missing shader geometry test','test_26946_gainmap_geometry.py','missing'),
 ('missing published prior native restore','prepare_26946_lkr_from_successful_26945.py','missing')]
 passed=0
 with tempfile.TemporaryDirectory(prefix='26946_mutant_') as temp:
  d=pathlib.Path(temp)
  for rel in files:
   target=d/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original/rel,target)
  b.R=d;b.seal()
  for name,rel,mode in cases:
   f=d/rel;old=f.read_bytes()
   try:
    if mode=='missing':f.unlink()
    elif mode=='historic':f.write_bytes(old.replace(b'verify_26904_v3_safety.py',b'verify_26904_v2_safety.py',1))
    elif mode=='prior':f.write_bytes(old.replace(b'build_26945_incremental.py seal',b'build_26944_incremental.py seal',1))
    elif mode=='duplicate':f.write_bytes(old.replace(b'actions/upload-artifact@v4',b'actions/upload-artifact@v4\n        uses: actions/upload-artifact@v4',1))
    else:f.write_bytes(old+b'\nUNAUTHORIZED_TAMPER\n')
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('failed open to unsealed mutation '+name)
   finally:f.write_bytes(old)
  # Malicious re-sealing cannot bypass source/workflow mandatory contract.
  changes=[
   ('26946_CHANGED_RUNTIME_ALLOWLIST.txt','app/version.properties','app/src/main/cpp/MALICIOUS.so'),
   ('.github/workflows/build-26946-change-aware.yml','verify_26904_v3_safety.py','verify_26904_xx_safety.py'),
   ('.github/workflows/build-26946-change-aware.yml','build_26945_incremental.py seal','build_26944_incremental.py seal'),
   ('.github/workflows/build-26946-change-aware.yml','actions/upload-artifact@v4','actions/upload-artifact@v4\n        uses: actions/upload-artifact@v4'),
  ]
  for rel,key,repl in changes:
   f=d/rel;originalbytes=f.read_bytes();manifest=d/'26946_HANDOFF_HASHES.sha256';oldmanifest=manifest.read_bytes()
   if key.encode() not in originalbytes:b.fail('negative fixture keyword absent '+key)
   try:
    f.write_bytes(originalbytes.replace(key.encode(),repl.encode(),1))
    manifest.write_bytes(oldmanifest.replace((b.sha(original/rel)+'  '+rel).encode(),(b.sha(f)+'  '+rel).encode()))
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('re-sealed hostile tamper accepted '+rel)
   finally:f.write_bytes(originalbytes);manifest.write_bytes(oldmanifest)
  # Actual failed 26945 V1: a 65-hex source TAR SHA must fail before fetch/compile.
  proper=b.TAR_SHA
  try:
   b.TAR_SHA=proper[:24]+'a'+proper[24:]
   try:b.seal()
   except Exception:passed+=1
   else:b.fail('65-character compiled source digest accepted')
  finally:b.TAR_SHA=proper
  # Official published artifact itself must be pinned as 64-hex, not a placeholder.
  proper=b.ART_SHA
  try:
   b.ART_SHA=proper[:63]
   try:b.seal()
   except Exception:passed+=1
   else:b.fail('63-character artifact digest accepted')
  finally:b.ART_SHA=proper
  if passed!=len(cases)+len(changes)+2:b.fail('negative-count mismatch '+str(passed))
  b.seal()
 b.R=original
 print(f'PASS {passed} negative tests: stage, source, historical, executable, re-sealed, stale 26945 V1 checksum, artifact digest')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
