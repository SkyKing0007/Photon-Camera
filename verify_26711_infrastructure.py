#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26711_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="38db48d5762d1ea1f44601b2b404271eb29e855b"',
'BASE_RUN_ID="36251104057"','BASE_ARTIFACT_ID="10909395982"',
'BASE_ARTIFACT_SHA="7b67cae3376a8afae0357da9e4fda0f3062ba83d2f4b40694ade59fd97962c9c"',
'BASE_TAR_SHA="930678374acbf03c17cce53452158be5d8bd208bfe89b33ef56a451628a5dd91"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26711_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'cda50961f3e150de42756e8be8fd15237e67271ccf0106ae7d8b032c3a1ec33d',
'48158f2932ea26222680b0361589703dd535ee8b787e68eacab962c2f12b70d3']:
 assert t in s,t
m='# IRIS_26711_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26710_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26711 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26711 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26711_locked_reference_lifecycle.sh']:
 assert t in w,t
assert 'python3 -S verify_26711_infrastructure.py build_26711_locked_reference_lifecycle.sh .github/workflows/build-26711-locked-reference-lifecycle.yml' in w
print('PASS 26711 infrastructure: exact successful 26710 Actions stage order retained; authority advanced only to successful 26710 compiled artifact; pinned glslang dual handoff retained; no procedure reordering')
