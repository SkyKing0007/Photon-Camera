#!/usr/bin/env python3
"""Physical current allowlist plus C exposure, shared naming and pre-MPF EXIF contracts."""
import argparse,pathlib,importlib.util
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload^a.live
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26979',R/'build_26979_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
changed,base,expected=b.scope();root=R/'handoff_payload_26979' if a.payload else R
if a.payload:assert {p:b.sha(root/p) for p in changed}=={p:expected[p] for p in changed}
else:b.exact(R,'26979_EXPECTED_FULL_APP.sha256','26979 complete runtime')
def get(n):
 p=list((root/'app/src/main/java').rglob(n));assert len(p)==1,(n,p);return p[0].read_text()
def need(s,*t):
 for x in t:assert x in s,x
c=get('CaptureController.java');t=get('Iris26979CExposureTracking.java');m=get('Iris26975CRawHighlightMeter.java');f=get('TouchFocus.java');session=get('Iris26972CCamera2ShutterSession.kt');pub=get('Iris26975CDonorMediaStorePublisher.java');engine=get('Iris26975CPinnedDonorProEngine.kt');encoder=get('Jpeg444ExportEncoder.kt');exif=get('Iris26979CExif.kt')
need(c,'mIris26979CTracking.resetRequest();','mIris26979CTracking.selectLens(physicalID)','mIris26979CTracking.observeProtection(','mIris26979CTracking.observeAuto(ts,ss,iso,aeState,touch)','mIris26979CTracking.observeLocked(ts,meter.mean,meter.clippedFraction)','mIris26979CTracking.compensation(userComp','CONTROL_AE_REGIONS),mPreviewMeteringAE','CONTROL_AE_ANTIBANDING_MODE,','mIris26975CFactoryPreviewAntibanding','cUserManualExposure || !night ? null :','builder.set(CaptureRequest.SENSOR_EXPOSURE_TIME,ss);','builder.set(CaptureRequest.SENSOR_SENSITIVITY,iso);','iris26978CArmUi(owner);','iris26978CFinishUi(ownerHolder[0]);','mIris26979CTracking.clearProtection();','mIris26979CTouchUpdate ||','total.getRequest()!=mIris26975CProvenRawPreviewRequest','cSequenceFence.takeReleasePermit()')
need(t,'120_000_000L','350_000_000L','Math.pow(2.0,Math.max(0f,appliedEv))','protectionEv=0f','releaseVotes>=2','ratio>=2.0||ratio<=.5');need(m,'highlightSignal','Math.max(p995Max, coherentPeak)');need(f,'iris26979CBeginTouchMetering()','iris26979CEndTouchMetering(cMetering)','if (captureController.iris26975CSelectedForCapture())','builder.set(CaptureRequest.CONTROL_AE_REGIONS, activeTouchRegion);')
need(session,'ImagePath.generateNewFileName("IMG") + ".jpg"','val name = displayName','Iris26976CRawTicketJoin<Image>');assert '"IRIS_C_${shutterMillis}' not in session
need(pub,'validDisplayName(name)','name.length()-19','requireLive(stillLive)','hasOriginalNormalizedExif(verifiedJpegR)')
need(exif,'ParseExif.ExifData()','ParseExif.getTime(requireNotNull(info.exposureTime))','ParseExif.setAllAttributes(base, data)','TAG_PHOTOGRAPHIC_SENSITIVITY','TAG_ORIENTATION','ORIENTATION_NORMAL','android.os.Build.BRAND','exif.saveAttributes()');need(encoder,'baseExifWriter: ((File) -> Unit)? = null','if (baseExifWriter != null) baseExifWriter(baseOutputFile)','else captureInfo?.let { ExifWriter.writeExif(baseOutputFile, it) }');assert encoder.index('baseExifWriter(baseOutputFile)')<encoder.index('writeJpegR(\n                    baseBitmap')
need(engine,'MultiFrameStacker.processBurstRaw','renderer.processMgcSpatialGpuLinearRgb','mgcTuningSnr = tuningSnr','capturePreviewThumbnail = capturePreview','RawRenderingEngine.AdobeCurve','includeHdrReference = true','rawOutputUpscaleMode = proSabre1x.outputUpscaleMode','Iris26978CFinalOutput.prepareSdr(originalSdr)','rawGpuGainmapProducer.build(','baseExifWriter = { base -> Iris26979CExif.write(base, info) }','Iris26979CExif.verify(temporary, info)','Iris26975CDonorMediaStorePublisher.publish(')
assert engine.index('Iris26979CExif.verify(temporary, info)')<engine.index('Iris26975CDonorMediaStorePublisher.publish(')
for x in changed:assert not any(k in x for k in ('/src/main/cpp/','/src/main/assets/','/src/main/jniLibs/'))
assert base['app/build.gradle']==expected['app/build.gradle']
if a.live:
 for n in ('Iris26978CFinalOutput.kt','Iris26976CRawTicketJoin.java','Iris26972CPhysicalRawSpool.kt','Iris26977CDonorPrewarm.kt','RawDemosaicProcessor.kt','RawMgcTuningSnr.kt','MultiFrameStacker.kt','GpuReferenceGainmapProducer.kt','ExifWriter.kt','NoLookLutRawGainmapSidecar.kt','ImagePath.java','ParseExif.java','CameraUIViewImpl.java','CameraFragment.java'):
  matches=[p for p in base if p.endswith('/'+n)];assert matches and all(base[p]==expected[p] for p in matches),n
 print('PASS protected original donor algorithms, UI, shared naming/EXIF helpers and exact RAW spool invariance')
print('PASS 26979 C-only faster tracking, persistent bias, touch settle, prefix and pre-MPF shared EXIF contract')
