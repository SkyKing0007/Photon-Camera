#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,5): raise SystemExit("usage: verify_26755_infrastructure.py BUILD WORKFLOW [REF26752_BUILD REF26752_WORKFLOW]")
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
def ordered(text,items):
 p=[]
 for s in items:
  i=text.find(s); assert i>=0,s; p.append(i)
 assert p==sorted(p),list(zip(items,p))
cur=["verify_package","verify_scope","obtain_authority","make_candidate","verify_successful_26752_mechanics","prepare_glslang","compile_modified_runtime_shaders","compile_spektra_raw_shader","install_frozen_candidate_live",":app:compileDebugKotlin",":app:compileDebugJavaWithJavac","after_language_compiler_snapshot","buildCMakeDebug[arm64-v8a]","buildCMakeDebug[armeabi-v7a]","PRE-BUILD SAFETY PROOF PASSED",":app:assembleDebug","postbuild_proof"]
exec_b=b[b.index("# IRIS_26755_AUTHORITATIVE_ACTIONS_STAGE_ORDER"):]; ordered(exec_b,cur); assert exec_b.find("buildCMakeDebug[armeabi-v7a]") < exec_b.rfind("verify_candidate_patches") < exec_b.find("PRE-BUILD SAFETY PROOF PASSED")
for s in ['GLSLANG_VERSION="16.5.0"','RUNTIME_AUTHORITY_COMMIT="9dfdc3980bbf1fd7378c6b157793c3200d50fc76"','ROOT_ARTIFACT_SHA="e20320de6c386ab56d56e265131e98c96a71ee89746b0602ead41ff8d7c87391"','ROOT_TAR_SHA="e33636de48a49ad431ad1f19d047d8760e24d0bedb3cc6ba4847b82be21058d7"','MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"','IRIS_26755_AUTHORITATIVE_ACTIONS_STAGE_ORDER']: assert s in b,s
for s in ["java-version: '17'","actions/checkout@v5","actions/setup-java@v5","actions/setup-python@v5","bash build_26755_raw_lifetime_bounded_ipol.sh","Verify exact 26755 APK exists before artifact upload","actions/upload-artifact@v4"]: assert s in w,s
if len(sys.argv)==5:
 rb=Path(sys.argv[3]).read_text(); rw=Path(sys.argv[4]).read_text(); prior=["verify_package","verify_scope","obtain_authority","make_candidate","verify_successful_26751_mechanics","prepare_glslang","compile_modified_runtime_shaders","compile_spektra_raw_shader","install_frozen_candidate_live",":app:compileDebugKotlin",":app:compileDebugJavaWithJavac","after_language_compiler_snapshot","buildCMakeDebug[arm64-v8a]","buildCMakeDebug[armeabi-v7a]","PRE-BUILD SAFETY PROOF PASSED",":app:assembleDebug","postbuild_proof"]; exec_rb=rb[rb.index("# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER"):]; ordered(exec_rb,prior); assert exec_rb.find("buildCMakeDebug[armeabi-v7a]") < exec_rb.rfind("verify_candidate_patches") < exec_rb.find("PRE-BUILD SAFETY PROOF PASSED")
 for s in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER']: assert s in rb,s
 for s in ["java-version: '17'","actions/checkout@v5","actions/setup-java@v5","actions/setup-python@v5","actions/upload-artifact@v4"]: assert s in rw,s
print("PASS 26755 infrastructure diff-audit: exact successful 26752 stage/toolchain/order inherited; deltas limited to 26754 runtime authority, 26755 version/scope, and applicable validators")
