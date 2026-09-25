#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26704_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
required=[
'MECHANICS_AUTHORITY_COMMIT="49f4d3d05848714de5763716b1a3afb29832415f"',
'AUTH_26703_BUILD_SCRIPT_BLOB="f6823794a35cc2fef4474895e5bcb2a27e06ac9a"',
'AUTH_26703_WORKFLOW_BLOB="329c218925e5d5901f3629eaac63219836e7a74b"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'build_26703_spektra_full_frame_still_geometry.sh','.github/workflows/build-26703-spektra-full-frame-still-geometry.yml']
for t in required:assert t in s,t
marker='# IRIS_26704_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1
main=s[s.index(marker):]
# Exact successful-26703 outer order retained; only applicable modified-runtime GLSL proof is inserted inside inherited GLSL phase.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26703_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','verify_compiled_jni_callback','verify_compiled_motion_jni','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26704 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','verify_apk_jni_contract','postbuild_proof','26704 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
# Reserved scan happens during candidate validation before pinned compiler stage.
assert s.index('python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee') < s.index('prepare_glslang(){')
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert t in w,t
wo=['Verify sealed 26704 handoff and exact successful 26703 mechanics','Build exact 26704 candidate from successful 26703 compiled authority','Verify exact 26704 APK exists before artifact upload','Upload 26704 proof and APK']
pos=-1
for t in wo:
 n=w.find(t,pos+1);assert n>pos,('workflow order',t);pos=n
push=w.split('workflow_dispatch:',1)[0]
assert '26703_*' not in push and 'handoff_payload_26703' not in push
assert '26704_*' in push and 'handoff_payload_26704/**' in push
print('PASS 26704 infrastructure audit: exact successful 26703 authority/toolchain/outer compiler-build order retained; only required modified-runtime shader proof + 26704 identity/scope/regression wrappers adapted')
