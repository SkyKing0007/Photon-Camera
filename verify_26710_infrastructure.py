#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26710_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="196be5aaaef28383ccea8446328658b2e6336d0d"',
'BASE_RUN_ID="36245295705"','BASE_ARTIFACT_ID="10907700264"',
'BASE_ARTIFACT_SHA="d2548ab2b544004c5e13d66fc6a34d89345ec5be20807cb11d35a81bf3a68d42"',
'BASE_TAR_SHA="b0bc41bbd2721a701fd7d0e3d731812a0990c7827694e8f6342a35a00e313f53"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26710_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'a1f81407498c91c791858e8f65d85c7b9b3cf04cabffb42396d17c47e8a3e1b4',
'd736936e7f2b404354ad156d97b55057072397e3fa98f5a9f4efe1039b090424']:
 assert t in s,t
m='# IRIS_26710_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26709_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26710 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26710 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26710_one_shot_reference_hal_long.sh']:
 assert t in w,t
assert 'python3 -S verify_26710_infrastructure.py build_26710_one_shot_reference_hal_long.sh .github/workflows/build-26710-one-shot-reference-hal-long.yml' in w
print('PASS 26710 infrastructure: exact successful 26709 Actions stage order retained; authority advanced only to successful 26709 compiled artifact; pinned glslang dual handoff retained; no procedure reordering')
