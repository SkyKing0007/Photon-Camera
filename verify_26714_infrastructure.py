#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26714_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="f92571e8e7d11e5e88d1b74070ba5f1a0119ed2a"',
'BASE_RUN_ID="36273185135"','BASE_ARTIFACT_ID="10916278428"',
'BASE_ARTIFACT_SHA="fe34d8d2a21596785ae96a4c5a234092da4e2d3d57df30e8e3f8e2c63ad26bb6"',
'BASE_TAR_SHA="f8b6bf1eba7bac6071a3c336af58a7e7e5fbf5a74dc4135a3c206293e62228eb"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26714_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'7424aecf1ac772e846ce67c1047b86cb4ed78e2c6cb71a3a9093d5439f7706ec',
'7780c3ff71d994ce67dde89d5c3081127e57dd57a0fc63fe79c094258f00dab2']:
 assert t in s,t
m='# IRIS_26714_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26713_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26714 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26714 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26714_normalized_handheld_highlight.sh']:
 assert t in w,t
assert 'python3 -S verify_26714_infrastructure.py build_26714_normalized_handheld_highlight.sh .github/workflows/build-26714-normalized-handheld-highlight.yml' in w
assert 'exact successful 26713 mechanics' in w
assert 'from successful 26713 compiled authority' in w
print('PASS 26714 infrastructure: exact successful 26713 Actions stage order retained; authority advanced only to successful 26713 compiled artifact; pinned glslang dual handoff retained; no procedure reordering')
