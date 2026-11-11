#!/usr/bin/env python3
"""Strict 26919 3-stage seal, real 26918 compiled authority and identical
successful verification procedure plus ADDITIVE clipped-CFA FCC checks.
Protect original 26917 physical-border and 26918 smooth-white WB invariants.
"""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26919-change-aware.yml'
PRIOR_WF='.github/workflows/build-26918-change-aware.yml'
PRIOR_BUILDER='build_26918_incremental.py'
PRIOR_WF_SHA='66babec55970e4cbf341dc5e9a32a4f25215d681723f53a002b7da9725563c28'
PRIOR_BUILDER_SHA='a0012a9bdeafcfe95917cfa43bc91ce84af6cf7132422dcc9f016f8c6e71320b'
PRIOR_RUN=42895817879
PRIOR_COMMIT='00a22e03efa3ed4c5fc80a4e818046201d85760e'
PRIOR_ARTIFACT=13800448678
PRIOR_ART_SHA='e44d33a2c238edeba39655c6a9ac56b9aadb76250a4684a6e940a9f45bddcb68'
PRIOR_TAR_SHA='fb229c8e275e3d52077be7f7e74c46ca8d52dce03184f231c5e88bedc528658c'
PRIOR_APK_SHA='b93ba092f45dfada55cffb06fb9f9017afd15e03332c2ea8cdd8a532f6f27168'
TRIGGER=b'RUN_26919_B_OFF_NATIVE_CLIP_AWARE_FCC_WHITE_FADE_PROTECTED_FROM_26918_V1\n'
CHANGED={
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt',
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
 if not ok:raise AssertionError('26919 BLOCKED '+msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(path):
 d={}
 for line in (R/path).read_text().splitlines():
  h,p=line.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h)!=None and p.startswith('app/') and '..' not in Path(p).parts and p not in d,'malformed source manifest')
  d[p]=h
 return d

