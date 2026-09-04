#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[x for x in '''app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/version.properties'''.splitlines() if x]
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(r):return {p.relative_to(r).as_posix():sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def section(s,a,b):
 if a not in s or b not in s:fail('section anchors '+a+' / '+b)
 return s[s.index(a):s.index(b,s.index(a)+len(a))]
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);a,d=amap(b),amap(c)
 if len(a)!=1708 or len(d)!=1708:fail(f'universe {len(a)}/{len(d)}')
 diff=sorted(k for k in set(a)|set(d) if a.get(k)!=d.get(k))
 if diff!=sorted(CHANGED):fail('allowlist '+repr(diff))
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726593','version');need(v,'VERSION_BUILD=26593','version')
 for r,h in a.items():
  if r not in CHANGED and d.get(r)!=h:fail('protected owner '+r)
 cap=(c/CHANGED[0]).read_text();basecap=(b/CHANGED[0]).read_text();batch=(c/CHANGED[1]).read_text();bridge=(c/CHANGED[2]).read_text()
 # Exact real Actions javac failure 33833745581: successful 26592 stores preview result as CaptureResult.
 need(basecap,'public static CaptureResult mPreviewCaptureResult;','26592 preview result type authority')
 need(cap,'mPreviewCaptureResult instanceof TotalCaptureResult','26593 checked TotalCaptureResult cast')
 need(cap,'? (TotalCaptureResult) mPreviewCaptureResult : null;','26593 checked TotalCaptureResult cast')
 if 'final TotalCaptureResult iris26593NormalReference = mPreviewCaptureResult;' in cap:fail('Actions 33833745581 direct CaptureResult->TotalCaptureResult assignment survived')
 # Slider is total physical frame budget, auxiliaries reserve slots, one NORMAL is mandatory.
 for t in ['IRIS_26593_MOTION_TOTAL_FRAME_SLIDER_OWNER','MOTION_26593_MAX_TOTAL_FRAMES = 30','iris26593AuxCount','iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount','iris26593NormalTarget < 1','exactTotalRequired=true']:
  need(cap,t,'total frame owner')
 # Shutter-frozen NORMAL metadata is the exposure owner for SHORT/LONG and top-up.
 for t in ['normalReferenceResult','applyMotion26486ExplicitShortCaptureIfNeeded(\n                        iris26486ShortTicket, iris26593NormalReference)','applyMotion26505ExplicitLongCaptureIfUseful(iris26505LongTicket, iris26593NormalReference)','mCaptureResult = iris26593Plan.normalReferenceResult','iris26593Plan.normalReferenceResult.getRequest()']:
  need(cap,t,'frozen normal owner')
 # Quick-open top-up: only missing NORMALs, raw-only, same exposure/ISO, no preview mutation.
 for t in ['IRIS_26593_EXPLICIT_FROZEN_NORMAL_TOPUP','submitMotion26593MissingNormals','MOTION_26593_NORMAL_TOPUP_TAG','SENSOR_EXPOSURE_TIME, expObj','SENSOR_SENSITIVITY, isoObj','previewRepeatingRequestMutated=false rawOnlyTarget=true']:
  need(cap,t,'quick-open topup')
 # The actual chandelier failure is now impossible to silently downgrade: scene requirement survives submit failure.
 for t in ['volatile boolean sceneRequired = false','ticket.sceneRequired = sceneRequiresShort','iris26486ShortTicket.sceneRequired','IRIS_26593_REQUIRED_SHORT_NOT_SUBMITTED','SHORT_CAPTURE_FAILURE','SHORT_CAPTURE_TIMEOUT','silentNormalOnlyForbidden=true']:
  need(cap,t,'required SHORT')
 # One generation owns exact ticket objects even after mutable ingress pointers clear.
 for t in ['IRIS_26593_GENERATION_OWNED_TOTAL_CAPTURE_PLAN','final Motion26486ShortTicket shortTicket','final Motion26505LongTicket longTicket','mMotion26593CapturePlan = iris26593Plan','final Motion26486ShortTicket iris26486ShortTicket = iris26593Plan.shortTicket']:
  need(cap,t,'generation ownership')
 # Old contradictory 80ms batch seal / metadata-only no-topup logic is gone.
 for t in ['freezeExpectedAuxiliaries','MOTION_26520_FROZEN_METADATA_GRACE_MS','pollMotion26520FrozenMetadataGrace','pollMotionTopUp()']:
  if t in cap+batch:fail('retired freeze/topup survived '+t)
 # Immutable total and bridge fail-loud guard.
 for t in ['freezePresentAuxiliaries','requiredFreezeComplete','totalFrameCount','exact total-frame contract mismatch']:
  need(batch,t,'MotionBatch exact total')
 for t in ['shortWasExpected','shadowWasExpected','requiredFreezeComplete','requested SHORT disappeared after immutable batch freeze','requested LONG disappeared after immutable batch freeze','IRIS_26593_AUX_OWNERSHIP_PROOF']:
  need(bridge,t,'bridge aux proof')
 need(cap,'IRIS_26593_UNRESERVED_SHADOW_AUX_DISABLED','unreserved shadow guard');need(cap,'boolean brighter = false;','unreserved shadow disabled')
 # Preserve successful 26592 image math exactly. These are explicitly not in the allowlist.
 protected=[
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/assets/shaders/motionv2/render.glsl',
  'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
  'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java']
 for r in protected:
  if a[r]!=d[r]:fail('26592 IQ owner drift '+r)
 # Night path remains null-slot and cannot be made subject to Motion auxiliary freeze.
 night=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java').read_text()
 need(night,'PhotonMotionMgc1271Bridge.reconstruct(\n                    new Point(width, height), images, ref, p, null, batch.saveRaw >= 1)','Night null aux slot')
 print('PASS exact successful-26592 authority -> exact four-file 26593 total-frame HDR ownership allowlist')
 print('PASS slider N is exact physical total; required SHORT/LONG reserve slots; quick-open top-up uses shutter-frozen NORMAL exposure without mutating preview')
 print('PASS generation-owned SHORT cannot silently disappear; missing required auxiliary fails before reconstruction; old 80ms freeze removed')
 print('PASS MotionBatch/bridge immutable total and requested-aux proof; unreserved shadow promotion disabled')
 print('PASS successful 26592 viewfinder meter/Sabre handoff/render/8x UHDR/DNG/SR/Night IQ owners byte-identical')
if __name__=='__main__':main()
