#!/usr/bin/env python3
"""26970 exact runtime scope and protected original compiled 26968 source."""
from pathlib import Path
import hashlib,sys,re,subprocess
R=Path(__file__).resolve().parent;P=R if '--live' in sys.argv else R/'handoff_payload_26970'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
def manifest(n):
 d={}
 for line in (R/n).read_text().splitlines():
  h,path=line.split('  ',1);assert re.fullmatch('[a-f0-9]{64}',h) and path.startswith('app/') and path not in d
  d[path]=h
 return d
A=manifest('26970_BASE_26968_FULL_APP.sha256');B=manifest('26970_EXPECTED_FULL_APP.sha256');Q=manifest('26970_PROTECTED_SOURCE.sha256')
changed=set((R/'26970_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines());added=set((R/'26970_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
assert len(A)==2055 and len(B)==2056 and len(changed)==12 and len(added)==1 and len(Q)==2044
assert added=={'app/src/main/cpp/iris26864/bridge/Iris26970BOffGrainEven.comp'}
assert not (R/'26970_DELETED_RUNTIME_PATHS.txt').read_text().strip()
assert set(B)==set(A)|added
assert changed=={p for p in set(A)&set(B) if A[p]!=B[p]}|added
assert Q=={p:h for p,h in A.items() if p not in changed}
assert all(sha(P/p)==B[p] for p in changed)
assert B['app/build.gradle']==A['app/build.gradle']
assert all('vendor/' not in p and 'spektra/' not in p.lower() for p in changed)
assert (P/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726970','VERSION_BUILD=26970']
j=(P/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java').read_text()
c=(P/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
assert j.count('MAX_26970_AUTO_SHUTTER_NS = 71_428_571L')==1 and 'solve26970(' in j and 'rawSceneRemeter26970(' in j
assert c.count('IRIS_26970_B_LIVE_SENSOR_METERING')==1 and 'mMotion26380RawMeanSignal' in c
assert 'STATISTICS_SCENE_FLICKER_50HZ' in c and 'STATISTICS_SCENE_FLICKER_60HZ' in c
assert c.index('halVerifiedFlicker26970') < c.index('mIris26970LockedPeriodNs = iris26948MeasuredPeriodNs')
assert c.count('Iris26909ShutterIsoMath.solve26970(')==1
jni=(P/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
assert jni.count('IRIS_26970_B_OFF_HDRQ_FUSION_INFORMED_LC_GRAIN_EVEN')==1
assert 'sr==JNI_FALSE && photoBOffOnly==JNI_TRUE' in jni and 'hdrqEffectiveChroma==JNI_FALSE' in jni
assert 'result.noiseEstimated' in jni and 'iris26970HdrqResidualMTiles' in jni
assert 'bOffGrain26970->preflight' in jni and 'bWaveletCopy->preflight' in jni
assert 'outputRGB' in (P/'app/src/main/cpp/iris26864/bridge/Iris26970BOffGrainEven.comp').read_text()
assert 'rx_even.comp' not in str(changed) and '26969' not in ' '.join(changed)
for n in ('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/res/xml/preferences.xml', 'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'):
 assert A[n]==B[n],n
if '--live' in sys.argv:
 from importlib.machinery import SourceFileLoader
 m=SourceFileLoader('p26970',str(R/'build_26970_incremental.py')).load_module(); assert m.scan(R)==B
print('PASS 26970 exact 26968 compiled baseline, 11 modified + 1 added, 2044 protected, B OFF <1.10-only grain and sensor-scene AE intent')
