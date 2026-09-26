#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26707_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for t in ['MECHANICS_AUTHORITY_COMMIT="9523e5d8a72e687385ba7fe9000072cb915404a1"','AUTH_26706_COMMIT="de9a18d08aabaaa490a75b50324567fc4651a39e"','AUTH_26706_BUILD_SCRIPT_BLOB="1852e9643caa3d17ef13b9b13ff0013aea712764"','AUTH_26706_WORKFLOW_BLOB="1b28ffd83b1f2975415a148c66e90e56fedce552"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
 assert t in s,t
assert s.count('export IRIS26707_GLSLANG="$compiler"')==1
assert s.count('export IRIS26681_SPEKTRA_GLSLANG="$compiler"')==1
prep=s[s.index('prepare_glslang(){'):s.index('compile_modified_runtime_shaders(){')]
for t in ['export IRIS26707_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:assert t in prep
marker='# IRIS_26707_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26706_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','verify_compiled_jni_callback','verify_compiled_motion_jni','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26707 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','verify_apk_jni_contract','postbuild_proof','26707 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:assert t in w,t
# R1 marker regression remains.
assert "b'iris26704BodyToneStrength'" in s and "b'iris26707BodyToneStrength'" in s
print('PASS 26707 infrastructure audit revised: exact successful 26706/26704 compiler-build ordering + dual glslang + inherited body-tone marker regression retained; runtime proof expanded only for 5-file scope and 2 modified embedded shaders')
