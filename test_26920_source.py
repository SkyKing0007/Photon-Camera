#!/usr/bin/env python3
"""Source-authoritative B ON active 26920: fail closed on any unallowlisted bit.
Host audit is additive; Android Gradle, Vulkan shader, and full NDK compilation
are mandatory in the inherited unchanged successful 26919 workflow.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=(R if (R/'app/src').is_dir() else R/'.photon_26920_work/candidate_26920') if LIVE else R/'handoff_payload_26920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
 d={}
 for ln in (R/name).read_text().splitlines():
  h,p=ln.split('  ',1)
  assert p not in d and re.fullmatch('[a-f0-9]{64}',h) and p.startswith('app/') and '..' not in Path(p).parts
  d[p]=h
 return d
old=read('26920_BASE_26917_FULL_APP.sha256');new=read('26920_PRECOMPILE_EXPECTED_FULL_APP.sha256')
allow=(R/'26920_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
added=(R/'26920_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
assert len(old)==2036 and len(new)==2038 and len(allow)==17 and len(added)==2
assert len(allow)==len(set(allow)) and len(added)==len(set(added))
assert set(new)-set(old)==set(added) and not(set(old)-set(new))
assert {p for p in old if old[p]!=new[p]}==set(allow)-set(added)
assert len(old)-len(allow)+len(added)==2021
for ln in (R/'26920_FROZEN_26917_BORDER.sha256').read_text().splitlines():
 h,p=ln.split('  ',1);assert old[p]==h and new[p]==h,p
for p in old:
 if p.startswith(('app/src/main/assets/','app/src/main/jniLibs/','app/src/main/cpp/iris26856/','app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/')) and p not in allow:assert old[p]==new[p],p
if LIVE:
 current={x.relative_to(ROOT).as_posix():sha(x) for x in (ROOT/'app/src').rglob('*') if x.is_file()}
 for p in ['app/build.gradle','app/version.properties']:current[p]=sha(ROOT/p)
 assert current==new,{'missing':list(new.keys()-current.keys())[:5], 'extra':list(current.keys()-new.keys())[:5], 'wrong':[p for p in new if current.get(p)!=new[p]][:5]}
else:
 for p in allow:assert sha(ROOT/p)==new[p],p
k=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
settings=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
prefs=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26920LensSettings.java').read_text()
capture=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
java=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/Iris26920NativeProbe.java').read_text()
runner=(ROOT/'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp').read_text()
coordinator=(ROOT/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
recorder=(ROOT/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/MultiframeRecorder.cpp').read_text()
android=(ROOT/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/AndroidBurstCoordinator.cpp').read_text()
lk=(ROOT/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp').read_text()
rob=(ROOT/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp').read_text()
assert settings.count('lk.setTitle("Lucas-Kanade SR")')==1
assert settings.count('lens.addPreference(mode);')==1 and settings.count('lens.addPreference(lk);')==1
assert settings.index('lens.addPreference(mode);')<settings.index('lens.addPreference(lk);')
assert 'lk.setIconSpaceReserved(mode.isIconSpaceReserved());' in settings
assert 'Iris26920LensSettings.get(mContext, active)' in settings
assert 'Iris26920LensSettings.set(mContext, active' in settings
assert 'private static final ConcurrentHashMap<Long, Snapshot>' in prefs
assert 'Iris26856ABSettings.identity(physical, null)' in prefs
assert 'mMotion26575SuperResAtShutter)' in capture and 'Iris26920LensSettings.freezeNormal(' in capture
assert 'frozenForReference(refNs26920, refLens26920)' in k
assert k.count('Iris26920NativeProbe.arm(')==1 and k.count('Iris26920NativeProbe.clear()')==1
assert k.count('MotionTrace.processingState("IRIS_26920_B_ON_LK", proof)')==1
assert 'if (iris26856BTrue2x)' in k and 'try {' in k and 'finally {' in k
assert java.count('nativeArm(')==2 and 'System.loadLibrary("iris26856amaze")' in java
assert 'iris26920Arm.armed=false;' in runner and 'merge.iris26920Active=iris26920Enabled;' in runner
assert 'result.iris26920Enabled' in runner and 'enhancedPathApplied=true' in runner
assert 'totalGpuMs=' in runner and 'alignmentGpuMs=' in runner and 'robustnessGpuMs=' in runner
assert 'reason=GPU_RUN_OR_CONSUMER_FAILURE' in runner
for key in ['nativeArm(', 'nativeClear(', 'nativeTakeLastReport(']:assert key in runner
assert 'wronski.iris26920Active = sr && frozen.iris26920Active;' in coordinator
assert 'recordCompanionAlignmentLevel' in recorder and 'iris26920_stats' in recorder
assert 'merge_.iris26920Active' in android and 'vkCmdCopyBuffer' in android and 'iris26920Counts' in android
assert 'if (p.iris26920Active != 0 && p.ts == 16)' in lk and 'H1 < H0 * 0.85' in lk and 'sf += iris26920Step;' in lk
assert 'p.iris26920Active != 0' in rob and 'contribution *= factor;' in rob
assert 'VERSION_BUILD=26920' in (ROOT/'app/version.properties').read_text()
ex=(ROOT/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/VulkanExecutor.cpp').read_text()
assert 'mf compute pipeline shader=' in ex and ' variant=' in ex
assert '{4, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}}}' in ex and '{9, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}}}' in ex
assert not any(p.startswith('app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc') for p in allow)
print('PASS 26920 '+('LIVE' if LIVE else 'PAYLOAD')+' 2036->2038, 17 changed incl 2 added, 2021 protected, 7 frozen 26917 border paths, physical-lens ON active shader-to-fusion and dual log ownership')
