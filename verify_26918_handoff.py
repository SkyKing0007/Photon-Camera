#!/usr/bin/env python3
"""26918 sealed three-stage contract: actual successful 26917 runtime, unchanged
historic successful build stages, full frozen 26917 Bayer-border implementation.
"""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26918-change-aware.yml'
PRIOR_WF='.github/workflows/build-26917-change-aware.yml'
PRIOR_BUILDER='build_26917_incremental.py'
PRIOR_WF_SHA='8d75c66c70ab0c2a6be029a5707e52fea05d3c4a1075ec8be70c04e27ea4afcb'
PRIOR_BUILDER_SHA='31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf'
PRIOR_RUN=42859946714
PRIOR_COMMIT='83ad93725baf8de8fa7653235e93e4fc0ffeaebb'
PRIOR_ARTIFACT=13786011058
PRIOR_ART_SHA='ae09ca810fee66057f173ccc65efbe18772c2561b0c96e8931763da748b2e57b'
PRIOR_TAR_SHA='d82d550362b22a5486098335a41e3817b1417256205c356c6ef837aceb7d68a1'
PRIOR_APK_SHA='3846787d39e59084098d1771f7b8084fd12c86e36157cc098c0961fdf9773c18'
TRIGGER=b'RUN_26918_B_OFF_POST_AMAZE_CHROMA_BYPASS_FROM_26917_V2_RECEIPT_PATH_FIX\n'
CHANGED={
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/version.properties',
}
BORDER={
 'app/src/main/cpp/iris26856/amaze/include/amaze/Amaze.hpp',
 'app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp',
 'app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp',
 'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv',
}
def need(ok,msg):
 if not ok:raise AssertionError('26918 BLOCKED: '+msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(path):
 d={}
 for line in (R/path).read_text().splitlines():
  h,p=line.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h)!=None and p.startswith('app/') and '..' not in Path(p).parts and p not in d,'invalid manifest entry')
  d[p]=h
 return d
