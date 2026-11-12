#!/usr/bin/env python3
"""26922 exact current 7-file B SR ON-only ownership and frozen B OFF regression."""
from pathlib import Path
import hashlib,sys,re
R=Path(__file__).resolve().parent
root=R if '--live' in sys.argv else R/'handoff_payload_26922'
def read(p):return (root/p).read_text()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 return dict((name,h) for h,name in (line.split('  ',1) for line in (R/p).read_text().splitlines()))
old=manifest('26922_BASE_26921_FULL_APP.sha256');new=manifest('26922_EXPECTED_FULL_APP.sha256');protected=manifest('26922_PROTECTED_SOURCE.sha256')
change=set((R/'26922_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
assert len(old)==len(new)==2038 and len(change)==7 and old.keys()==new.keys()
assert {p for p in old if old[p]!=new[p]}==change
assert protected=={p:h for p,h in old.items() if p not in change} and len(protected)==2031
if '--live' in sys.argv:
 present={x.relative_to(root).as_posix():sha(x) for x in (root/'app/src').rglob('*') if x.is_file()}
 for p in ('app/version.properties','app/build.gradle'):present[p]=sha(root/p)
 assert present==new,{'missing':sorted(new.keys()-present.keys())[:6],'extra':sorted(present.keys()-new.keys())[:6],'wrong':[p for p in new if present.get(p)!=new[p]][:6]}
else:
 for p in change: assert sha(root/p)==new[p],p
pref=read('app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26920LensSettings.java')
ui=read('app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
k=read('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
chroma=read('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt')
render=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
frag=read('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag')
assert 'boolean on = experimentB && superResAtShutter;' in pref
assert 'get(context, physical)' not in pref and 'SharedPreferences' not in pref
assert 'putIfAbsent(timestamp, new Snapshot(hash(physical), on))' in pref
assert 'old.lens != hash(physical) || old.enabled != on' in pref
assert '26920 missing physical-lens shutter snapshot' in pref
assert 'new SwitchPreferenceCompat(mContext)' not in ui and 'Lucas-Kanade SR' not in ui
assert 'lens.addPreference(mode);' in ui and 'Iris26856ABSettings.write(mContext, active, next)' in ui
assert 'frozenForReference(refNs26920, refLens26920)' in k
assert 'Iris26920NativeProbe.arm(enabled26920' in k and k.count('Iris26920NativeProbe.clear()')==1
assert 'iris26922SrOnNoiseReference = selectedReference' in k
assert 'val srOn26922 = iris26856BTrue2x &&' in k
assert 'processingWidth == width * 2 && processingHeight == height * 2' in k
assert 'noiseModelForFrame(ref26922)' in k and 'normalizedShotNoiseForShader(cfaPattern)' in k
assert 'uniform1i(applyProgram,"uIris26922SrOn",if(srOn26922) 1 else 0)' in k
assert 'uIris26922ReadVariance' in k and 'uIris26922ShotVariance' in k
assert 'uniform int uIris26922SrOn;' in chroma and 'if(uIris26922SrOn!=0 && y<0.24' in chroma
assert 'float uncertainty=max(localSigma,sigmaFloor);' in chroma
assert 'uIris26922ShotVariance*max(y,0.0)' in chroma and 'dot(vc-center,vc-center)' in chroma
assert 'protectedStructure*agree*visible' in chroma
assert 'float g=y-0.25*(filteredChroma.x+filteredChroma.y)*span;' in chroma
assert render.count('&& !basePipeline.mParameters.motionV2SuperResOutputEnabled) ? 1 : 0);')==2
assert 'iris26906BVisualTone(' not in frag and 'IRIS_26922_B_SR_ON_TONE_RESTORE' in frag
assert frag.startswith('#version 310 es')
assert 'IRIS_26922_B_SRON_MATCHED_HDR_SDR_QUOTIENT' in frag
assert 'float hdrTargetY=sourceY*requested;' in frag
assert 'float matchedRatio=clamp((hdrTargetY+off)/(sdrY+off),1.0,contentMax);' in frag
assert 'float highlightEligibility=smoothstep(0.12,0.58,sourceGuide);' in frag
assert 'ratio=clamp(exp2(log2(max(matchedRatio,1.0))*highlightEligibility),1.0,contentMax);' in frag
assert 'const float hdrEntry=0.65,hdrFullEntry=0.85;' not in frag
assert 'uBOriginal2x' in frag and 'uBFinal1x' in frag and 'uBWhiteBalance' in frag
assert 'VERSION_BUILD=26922' in read('app/version.properties')
# Absence of every B OFF / native / vendor/third-party change is proven by
# manifest equality, rather than brittle 26920 historical --live validators.
for name in (
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp',
 'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake',
):
 assert old[name]==new[name],name
print('PASS 26922 '+('LIVE' if '--live' in sys.argv else 'PAYLOAD')+': 7 exact runtime paths, 2031 immutable; automatic frozen LK only B SR ON; untouched B OFF/native/vendor; spatial noise/hdr/tone gates')
