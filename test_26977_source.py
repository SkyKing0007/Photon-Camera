#!/usr/bin/env python3
"""Exact C-only runtime delta and source call-path checks; historical checks remain separate."""
import argparse,pathlib,importlib.util
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload^a.live
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26977',R/'build_26977_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
changed,base,expected=b.scope();root=R/'handoff_payload_26977' if a.payload else R
if a.payload:assert {p:b.sha(root/p) for p in changed}=={p:expected[p] for p in changed}
else:b.exact(R,'26977_EXPECTED_FULL_APP.sha256','26977 full current source')
def get(n):
 p=list((root/'app/src/main/java').rglob(n));assert len(p)==1,(n,p);return p[0].read_text()
def need(s,*t):
 for x in t:assert x in s,x
c=get('CaptureController.java');e=get('Iris26975CPinnedDonorProEngine.kt');s=get('Iris26972CCamera2ShutterSession.kt');g=get('Iris26972CCaptureToGallery.kt');prefs=get('Iris26856ABSettings.java');ui=get('SettingsActivity.java');v=(root/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java').read_text();pre=get('Iris26977CDonorPrewarm.kt');geo=get('Iris26977CPhysicalGeometry.kt')
need(c,'iris26976CTrimOwnRingLocked','mIris26976CExposureEpoch.observeAuto','mIris26976CExposureEpoch.observeLocked','request == mIris26975CProvenRawPreviewRequest','cPreShutterImages.sort','frames - cPreShutterImages.size()','cSequenceFence.takeReleasePermit()','Iris26975CHighlightFreeze.freezeOwnMeter','Iris26975CDonorExposurePolicy.allowHighlightAdjustment','iris26975CMeterOwnRawAtShutter(chars,physical,ss,iso);','mIris26977CPendingPreview.close()','previewTicket.transfer()','cCompleteUiSequence.run()','compareAndSet(false, true)','Iris26977CPhysicalGeometry.freeze','Iris26977CDonorPrewarm.schedule','Iris26977CDonorPrewarm.cancel')
assert 'cHighlightProtection(' not in c+prefs+ui and 'Experiment C highlight protection' not in ui
need(v,'requestCPreview()','PixelCopy.request(this, bitmap','ticket.complete(result, bitmap)')
need(s,'rawTickets.start(timestampNs)','rawTickets.image(timestamp, image)','previewTicket.await(1500L)','previewTicket.close()','captureExposureCompensationEv, donorGeometry','com.particlesdevs.photoncamera.util.Log.e(traceTag, reason, failure)');assert 'Iris26972CEglProcessingOwner.withNewContext' not in s
need(g,'previewThumbnail','captureExposureCompensationEv','donorGeometry.geometry === output.geometry','previewThumbnail, captureExposureCompensationEv, donorGeometry')
need(e,'physicalCrop.rebase(RawMetadata.create(','withNoiseProfileSelection(noiseSelection)','MultiFrameStacker.processBurstRaw','renderer.processMgcSpatialGpuLinearRgb','RawMgcTuningSnr.read(RawMgcTuningSnr.write(','mgcTuningSnr = tuningSnr','DngNoiseProfile.fromMergedModel','capturePreviewThumbnail = capturePreview','captureExposureCompensationEv = transaction.captureExposureCompensationEv','physicalRawCrop = physicalCrop','viewfinderPreviewToCaptureRotationDegrees = previewRotation','rawPhysicalOutputSize = transaction.donorGeometry.nativeOutputSize','normalizeRawHdrReferenceForGainmap(rendered','cropFullRawHdrReferenceToOutput','RawRenderingEngine.AdobeCurve','includeHdrReference = true','Jpeg444ExportEncoder.isJpegR(temporary)','IRIS_26977_C_STAGE','IRIS_26977_C_NOISE')
assert 'capturePreviewThumbnail = null' not in e and e.index('renderer.releaseGpuBayerSource(merged.gpuBayerSource)')<e.index('RawProcessor.prepareRawDngProfile(')
need(pre,'prewarmCapturePipeline(app, RawRenderingEngine.AdobeCurve','RawSceneExposureEstimator.warmUp(app)','memoryClass < 384','isPowerSaveMode','THERMAL_STATUS_MODERATE','job?.cancel()')
need(geo,'RawDigitalZoomResampling.resolveCaptureProperties','RawDigitalZoomResampling.readPhysicalSize','RawProcessor.resolveCameraRawPhysicalCrop')
for x in changed:assert not any(k in x for k in ('/src/main/cpp/','/src/main/assets/','/src/main/jniLibs/'))
assert base['app/build.gradle']==expected['app/build.gradle']
if a.live:
 for n in ('Iris26976CExposureEpoch.java','Iris26976CRawTicketJoin.java','Iris26972CPhysicalRawSpool.kt','Iris26975COriginalRawBurst.kt','RawDemosaicProcessor.kt','RawMgcTuningSnr.kt','MultiFrameStacker.kt','GpuReferenceGainmapProducer.kt'):
  matches=[p for p in base if p.endswith('/'+n)];assert matches and all(base[p]==expected[p] for p in matches),n
 print('PASS historical acquisition and original donor implementation SHA invariance')
print('PASS 26977 C-only preview/PGTM, noise, crop, output, resource and terminal ownership source checks')
