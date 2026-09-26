#!/usr/bin/env python3
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
for t in ['RUNTIME_AUTHORITY_COMMIT="4d72e12e182583189bfc0e5a9ffd031466ee724d"','BASE_RUN_ID="36208117785"','BASE_ARTIFACT_ID="10894838081"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26708_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']: assert t in s,t
m='# IRIS_26708_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(m)==1; main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26707_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26708 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26708 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('stage order',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']: assert t in w,t
print('PASS 26708 infrastructure: successful 26707 stage ordering preserved; authority advanced only to exact 26707 artifact; dual glslang retained')
