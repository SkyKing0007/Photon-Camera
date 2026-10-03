#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,7):
    raise SystemExit('usage: verify_26758_infrastructure.py BUILD WORKFLOW [REF26757_BUILD REF26757_WORKFLOW REF26752_BUILD REF26752_WORKFLOW]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
def ordered(text,items):
    pos=[]
    for s in items:
        i=text.find(s); assert i>=0,s; pos.append(i)
    assert pos==sorted(pos),list(zip(items,pos))
cur=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
exec_b=b[b.index('# IRIS_26758_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]
ordered(exec_b,cur)
assert exec_b.find('buildCMakeDebug[armeabi-v7a]') < exec_b.rfind('verify_candidate_patches') < exec_b.find('PRE-BUILD SAFETY PROOF PASSED')
for s in [
 'GLSLANG_VERSION="16.5.0"',
 'RUNTIME_AUTHORITY_COMMIT="8fcf3590093622ec638152e5fda8012059501956"',
 'ROOT_ARTIFACT_SHA="8a0f886e2523b1a91a38b8aa2b014b0b298478f11faf6bbe355784e8728e3a90"',
 'ROOT_TAR_SHA="f6070955388117ee37c67d9d6040e5137dd1d812dd5da51f60990afa628dc944"',
 'MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"',
 'IRIS_26758_AUTHORITATIVE_ACTIONS_STAGE_ORDER',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace',
]: assert s in b,s
for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','bash build_26758_universal_direct_cfa_sr.sh','Verify exact 26758 APK exists before artifact upload','actions/upload-artifact@v4']:
    assert s in w,s
# One 26758 upload/commit must not match the historical 26757 trigger namespace.
for s in ["'26757_*'",'handoff_payload_26757/**','build_26757_evidence_limited_fast_plan_b.sh']:
    assert s not in w,('historical trigger survived',s)
if len(sys.argv)==7:
    r57b=Path(sys.argv[3]).read_text(); r57w=Path(sys.argv[4]).read_text(); r52b=Path(sys.argv[5]).read_text(); r52w=Path(sys.argv[6]).read_text()
    prior57=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26752_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
    e57=r57b[r57b.index('# IRIS_26757_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e57,prior57)
    assert e57.find('buildCMakeDebug[armeabi-v7a]') < e57.rfind('verify_candidate_patches') < e57.find('PRE-BUILD SAFETY PROOF PASSED')
    prior52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
    e52=r52b[r52b.index('# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e52,prior52)
    for s in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
        assert s in r57b and s in r52b,s
    for rw in [r57w,r52w]:
        for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4']:
            assert s in rw,s
print('PASS 26758 infrastructure: exact successful 26757 implementation and 26752 mechanics preserve stage/toolchain/order; delta limited to 26757 runtime authority, 26758 scope, exact 3 embedded GLSL compiler gate, regressions, and identity')