def verify():
 stage=(R/'26918_STAGE1_PATHS.txt').read_text().splitlines()
 need(len(stage)>=13 and len(stage)==len(set(stage)) and '26918_HANDOFF_HASHES.sha256' in stage,'stage1 inventory wrong')
 need(not any(p.startswith('/') or '..' in Path(p).parts for p in stage),'unsafe stage1 path')
 receipts={}
 for line in (R/'26918_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h)!=None and p not in receipts,'bad receipt')
  receipts[p]=h
 need(set(receipts)==(set(stage)-{'26918_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26918.txt'},'sealed payload inventory mismatch')
 for p,h in receipts.items():
  f=R/p;need(f.is_file() and not f.is_symlink() and sha(f)==h,'stale/tampered staged file '+p)
 need((R/'TRIGGER_26918.txt').read_bytes()==TRIGGER,'wrong trigger, must upload last')
 need((R/PRIOR_WF).is_file() and sha(R/PRIOR_WF)==PRIOR_WF_SHA,'successful executed 26917 workflow missing/modified')
 need((R/PRIOR_BUILDER).is_file() and sha(R/PRIOR_BUILDER)==PRIOR_BUILDER_SHA,'successful executed 26917 builder missing/modified')
 before=manifest('26918_BASE_26917_FULL_APP.sha256')
 after=manifest('26918_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26918_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 need(len(before)==len(after)==2036 and before.keys()==after.keys(),'runtime source universe changed')
 need(len(changed)==len(set(changed))==3 and set(changed)==CHANGED,'changed allowlist wrong')
 need({p for p in before if before[p]!=after[p]}==CHANGED and 2036-len(CHANGED)==2033,'invalid source scope/protected count')
 need(not (R/'26918_ADDED_RUNTIME_PATHS.txt').read_text().strip() and not (R/'26918_DELETED_RUNTIME_PATHS.txt').read_text().strip(),'added/deleted paths forbidden')
 need({p for p in stage if p.startswith('handoff_payload_26918/')}=={'handoff_payload_26918/'+p for p in CHANGED},'wrong runtime overlay inventory')
 for p in CHANGED:need(sha(R/'handoff_payload_26918'/p)==after[p],'altered actual staged runtime '+p)
 for p in before:
  if p not in CHANGED and p.startswith(('app/src/main/assets/','app/src/main/cpp/','app/src/main/jniLibs/')):
   need(before[p]==after[p],'native/vendor/GLSL or asset drift '+p)
 frozen=manifest('26918_FROZEN_26917_BORDER.sha256')
 need(set(frozen)==BORDER and CHANGED.isdisjoint(BORDER),'seven successful 26917 physical-border hashes missing')
 for p,h in frozen.items():need(before[p]==after[p]==h,'26917 physical CFA border regression '+p)
 patch=(R/'26918_FULL_INDEX_FORWARD.patch').read_text()
 need(patch.count('diff --git ')==3 and patch.count('index ')==3 and patch.count('@@ ')>=3,'wrong full-index patch count')
 for p in CHANGED:need(f'diff --git a/{p} b/{p}\n' in patch,'missing actual full-index change '+p)
 s=(R/'handoff_payload_26918/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
 k=(R/'handoff_payload_26918/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 need(s.count('if(uIris26918BypassSpatialChroma!=0)')==1 and 'vec4(rawrHighlightOff(raw.rgb),raw.a);' in s,'chroma-only fast bypass or original highlight contract missing')
 need(k.count('bPhotoSrOffChromaBypass26918 = true')==1 and
      'bPhotoSrOffChromaBypass26918: Boolean = false' in k and
      '!iris26856BTrue2x && !enableSabreSuperRes && !enableHighZoomDetail' in k,
      'B Photo SR OFF isolation missing')
 need('VERSION_BUILD=26918' in (R/'handoff_payload_26918/app/version.properties').read_text(),'wrong 26918 version')
 builder=(R/'build_26918_incremental.py').read_text();wf=(R/WF).read_text();compile=(R/'compile_26918_post_amaze_glsl.sh').read_text()
 for marker in [f'RUN={PRIOR_RUN}',f"COMMIT='{PRIOR_COMMIT}'",f'ART_ID={PRIOR_ARTIFACT}',PRIOR_ART_SHA,PRIOR_TAR_SHA,PRIOR_APK_SHA,PRIOR_BUILDER_SHA,PRIOR_WF_SHA,
                "get('26917_PREBUILD_SEALED_APP.sha256')", "get('ACTUAL_EXECUTED_build_26917_incremental.py')", "get('ACTUAL_EXECUTED_build-26917-change-aware.yml')",
                "R/'26918_BASE_26917_FULL_APP.sha256'", "R/'26918_PRECOMPILE_EXPECTED_FULL_APP.sha256'",'border(BASE)','border(CAND)','border(R)',
                "'26918_PREBUILD_SEALED_APP.sha256'", "'26918_COMPILER_STATUS.txt'", 'if len(apks)!=1:',
                "'REAL KOTLIN COMPILE: PASS'", "'REAL JAVA COMPILE: PASS'", "'NATIVE/NDK COMPILE: PASS'", "'REAL ANDROID Gradle :app:assembleDebug: PASS'",
                "'ACTUAL_EXECUTED_build_26918_incremental.py'","'ACTUAL_EXECUTED_build-26918-change-aware.yml'"]:
  need(marker in builder,'builder missing real authority/invariance gate '+marker)
 need("'26916_candidate_app_source.tar.gz'" not in builder and "'26915_success.zip'" not in builder,'stale authority in builder')

 # 26918 V2 regression: the *successful* 26917 compiler's actual output
 # directory remains photon_26917_outputs. The wrong 26918-folder lookup
 # caused Actions run 42890269282 to fail after real compilers succeeded.
 need("prior_native=R/'photon_26917_outputs'" in builder and
      "native_glsl=prior_native/'26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt'" in builder and
      "native_spirv=prior_native/'26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt'" in builder and
      "native_optimized=target/'amaze_import.opt.spv'" in builder and
      "sha(native_optimized) not in spirv_receipt" in builder and
      "sha(target/'amaze_import_expanded.comp') not in glsl_receipt" in builder and
      "'glslang 16.5.0' not in glsl_receipt" in builder,
      '26918 V2 inherited real native compiler evidence path/integrity gate missing')
 need("OUT/'26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt'" not in builder and
      "OUT/'26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt'" not in builder,
      'stale incorrect 26918 output-directory reference for 26917 compiler receipts')

 need('on:\n  push:\n    branches:\n      - experimental-clean-photon-rebuild\n    paths:\n      - TRIGGER_26918.txt' in wf,'wrong branch/trigger')
 need('TRIGGER_26917.txt' not in wf and 'TRIGGER_26916.txt' not in wf,'old triggers in new workflow')
 need(wf.count('actions/upload-artifact@v4')==1 and wf.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'mandatory real build altered')
 for cmd in ['verify_26917_handoff.py','test_26917_source.py --payload','test_26917_border.py --payload','test_26917_border.py --live',
             'test_26917_patch_proof.py --payload','test_26917_sealed_negatives.py','build_26917_incremental.py seal',
             'test_26914_kotlin_owner.py handoff_payload_26914/','test_26914_kotlin_owner.py handoff_payload_26914_v2/',
             'verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal','test_26904_changeaware.py . --with-javac',
             'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
             'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh','compile_26917_amaze_import.sh',
             'verify_26918_handoff.py','test_26918_source.py --payload','test_26918_bypass.py --payload','test_26918_patch_proof.py --payload','test_26918_sealed_negatives.py',
             'build_26918_incremental.py fetch','build_26918_incremental.py prepare','test_26918_source.py --live','test_26918_bypass.py --live','test_26918_patch_proof.py --live',
             'compile_26918_post_amaze_glsl.sh','build_26918_incremental.py verify-compiled','build_26918_incremental.py finalize',
             'photon_26918_outputs/26918_gradle_assemble.log','photon_26918_outputs/']:
  need(cmd in wf,'historical real compiler or 26918 stage missing '+cmd)
 need('test_26917_source.py --live' not in wf and 'test_26917_patch_proof.py --live' not in wf,'stale 26917 current-source gate would fail intentional B change')
 order=['verify_26917_handoff.py','build_26917_incremental.py seal','test_26906_native_cache.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal',
        'build_26918_incremental.py fetch','build_26918_incremental.py prepare','test_26917_border.py --live',
        'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh','compile_26917_amaze_import.sh',
        'compile_26918_post_amaze_glsl.sh','build_26918_incremental.py verify-compiled',':app:assembleDebug','verify_26906_native_cache.py postflight','build_26918_incremental.py finalize','actions/upload-artifact@v4']
 need([wf.index(x) for x in order]==sorted(wf.index(x) for x in order),'inherited 26917 17-stage order changed')
 need(wf.index('id: native-cache')<wf.index('verify_26906_native_cache.py preflight')<wf.index('compile_26904_shaders_v2.sh'),'native cache ordering changed')
 need('glslang' in compile and '16.5.0' in compile and 'post_amaze_exact_300.frag' in compile and
      'spirv-val --target-env opengl4.5' in compile and 'spirv-opt --target-env=opengl4.5 -O' in compile and
      "'REAL PINNED GLSL COMPILE: PASS'" not in compile and 'REAL PINNED GLSL COMPILE: PASS' in compile,
      'runtime/real pinned shader compiler downgraded')
 print('PASS 26918 exact 26917 compiled source/runner, 3 changed, 2033 protected, 7 frozen border hashes, unchanged historical 26886/87 26903/26904 V1/V2/V3 and full 17-stage compile gates')
if __name__=='__main__':verify()
