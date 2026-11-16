#!/usr/bin/env python3
"""Sealed upload tamper, old historical checks and 26945 V1 bad SHA regressions."""
import pathlib,shutil,tempfile,sys
import build_26947_incremental as b
def main():
 origin=b.R
 paths=[pathlib.Path(row.split('  ',1)[1]) for row in (origin/'26947_HANDOFF_HASHES.sha256').read_text().splitlines()]
 paths.append(pathlib.Path('26947_HANDOFF_HASHES.sha256'))
 cases=[('build_26947_incremental.py','delete'),('handoff_payload_26947/app/version.properties','append'),
 ('handoff_payload_26947/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','append'),
 ('handoff_payload_26947/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','append'),
 ('handoff_payload_26947/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java','append'),
 ('26947_FORWARD_FULLINDEX.patch','append'),('26947_ROLLBACK_FULLINDEX.patch','delete'),
 ('26947_PROTECTED_SOURCE.sha256','append'),('26947_CHANGED_RUNTIME_ALLOWLIST.txt','append'),
 ('26947_BASE_26946_FULL_APP.sha256','append'),('26947_EXPECTED_ACTION_EXECUTABLES.txt','append'),
 ('26947_STAGE_1_UPLOAD_PATHS.txt','append'),('26947_STAGE_2_UPLOAD_PATHS.txt','append'),
 ('26947_STAGE_3_UPLOAD_PATHS.txt','append'),('test_26947_lifecycle.py','delete'),
 ('test_26947_java_host.py','delete'),('prepare_26947_lkr_from_successful_26946.py','delete'),
 ('TRIGGER_26947.txt','append')]
 passed=0
 with tempfile.TemporaryDirectory(prefix='26947_negative_') as td:
  d=pathlib.Path(td)
  for p in paths:
   dst=d/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin/p,dst)
  b.R=d;b.seal()
  for p,mode in cases:
   f=d/p;old=f.read_bytes()
   try:
    if mode=='delete':f.unlink()
    else:f.write_bytes(old+b'\nBAD_MUTATION')
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('unsealed mutation accepted '+p)
   finally:f.write_bytes(old)
  wf=d/'.github/workflows/build-26947-change-aware.yml'
  for key,new in [('verify_26904_v3_safety.py','verify_26904_missing.py'),
                  ('build_26946_incremental.py seal','build_26943_incremental.py seal'),
                  ('actions/upload-artifact@v4','actions/upload-artifact@v4\n        uses: actions/upload-artifact@v4'),
                  ('build_26947_incremental.py prepare','build_26946_incremental.py prepare')]:
   content=wf.read_bytes();receipt=d/'26947_HANDOFF_HASHES.sha256';m=receipt.read_bytes()
   try:
    assert key.encode() in content
    wf.write_bytes(content.replace(key.encode(),new.encode(),1))
    receipt.write_bytes(m.replace((b.sha(origin/'.github/workflows/build-26947-change-aware.yml')+'  .github/workflows/build-26947-change-aware.yml').encode(),(b.sha(wf)+'  .github/workflows/build-26947-change-aware.yml').encode()))
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('resealed hostile workflow accepted '+key)
   finally:wf.write_bytes(content);receipt.write_bytes(m)
  for name in ('TAR_SHA','ART_SHA'):
   correct=getattr(b,name)
   try:
    setattr(b,name,correct[:12]+'a'+correct[12:] if name=='TAR_SHA' else correct[:63])
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('noncanonical SHA accepted '+name)
   finally:setattr(b,name,correct)
  if passed!=len(cases)+6:b.fail('negative count mismatch '+str(passed))
  b.seal()
 b.R=origin
 print('PASS',passed,'fail-closed source, stage, workflow, old refs, exact 64-character digest and re-sealed negative cases')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
