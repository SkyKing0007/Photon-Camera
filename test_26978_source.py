#!/usr/bin/env python3
"""Physical successor source allowlist and exact final output/shared UI contracts."""
import argparse,pathlib,importlib.util
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload^a.live
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26978',R/'build_26978_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
changed,base,expected=b.scope();root=R/'handoff_payload_26978' if a.payload else R
if a.payload:assert {p:b.sha(root/p) for p in changed}=={p:expected[p] for p in changed}
else:b.exact(R,'26978_EXPECTED_FULL_APP.sha256','26978 full current source')
def get(n):
 p=list((root/'app/src/main/java').rglob(n));assert len(p)==1,(n,p);return p[0].read_text()
def need(s,*t):
 for x in t:assert x in s,x
c=get('CaptureController.java');e=get('Iris26975CPinnedDonorProEngine.kt');f=get('Iris26978CFinalOutput.kt');v=get('CameraUIViewImpl.java');u=get('CameraFragment.java')
need(f,'ColorSpace.Named.EXTENDED_SRGB','ColorSpace.Named.SRGB','Bitmap.Config.ARGB_8888, false, srgb','Canvas(target).drawBitmap(source, bounds, bounds, null)','target.colorSpace?.isSrgb == true','Bitmap.Config.RGBA_F16','ColorSpace.Named.LINEAR_EXTENDED_SRGB','LuminanceGainMapEncoding.LINEAR_RATIO','RawGainmapMath.DOWNSAMPLE','target.recycle()');assert 'setColorSpace(' not in f
need(e,'MultiFrameStacker.processBurstRaw','renderer.processMgcSpatialGpuLinearRgb','mgcTuningSnr = tuningSnr','capturePreviewThumbnail = capturePreview','RawRenderingEngine.AdobeCurve','includeHdrReference = true','rawOutputUpscaleMode = proSabre1x.outputUpscaleMode','NoLookLutRawGainmapSidecar.create(checkNotNull(sdr))','Iris26978CFinalOutput.prepareSdr(originalSdr)','Iris26978CFinalOutput.validateHdrPair(checkNotNull(sdr), hdrBitmap)','Iris26978CFinalOutput.validateSidecar','Jpeg444ExportEncoder.isSupported','sdrBase = checkNotNull(sdr)','HdrBuffer(hdrBitmap, HdrBufferEncoding.LINEAR_SRGB)','Jpeg444ExportEncoder.isJpegR(temporary)','gainmapContents?.recycle()','Iris26975CDonorMediaStorePublisher.publish(')
assert e.index('Iris26978CFinalOutput.prepareSdr')<e.index('NoLookLutRawGainmapSidecar.create')<e.index('rawGpuGainmapProducer.build(')<e.index('Jpeg444ExportEncoder.write(')<e.index('Iris26975CDonorMediaStorePublisher.publish(')
need(c,'mIris26978CUiOwner = owner;','CaptureController.isProcessing = true;','iris26978CArmUi(owner);','iris26978CFinishUi(ownerHolder[0]);','iris26978CFinishUi(c)','owner == null || mIris26978CUiOwner != owner','cPreShutterImages.size(); i++','ExposureIndex.time2sec(exposure)','cSequenceFence.takeReleasePermit()','cCompleteUiSequence.run()','cameraEventsListener.onRequestTriggerMediaScanner(uri)')
start=c.index('iris26978CArmUi(owner);');assert start<c.index('owner.activate()',start);assert c.index('cameraEventsListener.onFrameCountSet(frames)',start)<c.index('owner.activate()',start)
terminal=c.index('iris26978CFinishUi(ownerHolder[0]);');assert terminal<c.index('cameraEventsListener.onProcessingFinished("Experiment C capture saved")',terminal)
need(v,'cameraFragment.captureController.iris26978CIsUiBusy()','&& CaptureController.isProcessing','Iris26935BOnSession.isActive() ||')
need(u,'!captureController.iris26978CIsUiBusy()','captureController.iris26978CIsUiBusy())','cameraFragmentViewModel.updateGalleryThumb(fileUri)','"media".equals(fileUri.getAuthority())')
for x in changed:assert not any(k in x for k in ('/src/main/cpp/','/src/main/assets/','/src/main/jniLibs/'))
assert base['app/build.gradle']==expected['app/build.gradle']
if a.live:
 for n in ('Iris26976CExposureEpoch.java','Iris26976CRawTicketJoin.java','Iris26972CPhysicalRawSpool.kt','Iris26972CCamera2ShutterSession.kt','Iris26977CDonorPrewarm.kt','RawDemosaicProcessor.kt','RawMgcTuningSnr.kt','MultiFrameStacker.kt','GpuReferenceGainmapProducer.kt','Jpeg444ExportEncoder.kt','ExifWriter.kt','Iris26975CDonorMediaStorePublisher.java','NoLookLutRawGainmapSidecar.kt'):
  matches=[p for p in base if p.endswith('/'+n)];assert matches and all(base[p]==expected[p] for p in matches),n
 print('PASS original donor algorithm, gainmap, encoder, publisher, acquisition and prewarming SHA invariance')
print('PASS 26978 exact sRGB pixel conversion, aligned HDR/sidecar, JPEG/R publication and C shared UI source contracts')
