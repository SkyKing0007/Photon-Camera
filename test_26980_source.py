#!/usr/bin/env python3
import argparse,pathlib,importlib.util
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload^a.live
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26980',R/'build_26980_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
changed,base,expected=b.scope();root=R/'handoff_payload_26980' if a.payload else R
if a.payload:assert {p:b.sha(root/p) for p in changed}=={p:expected[p] for p in changed}
else:b.exact(R,'26980_EXPECTED_FULL_APP.sha256','26980 complete runtime')
def get(n):
 p=list((root/'app/src/main/java').rglob(n));assert len(p)==1,(n,p);return p[0].read_text()
def need(s,*t):
 for x in t:assert x in s,x
c=get('CaptureController.java');session=get('Iris26972CCamera2ShutterSession.kt');engine=get('Iris26975CPinnedDonorProEngine.kt');t=get('TouchFocus.java');contract=get('Iris26972CContract.java');defaults=get('Iris26975COriginalDonorEngine.kt');ticket=get('Iris26977CPreviewTicket.java');join=get('Iris26976CRawTicketJoin.java')
need(c,'Iris26980CManualExposure.plan(','chosen.shutterNs','chosen.iso','STATISTICS_SCENE_FLICKER','mIris26980CTouchRegion','mIris26980CTouchLens','iris26980CSetTouchRegion','mIris26979CTracking.observeProtection(','mIris26980CWaitingForLock','if(cLockedGroup) { requests.add(cProducingRequest); continue; }','owner.remainingResultSlots()','owner.attemptsRemaining()>=missing','cActiveSequence[0]=captureSession.captureBurst(replacements,this,captureHandler)','cSequenceFence.takeReleasePermit()','mIris26980CReference.copyIfReady(b -> b.copy(android.graphics.Bitmap.Config.ARGB_8888,false))','IRIS_26980_C_HDRNET_REFERENCE','mIris26980CReferenceLastProof<=400L','iris26978CArmUi(owner);','iris26978CFinishUi(ownerHolder[0]);')
need(session,'Iris26980CExactExposureGroup(frameCount)','exactGroup.admit(actualTime, actualIso)','rawTickets.reject(ts)','pendingRaw.remove(ts)?.close()','nextResult == exactGroup.accepted()','if (!activated || state != State.COLLECTING) return','active.hasCompletePhysicalBurst()','physical.get(CaptureResult.SENSOR_TIMESTAMP) == ts','index == nextTotalAttempt','starts[index]','previewTicket.await(1500L)','ImagePath.generateNewFileName("IMG")')
need(join,'target*3','!rejected.contains(timestamp)','delivered.remove(timestamp)','trimPending(int limit)')
need(ticket,'copyIfReady(java.util.function.Function<Bitmap,Bitmap> copier)','copier.apply(bitmap)','isReady()')
need(t,'iris26980CSetTouchRegion(rectaf)','iris26980CSetTouchRegion(null)','iris26980CSetTouchRegion(activeTouchRegion)')
need(contract,'CHROMA_DENOISE = 0.50f','SHARPENING = 0.20f');need(defaults,'DEFAULT_CHROMA = 0.50f','DEFAULT_SHARPENING = 0.20f','DEFAULT_LUMA = 0.00f','Iris26972CContract.CHROMA_DENOISE == DEFAULT_CHROMA')
need(engine,'MultiFrameStacker.processBurstRaw','renderer.processMgcSpatialGpuLinearRgb','chromaStrengthScale = Iris26975COriginalDonorEngine.DEFAULT_CHROMA','chromaDenoiseValue = Iris26975COriginalDonorEngine.DEFAULT_CHROMA','sharpeningValue = Iris26975COriginalDonorEngine.DEFAULT_SHARPENING','mgcTuningSnr = tuningSnr','capturePreviewThumbnail = capturePreview','RawRenderingEngine.AdobeCurve','includeHdrReference = true','rawOutputUpscaleMode = proSabre1x.outputUpscaleMode','Iris26978CFinalOutput.prepareSdr(originalSdr)','rawGpuGainmapProducer.build(','baseExifWriter = { base -> Iris26979CExif.write(base, info) }','Iris26979CExif.verify(temporary, info)','Iris26975CDonorMediaStorePublisher.publish(')
assert engine.index('Iris26979CExif.verify(temporary, info)')<engine.index('Iris26975CDonorMediaStorePublisher.publish(')
assert base['app/build.gradle']==expected['app/build.gradle']
for x in changed:assert not any(k in x for k in ('/src/main/cpp/','/src/main/assets/','/src/main/jniLibs/','/original129/'))
if a.live:
 for n in ('Iris26978CFinalOutput.kt','Iris26972CPhysicalRawSpool.kt','Iris26977CDonorPrewarm.kt','RawDemosaicProcessor.kt','RawMgcTuningSnr.kt','MultiFrameStacker.kt','GpuReferenceGainmapProducer.kt','ExifWriter.kt','NoLookLutRawGainmapSidecar.kt','ImagePath.java','ParseExif.java','CameraUIViewImpl.java','CameraFragment.java','RawWarpRectilinearPass.kt'):
  matches=[p for p in base if p.endswith('/'+n)];assert matches and all(base[p]==expected[p] for p in matches),n
 print('PASS protected donor equations, final JPEG/R, UI, exact physical RAW spool and calibration invariance')
print('PASS 26980 source wiring: constrained manual optimization, touch ownership, exact result retry, 0.20/0.50 tuning')
