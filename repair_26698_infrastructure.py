#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26698_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
# Exact successful 26697 verification-mechanics authority.
MECH='007440f59feac3788de3e00df67b5e406fc2ce25'
BLOB='181dfef3ad75d3cd9d10b36193165a1ba997e767'
WBLOB='b1c075c8f2e922948e8eef7be3b01177b83b127e'
for token in [MECH,BLOB,WBLOB,'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
 assert token in s,token
marker='# IRIS_26698_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1
main=s[s.index(marker):]
# Same successful-26697 stage order; only identity/authority/scope filenames are allowed to differ.
order=[
'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26697_mechanics',
'prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
'verify_compiled_jni_callback','after_language_compiler_snapshot',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches','26698 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace',
'verify_apk_jni_contract','postbuild_proof','26698 ACTIONS BUILD COMPLETE']
pos=-1
for token in order:
 n=main.find(token,pos+1);assert n>pos,('stage order',token);pos=n
# Workflow runner/toolchain and step ordering copied from successful 26697.
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert token in w,token
wo=['Verify sealed 26698 handoff and exact successful 26697 mechanics','Build exact 26698 candidate from successful 26697 compiled authority','Verify exact 26698 APK exists before artifact upload','Upload 26698 proof and APK']
pos=-1
for token in wo:
 n=w.find(token,pos+1);assert n>pos,('workflow order',token);pos=n
# Exact compiler command content/order inherited.
for token in [
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'./gradlew :app:assembleDebug --stacktrace']:
 assert token in s,token
print('PASS 26698 infrastructure audit: exact successful 26697 compiler/build stage ordering retained; identity/authority/scope/regression wrappers only')
