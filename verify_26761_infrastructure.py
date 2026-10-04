#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv) not in (3,7):
 raise SystemExit('usage: verify_26761_infrastructure.py BUILD WORKFLOW [REF26760_BUILD REF26760_WORKFLOW REF26752_BUILD REF26752_WORKFLOW]')
bp,wp=Path(sys.argv[1]),Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text()
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ordered(text,items):
 pos=[]
 for s in items:
  i=text.find(s); assert i>=0,s; pos.append(i)
 assert pos==sorted(pos),list(zip(items,pos))
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
exec_b=b[b.index('# IRIS_26761_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(exec_b,stages)
assert exec_b.find('buildCMakeDebug[armeabi-v7a]') < exec_b.rfind('verify_candidate_patches') < exec_b.find('PRE-BUILD SAFETY PROOF PASSED')
for s in [
 'GLSLANG_VERSION="16.5.0"',
 'RUNTIME_AUTHORITY_COMMIT="c83ac4d417db537631b6ad15e4918754bd95e9e2"',
 'ROOT_ARTIFACT_NAME="photon-26760-super-res-chroma-denoise"',
 'ROOT_ARTIFACT_SHA="06837a8dd492df37f442cd349a0e6a11afb457db24649f4ded12674565e7841a"',
 'ROOT_TAR_SHA="666d5217ed2741722a20628cda2df7379770ed0ef56e792266956f0e3c6f87bf"',
 'MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"',
 'IRIS_26761_AUTHORITATIVE_ACTIONS_STAGE_ORDER',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace',
 'git show "$RUNTIME_AUTHORITY_COMMIT:build_26760_super_res_chroma_denoise.sh"',
 'git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh"',
]: assert s in b,s
for s in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','bash build_26761_measured_snr_chroma.sh','Verify exact 26761 APK exists before artifact upload','actions/upload-artifact@v4','name: photon-26761-measured-snr-chroma']:
 assert s in w,s
# Only the new namespace can trigger this workflow; prior workflow namespaces cannot overlap.
for s in ["- '26760_*'",'handoff_payload_26760/**','build_26760_super_res_chroma_denoise.sh\'','build-26760-super-res-chroma-denoise.yml\'']:
 assert s not in w,('historical trigger survived',s)
# No APK is ever committed by the workflow; it is build output only.
assert "- '*.apk'" not in w
if len(sys.argv)==7:
 r60b,r60w,r52b,r52w=map(Path,sys.argv[3:7])
 # Exact last-successful 26760 infrastructure identity, from successful c83 runtime-authority commit.
 assert H(r60b)=='e9693bb76d1b64b22b7bf4b04e3322f1ba45c2d5b794b524d17ba12fd7e74de1',H(r60b)
 assert H(r60w)=='edcbb5c011b2a827a93252675741f2f684df9ad24fd6a9dc04099f258f9aa919',H(r60w)
 rb=r60b.read_text(); rw=r60w.read_text(); r52=r52b.read_text(); r52w=r52w.read_text()
 e60=rb[rb.index('# IRIS_26760_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e60,stages)
 assert e60.find('buildCMakeDebug[armeabi-v7a]') < e60.rfind('verify_candidate_patches') < e60.find('PRE-BUILD SAFETY PROOF PASSED')
 prior52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','after_language_compiler_snapshot','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
 e52=r52[r52.index('# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER'):]; ordered(e52,prior52)
 for cmd in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
  assert cmd in b and cmd in rb and cmd in r52,cmd
 for ww in (w,rw,r52w):
  for token in ["java-version: '17'",'actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4']:
   assert token in ww,token
print('PASS 26761 infrastructure: exact successful 26760 build/workflow identity and successful 26752 stage/toolchain/order inherited; delta limited to 26760 authority advance, 5-file measured-SNR chroma scope, one modified runtime GLSL compiler target, regressions, and 26761 namespace')
