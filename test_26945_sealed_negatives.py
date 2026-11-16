#!/usr/bin/env python3
"""Fail-closed archive, exact allowlist, 3-stage, protected and historic checks."""
import hashlib,pathlib,shutil,tempfile,sys
import build_26945_incremental as b

def main():
 original=b.R
 files=[pathlib.Path(line.split('  ',1)[1]) for line in (original/'26945_HANDOFF_HASHES.sha256').read_text().splitlines()] + [pathlib.Path('26945_HANDOFF_HASHES.sha256')]
 if not files: b.fail('no staged files to mutate')
 cases=[
  ('missing builder','build_26945_incremental.py','missing'),
  ('altered front overlay','handoff_payload_26945/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java','append'),
  ('altered preview source','handoff_payload_26945/app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java','append'),
  ('altered patch index','26945_FORWARD_FULLINDEX.patch','append'),
  ('missing rollback','26945_ROLLBACK_FULLINDEX.patch','missing'),
  ('incorrect old compiled source manifest','26945_BASE_26944_FULL_APP.sha256','append'),
  ('incorrect protected manifest','26945_PROTECTED_SOURCE.sha256','append'),
  ('unapproved scope','26945_CHANGED_RUNTIME_ALLOWLIST.txt','append'),
  ('stage1 wrong order','26945_STAGE_1_UPLOAD_PATHS.txt','append'),
  ('stage2 unexpected','26945_STAGE_2_UPLOAD_PATHS.txt','append'),
  ('stage3 wrong trigger','26945_STAGE_3_UPLOAD_PATHS.txt','append'),
  ('workflow historic check removed','.github/workflows/build-26945-change-aware.yml','historic'),
  ('workflow duplicate compile','.github/workflows/build-26945-change-aware.yml','duplicate'),
  ('trigger tamper','TRIGGER_26945.txt','append'),
 ]
 passed=0
 with tempfile.TemporaryDirectory(prefix='26945_negative_') as td:
  tmp=pathlib.Path(td)
  # seal only looks at exact 3-stage sources/hashes; no Android full source needed.
  for rel in files:
   dst=tmp/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original/rel,dst)
  b.R=tmp
  b.seal()
  for name,relative,mut in cases:
   f=tmp/relative;originalbytes=f.read_bytes()
   try:
    if mut=='missing':f.unlink()
    elif mut=='historic':f.write_bytes(originalbytes.replace(b'verify_26904_v3_safety.py',b'verify_26904_xx_safety.py'))
    elif mut=='duplicate':f.write_bytes(originalbytes.replace(b'actions/upload-artifact@v4',b'actions/upload-artifact@v4\n        uses: actions/upload-artifact@v4'))
    else:f.write_bytes(originalbytes+b'\nHOSTILE_SILENT_CHANGE\n')
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('negative failed open: '+name)
   finally:f.write_bytes(originalbytes)
  # A bypass that updates the SHA seal must also fail the independently required workflow/exact scope checks.
  for rel,needle,repl in [
    ('26945_CHANGED_RUNTIME_ALLOWLIST.txt','app/version.properties','app/src/main/cpp/MALICIOUS.so'),
    ('.github/workflows/build-26945-change-aware.yml','verify_26904_v3_safety.py','verify_26904_xx_safety.py'),
    ('.github/workflows/build-26945-change-aware.yml','actions/upload-artifact@v4','actions/upload-artifact@v4\n        uses: actions/upload-artifact@v4')]:
   f=tmp/rel;orig=f.read_bytes();seal=(tmp/'26945_HANDOFF_HASHES.sha256');oldseal=seal.read_bytes()
   assert needle.encode() in orig
   try:
    f.write_bytes(orig.replace(needle.encode(),repl.encode(),1))
    old=b.sha(f);h=b.sha(original/rel)
    seal.write_bytes(oldseal.replace((h+'  '+rel).encode(),(old+'  '+rel).encode()))
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('re-sealed malicious bypass accepted '+rel)
   finally:
    f.write_bytes(orig);seal.write_bytes(oldseal)
  # The actual 26945 V1 error: 65-character SHA-256 literal escaped original tests.
  # Negative test does not modify the sealed files or weaken existing checks.
  good=b.TAR_SHA
  try:
   b.TAR_SHA=good[:52]+'a'+good[52:]
   try:b.seal()
   except Exception:passed+=1
   else:b.fail('noncanonical 65-character source TAR SHA accepted')
  finally:b.TAR_SHA=good
  if passed!=len(cases)+4:b.fail('incorrect negative test count '+str(passed))
  b.seal()
 b.R=original
 print('PASS '+str(passed)+' fail-closed 26945 sealed negative mutations, incl re-SHA tampering and old 26944 check removal')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
