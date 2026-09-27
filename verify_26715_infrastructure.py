#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26715_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in [
'RUNTIME_AUTHORITY_COMMIT="fc8964770b02a31abdd54a95e08f4e695adf05fa"',
'BASE_RUN_ID="36277122363"','BASE_ARTIFACT_ID="10917945123"',
'BASE_ARTIFACT_SHA="3191fb637395d88308f238c4a834936bfef221a8230153e9aebb2523d26ffc59"',
'BASE_TAR_SHA="4d14c987522d66d363873e62d3c0adc58863a4b43fd0f3fe33581f1ad5ea11c4"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26715_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'3e03cf368518685da72359ad9987d4cd44d81865b3adf4aaf94888c24d0fce57',
'c938de881a5ec49383ace392a7600ec69a62eea05d22eaddd21810c3260f95e0']:
 assert t in s,t
m='# IRIS_26715_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26714_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26715 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26715 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26715_sdr_zsl_iris_logs.sh']:
 assert t in w,t
assert 'python3 -S verify_26715_infrastructure.py build_26715_sdr_zsl_iris_logs.sh .github/workflows/build-26715-sdr-zsl-iris-logs.yml' in w
assert 'exact successful 26714 mechanics' in w
assert 'from successful 26714 compiled authority' in w
print('PASS 26715 infrastructure: exact successful 26714 Actions stage order retained; authority advanced only to successful 26714 compiled artifact; pinned glslang dual handoff retained; no procedure reordering')
