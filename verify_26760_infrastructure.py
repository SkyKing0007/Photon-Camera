#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,7):
    raise SystemExit('usage: verify_26760_infrastructure.py BUILD WORKFLOW [REF26759_BUILD REF26759_WORKFLOW REF26752_BUILD REF26752_WORKFLOW]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
def ordered(text,items):
    pos=[]
    for s in items:
        i=text.find(s); assert i>=0,s; pos.append(i)
    assert pos==sorted(pos),list(zip(items,pos))
cur=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
exec_b=b[b.index('# IRIS_26760_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(exec_b,cur)
assert exec_b.find('buildCMakeDebug[armeabi-v7a]') < exec_b.rfind('verify_candidate_patches') < exec_b.find('PRE-BUILD SAFETY PROOF PASSED')
for s in [
 'GLSLANG_VERSION="16.5.0"',
 'RUNTIME_AUTHORITY_COMMIT="cb2c465091142b221946787945dc002824507267"',
 'ROOT_ARTIFACT_SHA="d575ce8751fe275c29a718d381ba6000199d1f26e896c3a9525ab7e925e37f0c"',
 'ROOT_TAR_SHA="7da9b277a43b7d90a9053f2c6e626d3450eedea7a09faa6f69f8b8ed0fec358a"',
 'MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"',
 'IRIS_26760_AUTHORITATIVE_ACTIONS_STAGE_ORDER',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace',
]: assert s in b,s
for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','bash build_26760_super_res_chroma_denoise.sh','Verify exact 26760 APK exists before artifact upload','actions/upload-artifact@v4']:
    assert s in w,s
# A 26760 upload must not retrigger historical 26758 namespace.
for s in ["'26759_*'",'handoff_payload_26759/**','build_26759_confidence_gated_sr_detail.sh']:
    assert s not in w,('historical trigger survived',s)
if len(sys.argv)==7:
    r59b=Path(sys.argv[3]).read_text(); r59w=Path(sys.argv[4]).read_text(); r52b=Path(sys.argv[5]).read_text(); r52w=Path(sys.argv[6]).read_text()
    prior59=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
    e59=r59b[r59b.index('# IRIS_26759_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e59,prior59)
    assert e59.find('buildCMakeDebug[armeabi-v7a]') < e59.rfind('verify_candidate_patches') < e59.find('PRE-BUILD SAFETY PROOF PASSED')
    prior52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
    e52=r52b[r52b.index('# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e52,prior52)
    for s in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
        assert s in r59b and s in r52b,s
    for rw in [r59w,r52w]:
        for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4']:
            assert s in rw,s
print('PASS 26760 infrastructure: exact successful 26759 implementation and 26752 mechanics preserve stage/toolchain/order; delta limited to 26759 runtime authority, 26760 two-file scope, exact 1 live GLSL compiler gate, regressions, and identity')
