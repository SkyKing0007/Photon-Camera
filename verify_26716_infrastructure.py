#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26716_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="86ac112cf76f28f317c8ecdba9c16a1e788dbb4c"',
'BASE_RUN_ID="36282010855"','BASE_ARTIFACT_ID="10919491403"',
'BASE_ARTIFACT_SHA="7729bda8f55dcf2b83c46e15517143a78e541c583c2aa11e0bd3202d7af3c1b5"',
'BASE_TAR_SHA="1dd96bc7046d288e09050447d589652728a71fedf14098bfa394ad69462c84a0"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26716_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'f08b3f9ed5804655d21ad97f095977a8d3d750b44e7e64b3d9a1261fe1742b42',
'31a0b517712473305ba5992b0847197fe2aaa63112f9479e76060b2f060fa115']:
 assert t in s,t
m='# IRIS_26716_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26715_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26716 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26716 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26716_native_iris_log_storage.sh']:
 assert t in w,t
assert 'python3 -S verify_26716_infrastructure.py build_26716_native_iris_log_storage.sh .github/workflows/build-26716-native-iris-log-storage.yml' in w
assert 'exact successful 26715 mechanics' in w
assert 'from successful 26715 compiled authority' in w
print('PASS 26716 infrastructure: exact successful 26715 Actions stage order retained; authority advanced only to successful 26715 compiled artifact; pinned glslang dual handoff retained; no procedure reordering')
