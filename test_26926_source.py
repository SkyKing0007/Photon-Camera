#!/usr/bin/env python3
"""26926: original 26923 authority, B-specific domains, per-lens shutter freeze, no vendor changes."""
from pathlib import Path
import sys,hashlib,re,ast
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26926' if '--payload' in sys.argv else R
root=P/'app/src/main'; java=root/'java';cpp=root/'cpp/iris26864'
def read(path):
 p=P/path; assert p.is_file(),('missing candidate/payload source',path);return p.read_text()
def has(path,*need):
 s=read(path)
 for k in need:assert k in s,(path,k)
 return s
settings='app/src/main/java/com/particlesdevs/photoncamera/settings/'
ui='app/src/main/java/com/particlesdevs/photoncamera/ui/settings/'
proc='app/src/main/java/com/hinnka/mycamera/processor/'
cpp='app/src/main/cpp/iris26864/'
s=has(settings+'Iris26926FallbackSettings.java','DEFAULT_STEPS = {16, 8, 64}','MAX_STEPS = {32, 16, 64}','0.25','putInt','readSteps','freeze(','Snapshot','isValid')
assert 'static final int[] DEFAULT_STEPS' in s and 'Math.round(ticks)' in s
s=has(ui+'custompreferences/Iris26926FallbackSliderPreference.java','R.layout.preference_seekbar','R.id.seekbar_value','0.25 increments','preciseEntry','setMax','getVibration().Tick()')
s=has(ui+'SettingsActivity.java','new Iris26926FallbackSliderPreference','Fallback Chroma Gain','Fallback Luma Gain','Fallback Chroma Max Sigma')
s=has(settings+'Iris26920LensSettings.java','Iris26926FallbackSettings.freeze','entry.fallback.clone()','frozenFallbackForReference','BY_TIMESTAMP.putIfAbsent')
assert 'entry.lens != hash(physical) || !entry.enabled' not in s,'fallback is independent of optional LK arm'
s=has(proc+'Iris26920NativeProbe.java','float[] fallback','nativeArm(enabled, lensIdentity, referenceTimestamp, fallback)')
s=has(proc+'GlesMgcRawSpatialStacker.kt','frozenFallbackForReference','Iris26920NativeProbe.arm','uIris26926ShotByRgb','uIris26926ReadByRgb','uIris26926LensShading','uIris26924BOff','uIris26924ClipPresent','!iris26856BTrue2x')
s=has(cpp+'Iris26864FrozenDirectRawrRunner.cpp','iris26920ArmWasPresent','merge.iris26926Fallback=iris26920Arm.fallback')
s=has(cpp+'Iris26864RealRawrCoordinator.hpp','std::array<float,3> iris26926Fallback{{4.f,2.f,16.f}}')
s=has(cpp+'Iris26864RealRawrCoordinator.cpp','wronski.fallbackChromaGain=','wronski.fallbackLumaGain=','wronski.fallbackChromaMaxSigma=','!std::isfinite')
assert 'frozen.algorithm == RealBEngine::WronskiTrue2x' in s or 'RealBEngine::WronskiTrue2x' in s
s=has(cpp+'bridge/Iris26923WronskiFinalize.comp','IRIS_26926_B_SR_ON_EXACT_LOCAL_MERGE_SUPPORT','imageLoad(sumI,lq).a','rawrRoundHalfRte(vec4(rgb, originalRawConfidence))')
assert 'rawrRoundHalfRte(vec4(rgb, 1))' not in s
s=has(cpp+'Iris26885WronskiChromaGuide.comp','originalRaw.a','src.a=clamp(originalRaw.a','imageStore(amazeRgbInPlace')
s=has(cpp+'Iris26880WaveletCopy.comp','imageLoad(irisRgb,p).a','vec4(denoised,originalRawConfidence)')
s=has(proc+'GlesIris26870PostAmazeChroma.kt','originalRawSupport','burstFloor','uIris26926BurstFrames','uIris26926ShotByRgb','uIris26926ReadByRgb','uIris26926LensShading','connectedMaterial','untrustedClipNeighborhood','uIris26924BOff')
assert 'genuineFine' not in s or 'sourceSupport' in s
s=has(proc+'GlesIris26856RawrFalseColor.kt','uIris26924SensorClip','uIris26924BOff','uIris26924ClipPresent')
if '--live' in sys.argv:
 from build_26926_incremental import exact,scope
 exact(R,'26926_EXPECTED_FULL_APP.sha256','26926 current 2041 complete source')
 ch,add,base,tgt=scope()
 assert all('/vendor/' not in p and '/jniLibs/' not in p for p in ch|add)
 assert len(base)==2039 and len(tgt)==2041 and len(ch)==13 and len(add)==2
 assert tgt['app/version.properties']!=base['app/version.properties']
 assert 'VERSION_BUILD=26926' in (R/'app/version.properties').read_text()
print('PASS 26926 settings 0.25 physical lens/frozen native bridge, actual RAW support through 2x wavelet, B OFF edge/clip, exact source scope')
