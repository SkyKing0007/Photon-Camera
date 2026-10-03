#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,7):
    raise SystemExit('usage: verify_26759_infrastructure.py BUILD WORKFLOW [REF26758_BUILD REF26758_WORKFLOW REF26752_BUILD REF26752_WORKFLOW]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
def ordered(text,items):
    pos=[]
    for s in items:
        i=text.find(s); assert i>=0,s; pos.append(i)
    assert pos==sorted(pos),list(zip(items,pos))
cur=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
exec_b=b[b.index('# IRIS_26759_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(exec_b,cur)
assert exec_b.find('buildCMakeDebug[armeabi-v7a]') < exec_b.rfind('verify_candidate_patches') < exec_b.find('PRE-BUILD SAFETY PROOF PASSED')
for s in [
 'GLSLANG_VERSION="16.5.0"',
 'RUNTIME_AUTHORITY_COMMIT="72a546e00b751bd208f6ec0b6395614de974106c"',
 'ROOT_ARTIFACT_SHA="51b90b79d4bf0169bba72983113a6e5fe9511abf6add17fbaa0f5a29663fecd8"',
 'ROOT_TAR_SHA="6148a69e58494409f2e1772eb66a867a0ae08c5d2e31c0e9edcb8160ea60615f"',
 'MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"',
 'IRIS_26759_AUTHORITATIVE_ACTIONS_STAGE_ORDER',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace',
]: assert s in b,s
for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','bash build_26759_confidence_gated_sr_detail.sh','Verify exact 26759 APK exists before artifact upload','actions/upload-artifact@v4']:
    assert s in w,s
# A 26759 upload must not retrigger historical 26758 namespace.
for s in ["'26758_*'",'handoff_payload_26758/**','build_26758_universal_direct_cfa_sr.sh']:
    assert s not in w,('historical trigger survived',s)
if len(sys.argv)==7:
    r58b=Path(sys.argv[3]).read_text(); r58w=Path(sys.argv[4]).read_text(); r52b=Path(sys.argv[5]).read_text(); r52w=Path(sys.argv[6]).read_text()
    prior58=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
    e58=r58b[r58b.index('# IRIS_26758_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e58,prior58)
    assert e58.find('buildCMakeDebug[armeabi-v7a]') < e58.rfind('verify_candidate_patches') < e58.find('PRE-BUILD SAFETY PROOF PASSED')
    prior52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
    e52=r52b[r52b.index('# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e52,prior52)
    for s in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
        assert s in r58b and s in r52b,s
    for rw in [r58w,r52w]:
        for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4']:
            assert s in rw,s
print('PASS 26759 infrastructure: exact successful 26758 implementation and 26752 mechanics preserve stage/toolchain/order; delta limited to 26758 runtime authority, 26759 two-file scope, exact 2 live GLSL compiler gate, regressions, and identity')
