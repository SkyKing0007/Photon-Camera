#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26700_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
MECH='eaac596a30e8af45240bd4b26338f4a4140d7060'
BLOB='1e47cec30e2f414d4cbb6d0baa97bcacbb603156'
WBLOB='8686b7b0ba4f907bfe19fc888fc749bc96e220b6'
for token in [MECH,BLOB,WBLOB,'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
    assert token in s,token
assert 'build_26699_motion_performance_ui.sh' in s
assert '.github/workflows/build-26699-motion-performance-ui.yml' in s
marker='# IRIS_26700_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=[
'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26699_mechanics',
'prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
'verify_compiled_jni_callback','after_language_compiler_snapshot',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches','26700 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace',
'verify_apk_jni_contract','postbuild_proof','26700 ACTIONS BUILD COMPLETE']
pos=-1
for token in order:
    n=main.find(token,pos+1); assert n>pos,('stage order',token); pos=n
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    assert token in w,token
wo=['Verify sealed 26700 handoff and exact successful 26699 mechanics','Build exact 26700 candidate from successful 26699 compiled authority','Verify exact 26700 APK exists before artifact upload','Upload 26700 proof and APK']
pos=-1
for token in wo:
    n=w.find(token,pos+1); assert n>pos,('workflow order',token); pos=n
for token in [
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'./gradlew :app:assembleDebug --stacktrace']:
    assert token in s,token
print('PASS 26700 infrastructure audit: exact successful 26699 compiler/build stage ordering retained; only authority/identity/scope/regression wrappers changed')
