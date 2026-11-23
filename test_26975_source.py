#!/usr/bin/env python3
"""SHA-exact 26974->26975 C-only original Sabre source ownership tests."""
import argparse,pathlib,importlib.util,re
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args()
assert a.payload^a.live
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26975',R/'build_26975_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
changed,base,expected=b.scope()
if a.payload:
 d={p:b.sha(R/'handoff_payload_26975'/p) for p in changed}
 assert d=={p:expected[p] for p in changed}
 root=R/'handoff_payload_26975'
else:
 assert b.exact(R,'26975_EXPECTED_FULL_APP.sha256','source validation')==expected
 root=R

def file(p):
 f=root/p
 assert f.is_file(),p
 return f.read_text(encoding='utf-8')
publisher=file('app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26975CDonorMediaStorePublisher.java')
assert 'android.os.Environment.DIRECTORY_DCIM + "/Camera/"' in publisher and 'DCIM/PhotonCamera/' not in publisher
assert 'hasOriginalNormalizedExif(verifiedJpegR)' in publisher
settings=file('app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CProSabre1xSelection.kt')
for token in ('MgcRawMaxMode.SABRE','MgcMergeMethod.SABRE','RawOutputUpscaleMode.LANCZOS3','normalFrameCount in 2..30','outputScale == 1f'):
 assert token in settings,token
engine=file('app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975COriginalDonorEngine.kt')
assert 'private val originalEngine: Engine? = Iris26975CPinnedDonorProEngine' in engine
assert 'check(Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED)' in engine
assert 'Iris26975CDonorStackFrameAdapter.withOriginalDonorFrames' in engine
real=file('app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt')
for token in ('MultiFrameStacker.processBurstRaw','renderer.processMgcSpatialGpuLinearRgb','RawDemosaicProcessor.getInstance()','GpuReferenceGainmapProducer','NoLookLutRawGainmapSidecar.create','HdrGainmapStrength.DEFAULT','Jpeg444ExportEncoder.write','rawRenderingEngine = RawRenderingEngine.AdobeCurve','Iris26975CDonorMediaStorePublisher.publish'):
 assert token in real,token
# Pro RAW-only interface: all YUV photo/HDR mergers and obsolete bjzhou path must be physically absent.
for obsolete in ('app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou',
                 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvStacker.kt'):
 assert not (root/obsolete).exists(),obsolete
stacker=file('app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/MultiFrameStacker.kt')
assert 'fun processBurstRaw(' in stacker and 'GlesMgcRawFusion(' in stacker
assert 'fun processBurst(' not in stacker and 'processHdrBurstYuv(' not in stacker
assert 'embeddedPlan.lookTable == null' in real
assert 'UnifiedGainmapProducer' not in real and 'EstimatedSdrGainmapProducer' not in real
contract=file('app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CContract.java')
assert re.search(r'PRODUCTION_READY\s*=\s*false',contract), 'must not claim production readiness'
assert 'CONTROLLED_DEVICE_TRIAL_ENABLED' in contract
native=file('app/src/main/cpp/iris26975c/Iris26975Original129JniTrampolines.cpp')
assert 'Java_com_hinnka_mycamera_processor_experimentc_original129' in native
build=file('app/build.gradle')
for component in ('litert:2.3.2','litert-gpu:2.3.2','litert-support:2.3.2'):
 assert component in build,component
print(f'PASS {"LIVE" if a.live else "PAYLOAD"} 26975 original Pro Sabre 1x Lanczos3 2..30, original HDR/JPEG-R, Iris DCIM/Camera, strict trial/production gate; {len(changed)} allowlisted changes, {len(base)-22} protected')

# V5: verified donor optional style assets pruned, never the actual RAW processing assets.
if a.live:
 from pathlib import Path
 assetroot=R/'app/src/main/assets/experimentc/original129'
 for name in ("luts", "spektrafilm", "canon", "fotufilm", "lumix", "leica", "hncs", "dcp", "u2netp"):
  assert not (assetroot/name).exists(), "optional style/depth/DCP asset reintroduced: "+name
 for name in ("noise_profiles", "mgc_denoise", "mgc_ae", "mgc_hdrnet", "internal"):
  assert (assetroot/name).is_dir(), "required donor processing asset missing: "+name
 assert "RawRenderingEngine.AdobeCurve" in real and "embeddedDngRenderPlan = embeddedPlan" in real

# V6: no unreferenced frame_glass shader assets may return. The original full
# C-side shader source is preserved in the sealed Kotlin code, not a stale binary.
if a.live:
 assert not (assetroot/"shaders/frame_glass").exists()
 assert not any((assetroot/"shaders").rglob("*.*")) if (assetroot/"shaders").exists() else True
