#!/usr/bin/env python3
"""Photon 26915 exact source scope and source-domain regressions.
No semantic shortcut to full Android Kotlin/Java/NDK/APK compilation in Actions.
"""
from pathlib import Path
import hashlib,sys,re
R=Path(__file__).resolve().parent
MODE='--live' if '--live' in sys.argv else '--payload'
ROOT=(R if (R/'app/src').is_dir() else R/'candidate_26915') if MODE=='--live' else R/'handoff_payload_26915'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest(file):
 out={}
 for line in (R/file).read_text().splitlines():
  h,p=line.split('  ',1)
  assert re.fullmatch('[a-f0-9]{64}',h) and p.startswith('app/') and '..' not in Path(p).parts and p not in out
  out[p]=h
 return out
before=manifest('26915_BASE_26914_V2_FULL_APP.sha256')
after=manifest('26915_PRECOMPILE_EXPECTED_FULL_APP.sha256')
changed=(R/'26915_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
added=(R/'26915_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
deleted=(R/'26915_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
assert len(before)==2035 and len(after)==2036 and len(changed)==7 and len(added)==1 and not deleted
assert len(changed)==len(set(changed)) and len(added)==len(set(added))
assert set(after)-set(before)==set(added) and not (set(before)-set(after))
assert {p for p in before if before[p]!=after[p]}==set(changed)-set(added)
assert len(before)-len(changed)+len(added)==2029
for p in before:
 if p.startswith(('app/src/main/assets/','app/src/main/jniLibs/','app/src/main/cpp/iris26864/')):
  assert before[p]==after[p],p
if MODE=='--payload':
 for p in changed:assert (ROOT/p).is_file() and sha(ROOT/p)==after[p],p
else:
 # Exact live universe includes app/src/** plus the same 2 app metadata files.
 actual={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'app/src').rglob('*') if p.is_file()}
 for p in ['app/build.gradle','app/version.properties']:
  actual[p]=sha(ROOT/p)
 assert actual==after,({'missing':list(after.keys()-actual.keys())[:5],'extra':list(actual.keys()-after.keys())[:5], 'wrong':[p for p in after if actual.get(p)!=after[p]][:8]})
cap=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
math=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26910CaptureSafety.java').read_text()
bridge=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
carrier=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java').read_text()
cpp=(ROOT/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
header=(ROOT/'app/src/main/cpp/iris26915_rgba16f_guide.h').read_text()
assert 'return Iris26910CaptureSafety.frozenNormalPairMatches(' in cap
assert 'MOTION_26486_EXPOSURE_HALF_WINDOW_EV,\n                frozenExperimentB' in cap
assert 'plan.normalTargetIso,\n                        plan.iris26906BOffAllNormal' in cap
assert 'return experiment ==\n                com.particlesdevs.photoncamera.settings.Iris26856ABSettings.Mode.AMAZE_26855;' in cap
assert '&& !superResAtShutter;' not in cap[cap.index('private static boolean iris26905BOffNormalOnly('):cap.index('private void triggerZslCapture(')]
assert 'final boolean iris26593LongBudgetAllows = iris26593TotalTarget >= 2 && !iris26905BOffAllNormal' in cap
assert 'normalTarget=" + iris26757EffectiveNormalTarget' in cap
assert 'mMotion26575SuperResAtShutter = PreferenceKeys.isIrisSuperResOn();' in cap
for k in ['Math.abs(energyEv) > halfWindowEv','Math.abs(shutterEv) <= halfWindowEv','if (!requireShutter) return true']:
 assert k in math,k
assert bridge.count('tryCreateFinal1xGuide(w, h)')==1 and bridge.count('next.writeFinal1xGuideCpu(rgba, sensorMask)')==1
assert 'lockCpu()\n                ?: invalid("26878 1x final guide CPU write map failed")' not in bridge
assert 'true2x' in bridge.lower() and 'wronski' in bridge.lower()
assert 'USAGE_GPU_SAMPLED_IMAGE' in carrier and 'USAGE_CPU_WRITE_OFTEN' in carrier
assert carrier.count('writeFinal1xGuideNative(')==2
assert cpp.count('MotionV2SharedRgba16fCarrier_writeFinal1xGuideNative(')==1
assert 'AHardwareBuffer_lock(buffer,AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN' in cpp
assert 'AHardwareBuffer_unlock(buffer,nullptr)' in cpp
assert '#include "iris26915_rgba16f_guide.h"' in cpp
assert 'iris26915guide::pack(' in cpp
assert 'std::memcpy(dst,src,rowBytes)' in header and 'stridePixels' in header
# Historical 2x Wronski GPU packing untouched. The original API remains for others.
assert 'packWronskiRgbAndClipNative26876' in cpp
assert 'copyFromCurrentGlTextureNative' in cpp
assert (ROOT/'app/version.properties').read_text().count('VERSION_BUILD=26915')==1
print('PASS 26915 '+MODE+' source: 2035->2036, 7 changed incl 1 added, 2029 protected, original Wronski/AMaZE/Night shaders unchanged, B SR full NORMAL and strict frozen pair, stride-aware guide')
