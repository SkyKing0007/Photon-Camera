#!/usr/bin/env python3
"""Photon 26916 exact successful 26915 successor: fail-closed 3-stage seal.
Includes source, historical executed runner/workflow, mandatory real compilers,
original 17-stage order, sparse hue ownership and strictly local shader edits.
"""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26916-change-aware.yml'
PRIOR_WF='.github/workflows/build-26915-change-aware.yml'
PRIOR_BUILDER='build_26915_incremental.py'
PRIOR_WF_SHA='86af9761f142b6b4d21785f432b70ab38cafd36998c26b9cc1d84e6ffd39a2c8'
PRIOR_BUILDER_SHA='c8b4916d02d687eab5fd6af891830c6969f0ce79ddd7ddc58adefe5990f0ebcb'
TRIGGER=b'RUN_26916_UNIVERSAL_HUE_CONTINUITY_FROM_26915_V1\n'
CHANGED={
 'app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java',
 'app/version.properties',
}
def need(x,msg):
 if not x:raise AssertionError('26916 BLOCKED '+msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,k=line.split('  ',1)
  need(re.fullmatch('[a-f0-9]{64}',h) is not None and k.startswith('app/') and '..' not in Path(k).parts and k not in d,'invalid source manifest')
  d[k]=h
 return d

def verify():
 stage=(R/'26916_STAGE1_PATHS.txt').read_text().splitlines()
 need(len(stage)>=16 and len(set(stage))==len(stage) and '26916_HANDOFF_HASHES.sha256' in stage,'stage 1 inventory missing/duplicate')
 need(not any(p.startswith('/') or '..' in Path(p).parts for p in stage),'unsafe stage1 path')
 receipts={}
 for line in (R/'26916_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h) is not None and p not in receipts,'hash seal malformed/duplicate')
  receipts[p]=h
 need(set(receipts)==(set(stage)-{'26916_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26916.txt'},'wrong sealed inventory')
 for p,h in receipts.items():
  f=R/p
  need(f.is_file() and not f.is_symlink() and sha(f)==h,'tampered/missing staged byte '+p)
 need((R/'TRIGGER_26916.txt').read_bytes()==TRIGGER,'altered trigger last')
 need((R/PRIOR_WF).is_file() and sha(R/PRIOR_WF)==PRIOR_WF_SHA,'successful 26915 workflow missing/changed')
 need((R/PRIOR_BUILDER).is_file() and sha(R/PRIOR_BUILDER)==PRIOR_BUILDER_SHA,'successful executed 26915 builder missing/changed')
 before=manifest('26916_BASE_26915_FULL_APP.sha256');after=manifest('26916_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26916_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26916_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 deleted=(R/'26916_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
 need(len(before)==len(after)==2036 and set(before)==set(after),'source universe changed')
 need(len(changed)==len(set(changed))==3 and set(changed)==CHANGED and not added and not deleted,'changed/added/deleted allowlist drift')
 need({p for p in before if before[p]!=after[p]}==CHANGED and 2036-len(changed)==2033,'protected source changed')
 need({p for p in stage if p.startswith('handoff_payload_26916/')}=={'handoff_payload_26916/'+p for p in CHANGED},'source overlay inventory mismatch')
 for p in CHANGED:need(sha(R/'handoff_payload_26916'/p)==after[p],'wrong payload '+p)
 for p in before:
  if p not in CHANGED and p.startswith(('app/src/main/assets/','app/src/main/cpp/','app/src/main/jniLibs/')):
   need(after[p]==before[p],'protected shader/vendor/native drift '+p)
 need(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']=='5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1','pinned AMaZE SPV mutated')
 patch=(R/'26916_FULL_INDEX_FORWARD.patch').read_text()
 need(patch.count('diff --git ')==3 and patch.count('index ')==3 and patch.count('@@ ' )>=3,'full-index patch incomplete')
 for p in CHANGED:need('diff --git a/'+p+' b/'+p in patch,'missing forward patch '+p)
 need((R/'handoff_payload_26916/app/version.properties').read_text().count('VERSION_BUILD=26916')==1,'version not advanced once')
 js=(R/'handoff_payload_26916/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java').read_text()
 glsl=(R/'handoff_payload_26916/app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl').read_text()
 need('off=-1;off<=1;off++' in js and 'MAX_HUE_CHANGE = 0.32f' in js and 'smooth(0.015f,0.065f' in js,'unbounded/unmeasured hue sector fallback')
 need('for(int i=0;i<12;i++)' in glsl and '0.5*delta' not in glsl and '#version' not in glsl,'stepped or wrong GLSL source')
 b=(R/'build_26916_incremental.py').read_text();wf=(R/WF).read_text()
 for value in ["RUN=42699855427", "COMMIT='ad2d2d8ff64f7e02d6483307cd1a79d431400c0b'",
               'ART_ID=13711867064','24c814e59fdfa2ff44034aae5933072ae77ddf620d879c2965f5770f70c50cde',
               '395f8d00dc94a47bda874b90eaa1c82416a6b5131d166f598773828243b1c6c8',
               PRIOR_BUILDER_SHA,PRIOR_WF_SHA,
               "get('26915_PREBUILD_SEALED_APP.sha256')", "get('ACTUAL_EXECUTED_build_26915_incremental.py')",
               "get('ACTUAL_EXECUTED_build-26915-change-aware.yml')",'source=2036 runtime_changed=3 protected=2033 added=0 deleted=0',
               "OUT/'26916_PREBUILD_SEALED_APP.sha256'","OUT/'26916_REAL_HUE_SOURCE_SHA256.txt'",
               "OUT/'ACTUAL_EXECUTED_build_26916_incremental.py'", "OUT/'ACTUAL_EXECUTED_build-26916-change-aware.yml'",
               'if len(apks)!=1:', "'REAL KOTLIN COMPILE: PASS'", "'REAL JAVA COMPILE: PASS'", "'NATIVE/NDK COMPILE: PASS'", "'REAL ANDROID Gradle :app:assembleDebug: PASS'"]:
  need(value in b,'builder authority/invariance gate missing '+value)
 need('26914_v2_candidate_app_source' not in b and '26916_BASE_26914' not in b and '26915_outputs/26915_gradle_assemble' not in b,'stale predecessor output in builder')
 need('experimental-clean-photon-rebuild' in wf and wf.count('TRIGGER_26916.txt')==1,'wrong branch/trigger')
 need('TRIGGER_26915.txt' not in wf and 'TRIGGER_26914.txt' not in wf,'old trigger remains in new workflow')
 need('dev' not in wf.split('branches:')[1].split('paths:')[0],'dev modification risk')
 need(wf.count('build_26916_incremental.py')==5 and wf.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1 and wf.count('actions/upload-artifact@v4')==1,'mandatory real Actions/build/receipt commands changed')
 for k in ['verify_26915_handoff.py','test_26915_source.py --payload',
           'test_26914_kotlin_owner.py handoff_payload_26914/',
           'test_26914_kotlin_owner.py handoff_payload_26914_v2/',
           'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
           'build_26904_incremental.py seal','test_26904_changeaware.py . --with-javac',
           'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
           'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
           'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
           'test_26907_hue_source.py', 'test_26908_exposure_render.py','test_26909_exposure.py',
           'test_26910_capture_focus.py','test_26911_continuity.py','test_26912_source.py --payload',
           'test_26913_brightness.py --payload','test_26914_source.py --payload',
           'test_26916_source.py --payload','test_26916_source.py --live',
           'test_26916_hue.py --payload','test_26916_hue.py --live',
           'test_26916_patch_proof.py --live','test_26916_sealed_negatives.py']:
  need(k in wf,'missing historical or new verification gate '+k)
 seq=['verify_26916_handoff.py','build_26916_incremental.py seal','test_26906_native_cache.py',
      'test_26907_hue_source.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
      'build_26904_incremental.py seal','build_26916_incremental.py fetch',
      'build_26916_incremental.py prepare','verify_26906_native_cache.py preflight',
      'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
      'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh', 'compile_26908_render_glsl.sh',
      'build_26916_incremental.py verify-compiled',':app:assembleDebug',
      'verify_26906_native_cache.py postflight','build_26916_incremental.py finalize','actions/upload-artifact@v4']
 need([wf.index(x) for x in seq]==sorted(wf.index(x) for x in seq),'original 17-stage order changed')
 need(wf.index('id: native-cache')<wf.index('verify_26906_native_cache.py preflight')<wf.index('compile_26904_shaders_v2.sh'),'native cache ordering altered')
 need(wf.index('test_26916_source.py --live')<wf.index('compile_26907_hue_glsl.sh')<wf.index(':app:assembleDebug'),'new semantic/regression/real shader order wrong')
 need('photon_26915_outputs/' not in wf and 'build_26915_incremental.py fetch' not in wf,'stale 26915 generated output reference')
 print('PASS 26916 sealed exact 26915 Actions, 3 changed/2033 protected, original 17-stage pinned GLSL/SPIR-V/Kotlin/Java/NDK/assemble, 26886/87 26903/04 and 26915 historical gates')
if __name__=='__main__':verify()
