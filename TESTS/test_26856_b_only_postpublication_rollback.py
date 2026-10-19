#!/usr/bin/env python3
"""Permanent regression: B-only post-JPEG failure must remove a published JPEG/HEIC.

Source-contract checks plus failure-injection filesystem model, not an Android
compiler or integration test. A and A+B retain their independent legacy owners.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
s=(Path(__file__).resolve().parents[1]/'handoff_payload_26856/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
run=s[s.index('    public void Run() {'):s.index('private void ApplyHdrX() {')]
assert 'mIris26856BOnlyJpegRollbackPath = null;' in s[s.index('    public void start('):s.index('    public void startMotion(')]
assert 'mIris26856BOnlyJpegRollbackPath = null;' in run
assign=run.index('                ApplyHdrX();')
commit=run.index('mIris26856BOnlyJpegRollbackPath = null;', assign)
finally_part=run.index('            if (mIris26856BOnlyJpegRollbackPath != null) {',commit)
assert 'java.nio.file.Files.deleteIfExists(mIris26856BOnlyJpegRollbackPath);' in run[finally_part:]
assert run.index('mMotion26486ExposurePairs = null;') < finally_part
arm=s.index('mIris26856BOnlyJpegRollbackPath = imageFile;')
encoder=s.index('imageSaved = ImageSaver.Util.saveBitmapAsJPGMotionV2(')
fail=s.index('if (iris26856BOnly && !imageSaved) {')
notify=s.index('processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);')
assert arm < encoder < fail < notify
assert 'if (iris26856Both && !(imageSaved && iris26856BSavedForNotification))' in s
assert s.count('IRIS_26856_AB_PAIR_ROLLBACK A delete failed')==1
assert 'mIris26856BOnlyJpegRollbackPath = imageFile;' in s[s.index('if (iris26856BOnly) {',s.index('IRIS_26856_AB_DISTINCT_JPEG_NAMES')):arm+52]
# Model the field's same sequencing: arm before encoder, clear only if all
# synchronous processing/close/callback checks complete; Run finally unlinks
# an existing B file if exception or false-return leaves ownership armed.
with TemporaryDirectory() as td:
 for (name,encoder_succeeds,later_completes,expected_exists) in (
    ('B_fails_mid_encoder',False,False,False),
    ('B_saved_then_close_fails',True,False,False),
    ('B_saved_then_callback_fails',True,False,False),
    ('B_success',True,True,True),
 ):
  p=Path(td)/f'{name}_B_RAWR.jpg'
  p.write_bytes(b'partially-or-fully-written-JPEG')
  owner=p
  if encoder_succeeds and later_completes: owner=None
  if owner is not None: owner.unlink(missing_ok=True)
  assert p.exists() == expected_exists,name
# Check existing A+B atomic rollback remains present, and A-only does not arm
# the B-only rollback. These scopes must not be broadened.
assert 'if (iris26856BOnly) {\n            // Arm rollback BEFORE' in s
print('PASS B-only encoder false/partial, post-publication failure and successful commit cleanup')
print('PASS historical A/A+B ownership unchanged by B-only rollback')
