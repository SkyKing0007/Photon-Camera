#!/usr/bin/env python3
"""26976 exact capture-only source identity and independent C owner guards."""
import argparse,pathlib,importlib.util
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload^a.live
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26976',R/'build_26976_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
changed,base,expected=b.scope();root=R/'handoff_payload_26976' if a.payload else R
if a.payload:assert {p:b.sha(root/p) for p in changed}=={p:expected[p] for p in changed}
else:b.exact(R,'26976_EXPECTED_FULL_APP.sha256','26976 full current source')
J='app/src/main/java/'; P=J+'com/particlesdevs/photoncamera/'; K=J+'com/hinnka/mycamera/processor/'; E=P+'processing/experimentc/'
def read(path):return (root/path).read_text()
controller=read(P+'capture/CaptureController.java');session=read(K+'Iris26972CCamera2ShutterSession.kt');spool=read(K+'Iris26972CPhysicalRawSpool.kt');prefs=read(P+'settings/Iris26856ABSettings.java');ui=read(P+'ui/settings/SettingsActivity.java')
# Independent C owner, exact producer request, own epoch, exact actual pair, no copied B allocator.
for token in ('iris26976CTrimOwnRingLocked','iris26976CAdvanceEpoch','mIris26976CExposureEpoch.observeAuto','mIris26976CExposureEpoch.observeLocked','mIris26976CLockedPreviewRequest','IRIS_26976_C_HAL_PAIR_PRESERVED','mIris26976CAdmissionGeneration','request == mIris26975CProvenRawPreviewRequest','reader != mImageReaderRaw','cPostExposure','cPostIso','cPreShutterImages.sort','frames - cPreShutterImages.size()','cSequenceFence.takeReleasePermit()','Iris26975CHighlightFreeze.freezeOwnMeter','Iris26975CDonorExposurePolicy.allowHighlightAdjustment'):
 assert token in controller,token
start=controller.index('private void iris26976CAdvanceEpoch(');end=controller.index('private long mMotionUnifiedExposureNs',start);epoch=controller[start:end]
assert 'mMotion' not in epoch and 'Iris26909' not in epoch and 'Iris26935' not in epoch
assert 'CONTROL_AE_ANTIBANDING_MODE,' not in epoch # never set a new flicker mode
assert 'setRepeatingRequest(next,mCaptureCallback,mBackgroundHandler)' in epoch
assert 'mIris26975CProvenRawPreviewRequest' in epoch and 'C_PRIVATE_RAW' not in epoch.replace('Iris26975CRawHighlightMeter','')
assert 'rawTickets.start(timestampNs)' in session and 'rawTickets.image(timestamp, image)' in session
assert session.count('checkNotNull(spool).offerRaw(image)')==1
assert 'rawTickets.close()' in session and 'state = State.PROCESSING' in session
assert 'metadata.exposureTimeNs == reference.exposureTimeNs' in spool and 'metadata.sensitivityIso == reference.sensitivityIso' in spool
assert 'if (preferences.getBoolean(C_SESSION,false)) return Mode.BJZHOU_26972C;' in prefs
assert 'if(next==Iris26856ABSettings.Mode.BJZHOU_26972C) toRestartApp=true;' in ui
assert 'Experiment C highlight protection' in ui
for path in changed:
 assert '/src/main/cpp/' not in path and '/src/main/assets/' not in path and '/src/main/jniLibs/' not in path and '/processor/experimentc/' not in path
assert base['app/build.gradle']==expected['app/build.gradle']
if a.live:
 # Verify original processing invariance against exact successful actual compiled 26975.
 donor=[p for p in base if p.startswith(K+'experimentc/') or p.startswith('app/src/main/cpp/') or p.startswith('app/src/main/assets/experimentc/') or p.startswith('app/src/main/jniLibs/')]
 assert len(donor)>250 and all(base[p]==expected[p] for p in donor)
 engine=read(K+'experimentc/Iris26975CPinnedDonorProEngine.kt');selection=read(K+'experimentc/Iris26975CProSabre1xSelection.kt')
 for t in ('MultiFrameStacker.processBurstRaw','RawDemosaicProcessor.getInstance()','RawRenderingEngine.AdobeCurve','Jpeg444ExportEncoder.write','HdrGainmapStrength.DEFAULT'):assert t in engine,t
 for t in ('MgcRawMaxMode.SABRE','MgcMergeMethod.SABRE','RawOutputUpscaleMode.LANCZOS3','normalFrameCount in 2..30','outputScale == 1f'):assert t in selection,t
print('PASS 26976 exact capture-only allowlist, donor processing invariance and C owner/epoch guard')
