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
for component in ('litert:2.2.0','litert-support:1.4.2'):
 assert component in build,component
assert not re.search(r"^\s*implementation\s+['\"]com\.google\.ai\.edge\.litert:litert-(?:gpu|support):2\.2\.0['\"]", build, re.M)
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

# V15: exact fixes for all V14 compiler-error root causes.
v15_expected = {'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2Calibration.kt': '80c12bb03ac008ec083902a31eec1f7490c6cc9efc35e65f20ff8723153f5fee', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26975CDonorGuidedV25Gpu.kt': '5b22329f91f6f001c31c9fefe140777569f9e9f0ce99af24e1a9ee5e4b10d5d9', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26975COriginalHdrAfterDenoise.kt': '4c49e45bbcdfd294f41705237932722db838825a0d87fff6363b634109f46e21', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesGraphicsShader.kt': '8c159138030c789b02e3f4ef15b47b59ec74af98b25099e17125d2b4bc8864f1', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcRawBaseFrameSelector.kt': 'afe0dc3da83982d56f7dd2be3798b297d6b0df947530001c592d704c0d55b8fb', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/MgcSpatialRejectionGeometry.kt': 'e3631ce7d60cf5846760d9d1ef7ffe1190a12f1702be8b67a4f6fed3c0ef7334', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/RawStackRegistration.kt': '1d50323e946715d66f6082c01b65d58665d9a543732ae32ad0e3a46124c41b3b', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/NoisePolynomialFit.kt': '53b8aa099a0ebaa9672054da765cbd24c04ed92186a751b055422475ff9d653a', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/utils/RawProcessor.kt': '14c774d90f852d39fc4673569dc7f77ba2ab046b89635bdd37ad4b6d7c97e901'}
for rel, digest in v15_expected.items():
 assert b.sha(root/rel)==digest, "V15 compiler repair drift: "+rel
print("PASS V15 five repaired Kotlin callers and four pinned original donor dependencies")

# Android Camera2 API contract: illuminant 1 is Int, illuminant 2 is Byte.
calibration = file('app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2Calibration.kt')
assert "val first = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)\n" in calibration
assert "val second = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2)?.toInt()\n" in calibration
print("PASS Camera2 documented Integer/Byte illuminant boundary")
