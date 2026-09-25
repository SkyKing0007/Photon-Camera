#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26702_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
required=[
'MECHANICS_AUTHORITY_COMMIT="fdc1a06a0fe252de84f0dfde3593927e7c9a428a"',
'AUTH_26701_BUILD_SCRIPT_BLOB="c8c0ce0fea4e3b5b7addd7b7212f4b96946b7a04"',
'AUTH_26701_WORKFLOW_BLOB="84f0c35d972e2d37dc951c4ca9bfdd2a9ec6527b"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'build_26701_highlight_orientation_gainmap.sh','.github/workflows/build-26701-highlight-orientation-gainmap.yml']
for t in required: assert t in s,t
marker='# IRIS_26702_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
# Exact successful-26701 outer compiler/build order. 26702 adds only a native-contract proof adjacent to inherited Java ABI proof.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26701_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','verify_compiled_jni_callback','verify_compiled_motion_jni','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26702 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','verify_apk_jni_contract','postbuild_proof','26702 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('stage order',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert t in w,t
wo=['Verify sealed 26702 handoff and exact successful 26701 mechanics','Build exact 26702 candidate from successful 26701 compiled authority','Verify exact 26702 APK exists before artifact upload','Upload 26702 proof and APK']
pos=-1
for t in wo:
 n=w.find(t,pos+1); assert n>pos,('workflow order',t); pos=n
# No historical overlapping 26701 payload trigger in the new workflow.
push=w.split('workflow_dispatch:',1)[0]
assert '26701_*' not in push and 'handoff_payload_26701' not in push
print('PASS 26702 infrastructure audit: exact successful 26701 compiler/build ordering and toolchain pins retained; only 26702 authority/identity/scope/native-contract/regression wrappers adapted')