def verify():
 stage=(R/'26919_STAGE1_PATHS.txt').read_text().splitlines()
 need(len(stage)>=14 and len(stage)==len(set(stage)) and '26919_HANDOFF_HASHES.sha256' in stage,'stage1 file inventory missing/duplicated')
 need(not any(p.startswith('/') or '..' in Path(p).parts for p in stage),'unsafe stage1 path')
 receipts={}
 for row in (R/'26919_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=row.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h)!=None and p not in receipts,'bad stage hash receipt')
  receipts[p]=h
 need(set(receipts)==(set(stage)-{'26919_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26919.txt'},'wrong three-stage sealed file inventory')
 for p,h in receipts.items():
  f=R/p
  need(f.is_file() and not f.is_symlink() and sha(f)==h,'missing/tampered staged file '+p)
 need((R/'TRIGGER_26919.txt').read_bytes()==TRIGGER,'trigger differs; upload final')
 need((R/PRIOR_WF).is_file() and sha(R/PRIOR_WF)==PRIOR_WF_SHA,'successful 26918 executed workflow missing/tampered')
 need((R/PRIOR_BUILDER).is_file() and sha(R/PRIOR_BUILDER)==PRIOR_BUILDER_SHA,'successful 26918 executed builder missing/tampered')
 before=manifest('26919_BASE_26918_FULL_APP.sha256')
 after=manifest('26919_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26919_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 need(len(before)==len(after)==2036 and before.keys()==after.keys(),'runtime 2036 source scope changed')
 need(len(changed)==len(set(changed))==3 and set(changed)==CHANGED,'three-only allowlist changed')
 need({p for p in before if before[p]!=after[p]}==CHANGED and 2036-len(CHANGED)==2033,'protected runtime files changed')
 for p in ('26919_ADDED_RUNTIME_PATHS.txt','26919_DELETED_RUNTIME_PATHS.txt'):
  need(not (R/p).read_text().strip(),'unexpected added/deleted runtime source')
 need({p for p in stage if p.startswith('handoff_payload_26919/')}=={'handoff_payload_26919/'+p for p in CHANGED},'runtime overlay inventory differs')
 for p in CHANGED:need(sha(R/'handoff_payload_26919'/p)==after[p],'stale/tampered runtime source '+p)
 for p in before:
  if p not in CHANGED and p.startswith(('app/src/main/assets/','app/src/main/cpp/','app/src/main/jniLibs/')):
   need(before[p]==after[p],'protected native/vendor/shader mutated '+p)
 frozen=manifest('26919_FROZEN_26917_BORDER.sha256')
 need(set(frozen)==BORDER and not (BORDER&CHANGED),'missing frozen 26917 seven source/SPV hashes')
 for p,h in frozen.items():need(before[p]==after[p]==h,'26917 physical CFA border regression '+p)
 # Smooth-white WB is the exact successful 26918 file; no new painting or
 # loss of previously proved OFF smooth fade to white is authorized.
 wb='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
 need(before[wb]==after[wb] and wb not in CHANGED,'smooth-white WB/common-ceiling altered')
 patch=(R/'26919_FULL_INDEX_FORWARD.patch').read_text()
 need(patch.count('diff --git ')==3 and patch.count('index ')==3 and patch.count('@@ ' )>=3,'full index patch malformed')
 for p in CHANGED:need(f'diff --git a/{p} b/{p}' in patch,'patch omits runtime path '+p)
 median=(R/'handoff_payload_26919/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt').read_text()
 stack=(R/'handoff_payload_26919/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 need(median.count('uniform int uClipAwareBOff26919;')==2 and median.count('uniform sampler2D uOriginalSensorClip26919;')==2,'new median/reconstruction real CFA clip uniforms missing')
 need('if(clippedCenter){oRgb=src;return;}' in median and 'nearOriginalClipping(p)' in median and 'if(wSum<=1.0e-6){oRgb=src;return;}' in median,'clipped center or neutral guard removed')
 need('p.x>=4 && p.y>=4 && p.x<uSize.x-4 && p.y<uSize.y-4' in median,'four-border color guard missing')
 need(stack.count('bPhotoSrOffClipAwareFcc26919 = true')==1 and
      'bPhotoSrOffClipAwareFcc26919: Boolean = false' in stack and
      'bPhotoSrOffChromaBypass26918 && nativeSensorClipFullRes26866 != 0' in stack and
      '!iris26856BTrue2x && !enableSabreSuperRes && !enableHighZoomDetail' in stack,'B OFF-only clip source gate missing')
 need('edgeSigma = 0f, chromaBound = 0f' in stack,'RAWR post-FCC policy unexpectedly changed')
 need('VERSION_BUILD=26919' in (R/'handoff_payload_26919/app/version.properties').read_text(),'version not advanced')
 builder=(R/'build_26919_incremental.py').read_text();wf=(R/WF).read_text();compiler=(R/'compile_26919_fcc_glsl.sh').read_text()
 for value in [f'RUN={PRIOR_RUN}',f"COMMIT='{PRIOR_COMMIT}'",f'ART_ID={PRIOR_ARTIFACT}',PRIOR_ART_SHA,PRIOR_TAR_SHA,PRIOR_APK_SHA,PRIOR_BUILDER_SHA,PRIOR_WF_SHA,
               "get('26918_PREBUILD_SEALED_APP.sha256')","get('ACTUAL_EXECUTED_build_26918_incremental.py')","get('ACTUAL_EXECUTED_build-26918-change-aware.yml')",
               "R/'26919_BASE_26918_FULL_APP.sha256'","R/'26919_PRECOMPILE_EXPECTED_FULL_APP.sha256'",'border(BASE)','border(CAND)','border(R)',
               "'26919_PREBUILD_SEALED_APP.sha256'","'26919_COMPILER_STATUS.txt'",'if len(apks)!=1:',
               "'REAL KOTLIN COMPILE: PASS'","'REAL JAVA COMPILE: PASS'","'NATIVE/NDK COMPILE: PASS'","'REAL ANDROID Gradle :app:assembleDebug: PASS'",
               "'ACTUAL_EXECUTED_build_26919_incremental.py'","'ACTUAL_EXECUTED_build-26919-change-aware.yml'"]:
  need(value in builder,'new builder missing successful authority / real compiler gate '+value)
 # Explicitly defend against prior 26918 V1 failing native SPV receipt path.
 need("prior_native=R/'photon_26917_outputs'" in builder and
      "native_glsl=prior_native/'26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt'" in builder and
      "native_spirv=prior_native/'26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt'" in builder and
      "receipt=R/'photon_26918_outputs/26918_CHROMA_SHADER_REAL_COMPILER.txt'" in builder and
      "validation=R/'photon_26918_outputs/26918_CHROMA_SHADER_SPIRV_VALIDATED.txt'" in builder and
      "fcc_receipt=OUT/'26919_FCC_SHADER_REAL_COMPILER.txt'" in builder and
      "fcc_val=OUT/'26919_FCC_SHADER_SPIRV_VALIDATED.txt'" in builder and
      "OUT/'26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt'" not in builder and
      "OUT/'26918_CHROMA_SHADER_REAL_COMPILER.txt'" not in builder,
      'inherited compiler output folder error reintroduced')
 need('on:\n  push:\n    branches:\n      - experimental-clean-photon-rebuild\n    paths:\n      - TRIGGER_26919.txt' in wf,'wrong branch/new trigger')
 need('TRIGGER_26918.txt' not in wf and 'TRIGGER_26917.txt' not in wf and 'TRIGGER_26916.txt' not in wf,'old workflow trigger')
 need(wf.count('actions/upload-artifact@v4')==1 and wf.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'real Gradle/Android/artifact stage absent')
 for x in ['verify_26918_handoff.py','test_26918_source.py --payload','test_26918_bypass.py --payload','test_26918_patch_proof.py --payload','test_26918_sealed_negatives.py','build_26918_incremental.py seal',
           'test_26917_border.py --live','verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal','test_26904_changeaware.py . --with-javac',
           'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
           'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh','compile_26917_amaze_import.sh','compile_26918_post_amaze_glsl.sh',
           'verify_26919_handoff.py','test_26919_source.py --payload','test_26919_clip_fcc.py --payload','test_26919_patch_proof.py --payload','test_26919_sealed_negatives.py',
           'build_26919_incremental.py fetch','build_26919_incremental.py prepare','test_26919_source.py --live','test_26919_clip_fcc.py --live','test_26919_patch_proof.py --live',
           'compile_26919_fcc_glsl.sh','build_26919_incremental.py verify-compiled','build_26919_incremental.py finalize',
           'photon_26919_outputs/26919_gradle_assemble.log','photon_26919_outputs/']:
  need(x in wf,'historical or additive build gate missing '+x)
 order=['verify_26918_handoff.py','build_26918_incremental.py seal','test_26906_native_cache.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal',
        'build_26919_incremental.py fetch','build_26919_incremental.py prepare','test_26917_border.py --live','verify_26906_native_cache.py preflight',
        'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
        'compile_26917_amaze_import.sh','compile_26918_post_amaze_glsl.sh','compile_26919_fcc_glsl.sh','build_26919_incremental.py verify-compiled',':app:assembleDebug','verify_26906_native_cache.py postflight','build_26919_incremental.py finalize','actions/upload-artifact@v4']
 need([wf.index(x) for x in order]==sorted(wf.index(x) for x in order),'actual successful 26918 17-stage compiler/assembly order modified')
 need(wf.index('id: native-cache')<wf.index('verify_26906_native_cache.py preflight')<wf.index('compile_26904_shaders_v2.sh'),'native source fingerprint cache order modified')
 need('test_26918_source.py --live' not in wf and 'test_26918_patch_proof.py --live' not in wf,'stale 26918 current source gate')
 need('16.5.0' in compiler and 'medianChroma' in compiler and 'reconstructChroma' in compiler and 'spirv-val --target-env opengl4.5' in compiler and 'spirv-opt --target-env=opengl4.5 -O' in compiler and 'exact_300.frag' in compiler,'real pinned FCC shader compiler downgraded')
 print('PASS 26919 exact successful 26918 authority/runner, 3 changed, 2033 protected, 7 frozen 26917 border, untouched 26918 white fade, original 17-stage historical regressions and real pinned shader/NDK/Kotlin/Java/assemble')
if __name__=='__main__':verify()
