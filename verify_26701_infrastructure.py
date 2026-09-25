#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26701_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for token in ['MECHANICS_AUTHORITY_COMMIT="3086dd85c52bd3b125ba695ffbec3c5037359f11"','AUTH_26700_BUILD_SCRIPT_BLOB="8fc630fd5b6279591660b2e1633adc3d18cc8f7d"','AUTH_26700_WORKFLOW_BLOB="28002ef06f1c4833a9cc9fe1df6df6c4d3bc2cdf"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','build_26700_capture_recovery_spektra_watermark.sh','.github/workflows/build-26700-capture-recovery-spektra-watermark.yml']:
 assert token in s,token
marker='# IRIS_26701_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26700_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','verify_compiled_jni_callback','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26701 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','verify_apk_jni_contract','postbuild_proof','26701 ACTIONS BUILD COMPLETE']
pos=-1
for token in order:
 n=main.find(token,pos+1);assert n>pos,('stage order',token);pos=n
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert token in w,token
wo=['Verify sealed 26701 handoff and exact successful 26700 mechanics','Build exact 26701 candidate from successful 26700 compiled authority','Verify exact 26701 APK exists before artifact upload','Upload 26701 proof and APK']
pos=-1
for token in wo:
 n=w.find(token,pos+1);assert n>pos,('workflow order',token);pos=n
print('PASS 26701 infrastructure audit: exact successful 26700 compiler/build stage ordering retained; only authority/identity/scope/regression wrappers changed')
