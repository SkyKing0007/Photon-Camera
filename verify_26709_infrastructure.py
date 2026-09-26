#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26709_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="3533de84e8c11a316fa801ea2bd49db9b637cfa9"',
'BASE_RUN_ID="36217077715"','BASE_ARTIFACT_ID="10897738586"',
'BASE_ARTIFACT_SHA="bede299db9fcb0bbff0e0f7ea0d38ffd02a0fc8ba12e5eb5f5bbcf88bb79e56b"',
'BASE_TAR_SHA="59b6bb1106e5c9c72b3af9aebae2dbcf2faf3a972b145640843164830bf1e0c9"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26709_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'4a048c929caecb5bdeee25f4f6d2671b63ca0d480872b2d0a1fe86682f5a156c',
'84e2befce5d6ed9885e8567aa43b0f466a47c550f618243d6bf241deb82b1e4f']:
 assert t in s,t
m='# IRIS_26709_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26708_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26709 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26709 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26709_adaptive_reference_long.sh']:
 assert t in w,t
assert 'python3 -S verify_26709_infrastructure.py build_26709_adaptive_reference_long.sh .github/workflows/build-26709-adaptive-reference-long.yml' in w
print('PASS 26709 infrastructure: exact successful 26708 Actions stage order retained; authority advanced only to successful 26708 compiled artifact; pinned glslang dual handoff retained; only required modified-preview GLSL gate added')
