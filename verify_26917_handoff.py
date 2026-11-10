#!/usr/bin/env python3
"""Strict Photon 26917 prebuild SHA seal. Exact successful 26916 source/runner
and ALL original 26916 compiler/build/historical gates are immovable.
"""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26917-change-aware.yml'
PRIOR_WF='.github/workflows/build-26916-change-aware.yml'
PRIOR_BUILDER='build_26916_incremental.py'
PRIOR_WF_SHA='cf4ecae2bd06c89413549b6a197b26df1dc63dee518d7c7927e771c6d86b9c75'
PRIOR_BUILDER_SHA='f1ea60b8987c8e7851941d9c0245e9bc5b9803f0b0169e4d8478bd7b72df62af'
PRIOR_RUN=42741188185
PRIOR_COMMIT='a69515b7eb9d03c688df27618cb0fe7d154ae7ce'
PRIOR_ARTIFACT=13729418513
PRIOR_ART_SHA='c14728619371247dfbf1daedac61aa5ad1c7b2714739db34704aba11be82e2e3'
PRIOR_TAR_SHA='bed8dbcc11f938711695b84f66a5fc6c7a663511dc947b6ceb23576df947cf07'
PRIOR_APK_SHA='60483d9a1436420269ffeb36e39874b22ed804a4f2c808b285b53c37754942c7'
TRIGGER=b'RUN_26917_B_HDRQ_PHYSICAL_CFA_HALO_FROM_26916_V1\n'
STAGED={
 'app/src/main/cpp/iris26856/amaze/include/amaze/Amaze.hpp',
 'app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp',
 'app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp',
 'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/version.properties',
}
GENERATED='app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv'
ALLOWED=STAGED|{GENERATED}
def need(x,msg):
 if not x:raise AssertionError('26917 BLOCKED: '+msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,k=line.split('  ',1)
  need(re.fullmatch('[a-f0-9]{64}',h) is not None and k.startswith('app/') and '..' not in Path(k).parts and k not in d,'invalid/duplicate source manifest path/hash')
  d[k]=h
 return d

def verify():
 stage=(R/'26917_STAGE1_PATHS.txt').read_text().splitlines()
 need(len(stage)>=17 and len(set(stage))==len(stage) and '26917_HANDOFF_HASHES.sha256' in stage,'incomplete/duplicate stage1 inventory')
 need(not any(p.startswith('/') or '..' in Path(p).parts for p in stage),'unsafe stage1 file path')
 receipts={}
 for line in (R/'26917_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h) is not None and p not in receipts,'wrong SHA-sealed inventory')
  receipts[p]=h
 need(set(receipts)==(set(stage)-{'26917_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26917.txt'},'wrong stage1/2/3 hash inventory')
 for p,h in receipts.items():
  f=R/p
  need(f.is_file() and not f.is_symlink() and sha(f)==h,'missing or tampered stage byte '+p)
 need((R/'TRIGGER_26917.txt').read_bytes()==TRIGGER,'wrong last trigger')
 need((R/PRIOR_WF).is_file() and sha(R/PRIOR_WF)==PRIOR_WF_SHA,'successful executed 26916 workflow missing/modified')
 need((R/PRIOR_BUILDER).is_file() and sha(R/PRIOR_BUILDER)==PRIOR_BUILDER_SHA,'successful executed 26916 builder missing/modified')
 base=manifest('26917_BASE_26916_FULL_APP.sha256')
 after=manifest('26917_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 staged=(R/'26917_STAGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 changed=(R/'26917_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 generated=(R/'26917_GENERATED_RUNTIME_PATHS.txt').read_text().splitlines()
 added=(R/'26917_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 deleted=(R/'26917_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
 need(len(base)==len(after)==2036 and base.keys()==after.keys(),'runtime file universe drift')
 need(len(staged)==len(set(staged))==7 and set(staged)==STAGED,'staged source allowlist drift')
 need(len(changed)==len(set(changed))==8 and set(changed)==ALLOWED,'final runtime allowlist drift')
 need(generated==[GENERATED] and not added and not deleted,'generated SPV / added/deleted paths drift')
 need({p for p in base if base[p]!=after[p]}==STAGED and len(base)-len(ALLOWED)==2028,'protected count or source drift')
 need({p for p in stage if p.startswith('handoff_payload_26917/')}=={'handoff_payload_26917/'+p for p in STAGED},'wrong 26917 actual source payload paths')
 for p in STAGED:
  need(sha(R/'handoff_payload_26917'/p)==after[p],'stale staged source '+p)
 for p in base:
  if p not in STAGED and p.startswith(('app/src/main/assets/','app/src/main/cpp/','app/src/main/jniLibs/')):
   need(after[p]==base[p],'protected vendor/native/shader mutation '+p)
 need(base['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'],'26904 export SPV unexpectedly changed')
 need(base['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv']==after[GENERATED],'generated source already altered before real GLSL compiler')
 patch=(R/'26917_FULL_INDEX_FORWARD.patch').read_text()
 need(patch.count('diff --git ')==7 and patch.count('index ')==7 and patch.count('@@ ')>=7,'full-index patch missing or malformed')
 for p in STAGED:need('diff --git a/'+p+' b/'+p+'\n' in patch,'wrong full-index path '+p)
 need('VERSION_BUILD=26917' in (R/'handoff_payload_26917/app/version.properties').read_text(),'version not updated')
 cpp=(R/'handoff_payload_26917/app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp').read_text()
 imp=(R/'handoff_payload_26917/app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp').read_text()
 entry=(R/'handoff_payload_26917/app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
 need('config.phaseSafePhysicalHalo=(!sr && photoBOffOnly == JNI_TRUE);' in entry and 'tileGrid(cfg.width, cfg.height, cfg.phaseSafePhysicalHalo)' in cpp,'incorrect B OFF or SR ON isolation')
 need('iris26917ReflectPhysicalBayer' in imp and 'if (tile.reserved > 0.5)' in imp,'missing real phase-preserving imported CFA')
 java=(R/'handoff_payload_26917/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java').read_text()
 kotlin=(R/'handoff_payload_26917/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 need('photoBOffOnly && !wronskiTrue2x' in java and java.count('boolean photoBOffOnly')==2,'Java/JNI native photo ownership lost')
 need('false, // Wronski B SR ON never owns physical-halo experiment.' in kotlin and
      '!parameters.iris26903NightB && !parameters.irisNightActive' in kotlin,
      'Night/Wronski non-regression gate missing; B photo SR OFF only')
 b=(R/'build_26917_incremental.py').read_text()
 wf=(R/WF).read_text()
 shader_compiler=(R/'compile_26917_amaze_import.sh').read_text()
 for value in [f'RUN={PRIOR_RUN}',f"COMMIT='{PRIOR_COMMIT}'",f'ART_ID={PRIOR_ARTIFACT}',PRIOR_ART_SHA,PRIOR_TAR_SHA,PRIOR_APK_SHA,
               PRIOR_BUILDER_SHA,PRIOR_WF_SHA,
               "get('26916_PREBUILD_SEALED_APP.sha256')",
               "get('ACTUAL_EXECUTED_build_26916_incremental.py')",
               "get('ACTUAL_EXECUTED_build-26916-change-aware.yml')",
               "R/'26917_STAGED_RUNTIME_ALLOWLIST.txt'",
               "R/'26917_CHANGED_RUNTIME_ALLOWLIST.txt'",
               "R/'26917_PRECOMPILE_EXPECTED_FULL_APP.sha256'",
               'if len(apks)!=1:',
               "'REAL KOTLIN COMPILE: PASS'", "'REAL JAVA COMPILE: PASS'", "'NATIVE/NDK COMPILE: PASS'", "'REAL ANDROID Gradle :app:assembleDebug: PASS'",
               'amaze_import_expanded.comp', "'26917_PREBUILD_SEALED_APP.sha256'", "'26917_COMPILER_STATUS.txt'",
               "'ACTUAL_EXECUTED_build_26917_incremental.py'", "'ACTUAL_EXECUTED_build-26917-change-aware.yml'"]:
  need(value in b,'new builder missing mandatory real authority/safety '+value)
 need("'26915_candidate_app_source.tar.gz'" not in b and '26915_success.zip' not in b and "'26915_PREBUILD_SEALED_APP.sha256'" not in b,'stale prior build authority resurrected')
 need('on:\n  push:\n    branches:\n      - experimental-clean-photon-rebuild\n    paths:\n      - TRIGGER_26917.txt' in wf,'wrong 26917 branch/trigger')
 need('TRIGGER_26916.txt' not in wf and 'TRIGGER_26915.txt' not in wf,'historical trigger illegally added to new workflow')
 need(wf.count('actions/upload-artifact@v4')==1 and wf.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'build/one artifact compile altered')
 need(wf.count('compile_26917_amaze_import.sh')==1 and wf.count('compile_26904_shaders_v2.sh')==1,'real pin Vulkan compile missing')
 for cmd in ['verify_26916_handoff.py','test_26916_source.py --payload','test_26916_hue.py --payload','test_26916_patch_proof.py --payload','test_26916_sealed_negatives.py',
             'build_26916_incremental.py seal','test_26912_source.py --payload','test_26913_brightness.py --payload',
             'test_26914_kotlin_owner.py handoff_payload_26914/',
             'test_26914_kotlin_owner.py handoff_payload_26914_v2/',
             'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
             'build_26904_incremental.py seal','test_26904_changeaware.py . --with-javac',
             'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
             'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
             'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
             'test_26907_hue_source.py','test_26908_exposure_render.py','test_26909_exposure.py',
             'test_26910_capture_focus.py','test_26911_continuity.py',
             'test_26917_source.py --payload','test_26917_source.py --live',
             'test_26917_border.py --payload','test_26917_border.py --live',
             'test_26917_patch_proof.py --payload','test_26917_patch_proof.py --live',
             'test_26917_sealed_negatives.py','build_26917_incremental.py fetch',
             'build_26917_incremental.py prepare','build_26917_incremental.py verify-compiled',
             'build_26917_incremental.py finalize','photon_26917_outputs/26917_gradle_assemble.log']:
  need(cmd in wf,'historical/real 26917 regression gate missing '+cmd)
 original=(R/PRIOR_WF).read_text()
 # Existing successful 26916 technical check sequence must remain exact; the
 # only removed commands are the stale live 26916-source checks (would reject
 # the intended new B runtime), now replaced by equivalent 26917 live checks.
 retained=['verify_26916_handoff.py','build_26916_incremental.py seal','test_26906_native_cache.py',
           'test_26907_hue_source.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
           'build_26904_incremental.py seal',
           'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
           'verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
           'compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh', ':app:assembleDebug',
           'verify_26906_native_cache.py postflight','actions/upload-artifact@v4']
 need([wf.index(x) for x in retained]==sorted(wf.index(x) for x in retained),'inherited 26916 historical real build order altered')
 order=['build_26917_incremental.py fetch','build_26917_incremental.py prepare',
        'test_26917_source.py --live','compile_26904_shaders_v2.sh','compile_26917_amaze_import.sh',
        'build_26917_incremental.py verify-compiled', ':app:assembleDebug',
        'build_26917_incremental.py finalize','actions/upload-artifact@v4']
 need([wf.index(x) for x in order]==sorted(wf.index(x) for x in order),'26917 authority/source/GLSL/build/publish sequence altered')
 need(wf.index('id: native-cache')<wf.index('verify_26906_native_cache.py preflight')<wf.index('compile_26904_shaders_v2.sh'),'native cache provenance ordering altered')
 for flag in ['16.5.0','spirv-val --target-env vulkan1.1','spirv-opt --target-env=vulkan1.1 -O','spirv-val --target-env vulkan1.1 "$TARGET/amaze_import.opt.spv"','cmp --silent','$TARGET/amaze_import_expanded.comp']:
  need(flag in shader_compiler,'new native shader compilation gate missing '+flag)
 need('GLSL COMPILE: PASS' in shader_compiler and 'SPIR-V VALIDATION: PASS' in shader_compiler,'not saving genuine shader evidence')
 print('PASS 26917 exact successful 26916 Actions/provenance, sealed 7+1 runtime scope, 2028 protected, 17-stage unchanged GLSL/SPIRV/CMake/NDK/Kotlin/Java/assemble, historical 26886/87/26903/04 regressions')
if __name__=='__main__':verify()
