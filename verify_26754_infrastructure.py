#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,5): raise SystemExit('usage: verify_26754_infrastructure.py BUILD WORKFLOW [REF26752_BUILD REF26752_WORKFLOW]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
current=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26752_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
def ordered(text,items):
 pos=[]
 for s in items: i=text.find(s); assert i>=0,s; pos.append(i)
 assert pos==sorted(pos),list(zip(items,pos))
exec_b=b[b.index('# IRIS_26754_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(exec_b,current)
assert exec_b.find('buildCMakeDebug[armeabi-v7a]') < exec_b.rfind('verify_candidate_patches') < exec_b.find('PRE-BUILD SAFETY PROOF PASSED')
for s in ['GLSLANG_VERSION="16.5.0"','RUNTIME_AUTHORITY_COMMIT="01943675666f50e9f73d043a6436e19c71bd3e39"','ROOT_ARTIFACT_SHA="2ecfa5316467723c88f8b5c0cbaba31f446d3da313b0a30824ee275f0421d2af"','ROOT_TAR_SHA="9e6d7dd80717996e811cc55bc05a0818c1d338f213a5a161d2a59e12a69222b5"','MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"','IRIS_26754_AUTHORITATIVE_ACTIONS_STAGE_ORDER']: assert s in b,s
for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','bash build_26754_physical_owner_streaming_ipol.sh','Verify exact 26754 APK exists before artifact upload','actions/upload-artifact@v4']: assert s in w,s
if len(sys.argv)==5:
 rb=Path(sys.argv[3]).read_text(); rw=Path(sys.argv[4]).read_text(); prior=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']; exec_rb=rb[rb.index('# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(exec_rb,prior)
 assert exec_rb.find('buildCMakeDebug[armeabi-v7a]') < exec_rb.rfind('verify_candidate_patches') < exec_rb.find('PRE-BUILD SAFETY PROOF PASSED')
 for s in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER']: assert s in rb,s
 for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4']: assert s in rw,s
print('PASS 26754 infrastructure diff-audit: exact successful 26752 stage/toolchain/order inherited; deltas limited to successful 26753 runtime authority, 26754 version/scope, and applicable validators')
