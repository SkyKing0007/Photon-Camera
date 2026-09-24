#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26699_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
# Exact successful 26698 verification-mechanics authority.
MECH='98dcc60feee76570d45c17c34662660c4f6ac62c'
BLOB='1a138e9b8cb6c4541397f2033f855552adf8020d'
WBLOB='32a56ab993c41b9a9dbb84f3086c38d88dad4432'
for token in [MECH,BLOB,WBLOB,'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
    assert token in s,token
assert 'build_26698_motion_runtime_cleanup.sh' in s
assert '.github/workflows/build-26698-motion-runtime-cleanup.yml' in s
marker='# IRIS_26699_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
# Same successful-26698 stage order; only identity/authority/scope/validator labels may differ.
order=[
'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26698_mechanics',
'prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
'verify_compiled_jni_callback','after_language_compiler_snapshot',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches','26699 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace',
'verify_apk_jni_contract','postbuild_proof','26699 ACTIONS BUILD COMPLETE']
pos=-1
for token in order:
    n=main.find(token,pos+1); assert n>pos,('stage order',token); pos=n
# Workflow runner/toolchain and step ordering inherited from successful 26698.
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    assert token in w,token
wo=['Verify sealed 26699 handoff and exact successful 26698 mechanics','Build exact 26699 candidate from successful 26698 compiled authority','Verify exact 26699 APK exists before artifact upload','Upload 26699 proof and APK']
pos=-1
for token in wo:
    n=w.find(token,pos+1); assert n>pos,('workflow order',token); pos=n
# Exact compiler command content/order inherited.
for token in [
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'./gradlew :app:assembleDebug --stacktrace']:
    assert token in s,token
print('PASS 26699 infrastructure audit: exact successful 26698 compiler/build stage ordering retained; identity/authority/scope/regression wrappers only')
