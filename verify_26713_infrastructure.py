#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26713_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="555c2ffe82a00c63cd2672caada2fcd29d86e053"',
'BASE_RUN_ID="36266857647"','BASE_ARTIFACT_ID="10913954559"',
'BASE_ARTIFACT_SHA="92dd5c78ef76db827ba68c7c19bf1e5a3d9f7a7f9dd4b2fcd22d44876c08ae18"',
'BASE_TAR_SHA="74d6199fdf0257454cf92e9d12c12bb7958f07c135f93b5a71aac93a3ca3cf80"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26713_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'2d97fd4802a52290a93392a442a5bfecf16652bfba5a853879a4f701ffdf2851',
'4cc1cf4112ff413a2e6244b336e0f77683eab2c0287a9c3cf78ab5cb9b0dc3d6']:
 assert t in s,t
m='# IRIS_26713_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26712_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26713 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26713 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26713_capture_domain_exposure.sh']:
 assert t in w,t
assert 'python3 -S verify_26713_infrastructure.py build_26713_capture_domain_exposure.sh .github/workflows/build-26713-capture-domain-exposure.yml' in w
assert 'exact successful 26712 mechanics' in w
assert 'from successful 26712 compiled authority' in w
print('PASS 26713 infrastructure: exact successful 26712 Actions stage order retained; authority advanced only to successful 26712 compiled artifact; pinned glslang dual handoff retained; no procedure reordering')
