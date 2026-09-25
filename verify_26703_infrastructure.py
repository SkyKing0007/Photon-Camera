#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26703_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
required=[
'MECHANICS_AUTHORITY_COMMIT="a5f8480b6f8e106e8d7280049ac25b0813e0e2fd"',
'AUTH_26702_BUILD_SCRIPT_BLOB="4a6fdba7c7b3da59cf5c04fff1ec9ff37c2c50ec"',
'AUTH_26702_WORKFLOW_BLOB="994e3e187aace5cd925d9fac1537795b34aae989"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'build_26702_laplacian_ab_spektra_orientation.sh','.github/workflows/build-26702-laplacian-ab-spektra-orientation.yml']
for t in required: assert t in s,t
marker='# IRIS_26703_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
# Exact successful-26702 outer compiler/build order is retained.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26702_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','verify_compiled_jni_callback','verify_compiled_motion_jni','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26703 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','verify_apk_jni_contract','postbuild_proof','26703 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('stage order',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert t in w,t
wo=['Verify sealed 26703 handoff and exact successful 26702 mechanics','Build exact 26703 candidate from successful 26702 compiled authority','Verify exact 26703 APK exists before artifact upload','Upload 26703 proof and APK']
pos=-1
for t in wo:
 n=w.find(t,pos+1); assert n>pos,('workflow order',t); pos=n
push=w.split('workflow_dispatch:',1)[0]
assert '26702_*' not in push and 'handoff_payload_26702' not in push
print('PASS 26703 infrastructure audit: exact successful 26702 compiler/build ordering and toolchain pins retained; only 26703 authority/identity/scope/regression wrappers adapted')
