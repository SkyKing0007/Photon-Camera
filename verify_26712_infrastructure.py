#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26712_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="70cd4ecb41ac5638615ec7c72cbc07adb0e9076b"',
'BASE_RUN_ID="36259029955"','BASE_ARTIFACT_ID="10911484034"',
'BASE_ARTIFACT_SHA="ad2d0d136f5e6fc3c68414e8303758265d2b2ea86f61e6e9b4265edd62e2a697"',
'BASE_TAR_SHA="2632350748527eb3efce13e9df0dd30bfcd2e24bc21da2455e8ee0dbf24c9edf"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26712_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'63acc8fa4e850aec5b8701c714545229fd8ef75e684dd821e13e7035e9859289',
'1e8cc3e713d38b8db0dbecb8e7ef22d189fcc60b4bec83c831244975d69b0e22']:
 assert t in s,t
m='# IRIS_26712_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26711_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26712 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26712 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26712_hal_visible_capture_hidden.sh']:
 assert t in w,t
assert 'python3 -S verify_26712_infrastructure.py build_26712_hal_visible_capture_hidden.sh .github/workflows/build-26712-hal-visible-capture-hidden.yml' in w
assert 'exact successful 26711 mechanics' in w
assert 'from successful 26711 compiled authority' in w
print('PASS 26712 infrastructure: exact successful 26711 Actions stage order retained; authority advanced only to successful 26711 compiled artifact; pinned glslang dual handoff retained; no procedure reordering')
