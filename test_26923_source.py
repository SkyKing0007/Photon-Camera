#!/usr/bin/env python3
"""Exact 26922 successful runtime -> 26923 7 changed + 1 new, B ON noise contract."""
from pathlib import Path
import hashlib,sys,subprocess,tempfile
R=Path(__file__).resolve().parent
root=R if '--live' in sys.argv else R/'handoff_payload_26923'
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def manifest(name):return dict((path,h) for h,path in (q.split('  ',1) for q in (R/name).read_text().splitlines()))
a=manifest('26923_BASE_26922_FULL_APP.sha256');b=manifest('26923_EXPECTED_FULL_APP.sha256');protected=manifest('26923_PROTECTED_SOURCE.sha256')
changes=set((R/'26923_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
added=set((R/'26923_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
assert len(a)==2038 and len(b)==2039 and len(changes)==7 and len(added)==1
assert set(b)-set(a)==added and set(a)-set(b)==set()
assert {x for x in a if b[x]!=a[x]}==changes
assert protected=={x:h for x,h in a.items() if x not in changes} and len(protected)==2031
if '--live' in sys.argv:
 current={x.relative_to(R).as_posix():sha(x) for x in (R/'app/src').rglob('*') if x.is_file()}
 for x in ('app/build.gradle','app/version.properties'):current[x]=sha(R/x)
 assert current==b, {'wrong':[x for x in b if current.get(x)!=b[x]][:12]}
else:
 for x in changes|added:assert sha(root/x)==b[x],x
read=lambda x:(root/x).read_text()
base='app/src/main/cpp/iris26864/'
k=read('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
probe=read('app/src/main/java/com/hinnka/mycamera/processor/Iris26920NativeProbe.java')
coord=read(base+'Iris26864RealRawrCoordinator.cpp')
run=read(base+'Iris26864FrozenDirectRawrRunner.cpp')
shadow=read(base+'bridge/Iris26888BOffHdrqCoordinator.cpp')
cmake=read(base+'Iris26864VendorRawr.cmake')
shader=read(base+'bridge/Iris26923WronskiFinalize.comp')
assert 'nativeNoise26923 = Iris26920NativeProbe.takeLastNoise()' in k
assert 'iris26923SrOnNoise = nativeNoise26923' in k
assert 'noiseModelForFrame(ref26922)' not in k
assert 'val n26923 = checkNotNull(iris26923SrOnNoise)' in k
assert 'val nFrames = n26923[1].coerceAtLeast(1f)' in k
assert 'n26923[0]>0.5f' in k and 'RAW_BURST' in k and 'CUSTOM_C' in k
assert 'private static native float[] nativeTakeLastNoise();' in probe
assert 'Iris26920NativeProbe_nativeTakeLastNoise' in run
assert 'iris26923Noise.phase[2u*site]' in run
assert 'result.noiseEstimated || !rawr::raw_merge_wronski_gpu::valid' in run
assert 'iris26923Noise={}' in run and 'iris26923Noise = {}' in run
assert 'wronski.estimateNoiseFromBurst=!(sr && frozen.hasBOffCustomNoise)' in coord
assert 'result.noiseEstimated || !rawr::raw_merge_wronski_gpu::valid' in coord
assert 'wronski.kDenoise=5.0f' in coord and 'wronski.flatSigma=0.90f' in coord and 'alignment.lkIterations=5u' in coord
assert 'if (merge_.outputScale > 1.5f && !fit)' in shadow
assert 'iris26923MeasuredMoments(' in shadow
assert 'no finite RAW-pair noise measurements' in shadow
assert 'merge_.sensorNoiseProfile = fit->profile;' in shadow
assert 'if (fit)' in shadow
assert 'compile_' not in shader
assert shader.startswith('#version 450')
assert 'IRIS_26923_B_SR_ON_NINE_BOUNDED_HR_UPDATES' in shader
assert 'for (int t = 0; t < 3; ++t)' in shader
assert 'for (int step = 0; step < 3; ++step)' in shader
assert 'rgb *= max(currentY+update,1e-6)/max(currentY,1e-6);' in shader and 'dot(rgb,lumWeights)' in shader
assert 'imageLoad(sumI,z)' in shader and 'imageLoad(weightI,z)' in shader
assert cmake.count('Iris26923WronskiFinalize.comp')==1
assert '${IRIS26887_VENDOR_SHADOW}/multiframe/merge_wronski/shaders/a11_finalize.comp' in cmake
assert 'VERSION_BUILD=26923' in read('app/version.properties')
# Historical protected: .c layout, 26917 border, 26920 native LK shader,
# DNG/A/B OFF/long/capture/vendor, shader registry and WRONSKI output size.
for x in a:
 if x.startswith('app/src/main/cpp/iris26864/vendor/'):
  assert a[x]==b[x],x
for x in ('app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp',
 'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'):
 assert a[x]==b[x],x
# Real javac source compile. No Android dependencies in the probe class.
with tempfile.TemporaryDirectory(prefix='p26923_javac_') as d:
 subprocess.run(['javac','-d',d,str(root/'app/src/main/java/com/hinnka/mycamera/processor/Iris26920NativeProbe.java')],check=True)
print('PASS 26923 '+('LIVE' if '--live' in sys.argv else 'PAYLOAD')+' 2038->2039; B ONLY noise source; 9 bounded HR updates; 2031 protected; javac')
