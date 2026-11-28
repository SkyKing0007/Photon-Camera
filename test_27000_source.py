import argparse,json
import build_27000_incremental as b
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--live',action='store_true');g.add_argument('--payload',action='store_true');o=p.parse_args();changed,base,expected=b.scope();R=b.R if o.live else b.R/'handoff_payload_27000'
if o.live:b.exact(R,'27000_EXPECTED_FULL_APP.sha256','27000 live source')
else:assert all(b.sha(R/f)==expected[f] for f in changed)
D='app/src/main/java/com/hinnka/mycamera/processor/experimentc/'
U='app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/'
def read(p):return (R/p).read_text()
assert not any('/cpp/' in p or '/assets/' in p or '/jniLibs/' in p or '/processing/' in p for p in changed)
assert len(changed)==12 and base.keys()==expected.keys()
for row in json.loads((b.R/'27000_UPSTREAM_SOURCE_MAP.json').read_text())['files']:
 assert base[row['candidate']]==row['base_candidate_sha256'] and expected[row['candidate']]==row['candidate_sha256']
s=read(D+'Iris26975CPinnedDonorProEngine.kt');assert 'val photo1291 = !transaction.shutter.night' in s and 'useLensSensitivity = photo1291' in s
s=read(D+'original129/raw/RawCaptureProfileCoordinator.kt');assert 'useLensSensitivity: Boolean = false' in s and 'useLensSensitivity = useLensSensitivity' in s
s=read(D+'original129/raw/RawSceneExposureMatcher.kt');assert 'val useLensSensitivity: Boolean get() = false' in s and 'useLensSensitivity = useLensSensitivity' in s
s=read(D+'original129/raw/RawSceneExposureEstimator.kt');assert all(x in s for x in ['referenceSensitivityIso.toDouble() / apertureSquared','else MGC_V25_SENSOR_SENSITIVITY','MGC_V25_SENSOR_SENSITIVITY = 17.61','CAMERA_REF_ISO_OVER_F2','minWhiteBalanceGain','safeUnderexposureTetMs = highlightPreservationTetMs','MGC_DEFAULT_UNSAFE_UNDEREXPOSURE_MULTIPLIER = 1.1f'])
s=read(D+'original129/raw/RawDemosaicProcessor.kt');assert 'request.useLensSensitivity && camera2Transform == null' in s and 'else rawRgbGains' in s
s=read(D+'original129/processor/Iris26998GlesMgcRawSpatialStacker.kt');assert 'renderSabreSourceChroma(accumulatedColor, redX, redY, sourceChroma)' in s and 'renderSourceChroma(converted, saturationThreshold, sourceChroma)' in s and 'Half.toFloat(Half.toHalf(calculationWhiteBalance[0]))' in s and 'GlesMgcRawChromaReconstructionShaders.sabreQuads' in s
s=read(D+'original129/processor/GlesMgcRawChromaReconstructionShaders.kt');assert all(x in s for x in ['vec3 mean = 0.25 * (topLeft + topRight + bottomLeft + bottomRight)','vec4 signal = quad.rggb','vec4 weights = vec4(0.5 * (PHASE_WEIGHT[k].x + PHASE_WEIGHT[k].y))','phase = max(phase, 0.0)','PHASE_WEIGHT[k].xyxy','PHASE_WEIGHT[k].xxyy'])
for file in ['UniversalSeekBarPreference.java','TunableSeekBarPreference.java','MotionIqLabSeekBarPreference.java','Iris26998CAdvancedDenoisePreference.java']:
 s=read(U+file);assert '%.2f' in s and ('currentValueText' in s or 'initialDisplay' in s)
if o.live:
 assert 'Customize SNR Levels' in read('app/src/main/res/xml/preferences.xml')
 assert 'return Iris26998GlesMgcRawSpatialStacker(' in read(D+'original129/processor/GlesMgcRawSabreProcessor.kt')
 assert 'useLensSensitivity = photo1291' not in read(D+'original129/processor/GlesMgcRawSpatialStacker.kt')
print('PASS exact scoped source, Photo-only dynamic sensitivity, donor merged chroma, legacy safeguards and two-decimal settings contracts')
