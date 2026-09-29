#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26731_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); sv=Path('verify_26731_shaders.py').read_text(); rv=Path('verify_26731_regressions.py').read_text()
MECH='ac11ce0875343815513ab637a8c23ff7fa85921b'; LAST='978e2d3408e1c5e7e909468afbc7108a673581e6'
MECH_FILES={
'.github/workflows/build-26729-vgn-chroma-containment.yml':'ec717d6847127da9fdfcfbc979697b641bcbc65b0a929d87913bcf61ef1e433f','build_26729_vgn_chroma_containment.sh':'8f7c40421fd55e8b437b47d9675aac1d870e331a2bb28ad2736f24b97f70d874','transform_26729.py':'36df7b17c8fe9cd631aad96acb49e1867decbb0a298359c35e1925e6b24de669','validate_26729.py':'974d2af5ebc17c99d0427aa2a9c33960fe7000de90aebb6d601e2933ed3c5f5d','verify_26729_authority.py':'a5d4133524e8e36c8fcf427ddc2f74915c1225bfcd7f17355bd6b9cffd310691','verify_26729_infrastructure.py':'89c33d15ca6b079f1a5d8092993de861d9326e13d92675577394558694f1339b','verify_26729_patches.py':'794a81f0d74331598f832715cba37bfbbb7922a33736ffb201e5fb5dfad43590','verify_26729_regressions.py':'0559f62dcafed4c7f977b889d25e0fef8641e5c22a177c272d07c4f1bd5657ab','verify_26729_shaders.py':'c26fb0bb61a0e87259c54128a621fb2cfd935cc46ec0bcee928463e41f392b88'}
LAST_FILES={
'.github/workflows/build-26730-validity-owned-chroma-containment.yml':'2e5e454dd61ab63d6375256dc1daa93a6dfd55d3f953bd414658aefcbd895b04','build_26730_validity_owned_chroma_containment.sh':'df8dca699546e5ec9fcf5881a31c156f769ef1e7eb0051d70b6067bf12883dd6','transform_26730.py':'1d9217311965a892ebd23990f6faea3f06e1975615728a6ce064aa5db429c1a6','validate_26730.py':'ad9efd515b88d489c3ae5f7b57bc279b53c5088000bf0e46a554d58f55e48377','verify_26730_authority.py':'05e62c5bc54feec49b3be37f0f06ff7bd24d1facdee3132b0dd0ac246491cd73','verify_26730_infrastructure.py':'ec57f0f3c30428cfc46b570c5ef9fa44bcfa8f9f72dc06ccf0f9e4269bd65dfa','verify_26730_patches.py':'dfef552bfdb2ff255f69b10e3b03bc1ef06f04c0943b1ecadfdfcb6f70c74f3f','verify_26730_regressions.py':'2c41c4284d2a3373a6ca37017f0cae5621676bfd9a8fd3588ad19f4afa76a4ca','verify_26730_shaders.py':'b5fd20753751e4487f0820853e8cf6c12348dfe8e170a47933ac0a99f3cd78e3'}
if Path('.git').exists():
 for commit,files,label in [(MECH,MECH_FILES,'successful 26729 mechanics'),(LAST,LAST_FILES,'successful 26730 implementation')]:
  for path,h in files.items():
   data=subprocess.check_output(['git','show',f'{commit}:{path}']); assert hashlib.sha256(data).hexdigest()==h,(label,path)
for t in [f'RUNTIME_AUTHORITY_COMMIT="{LAST}"',f'MECHANICS_AUTHORITY_COMMIT="{MECH}"','BASE_RUN_ID="36512925620"','BASE_ARTIFACT_ID="11009888420"','BASE_ARTIFACT_NAME="photon-26730-validity-owned-chroma-containment"','BASE_ARTIFACT_SHA="596d56fe1e51864ab9ce36b8664b716cc74f79b0541ab0e3b8bfdc4114d5091b"','BASE_TAR_SHA="3bc699924db8c7db2ba7af66ddab261e338e5037a99e8489bfd73337a2e7c5f6"','VERSION_NAME="0.9726731"','VERSION_BUILD="26731"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26731_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
marker='# IRIS_26731_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26729_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26731 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26731 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26729 stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26731_frozen_material_chroma_transport.sh']:
 assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w and '.github/workflows/build-26731-frozen-material-chroma-transport.yml' in w
# Permanent 26729 R1 and R2 failures must be caught before real compilers advance.
for t in ['IRIS_26731_INHERIT_26729_R1_EXACT_KOTLIN_RUNTIME_SHADER_EXPANSION',"raw=raw.replace('$common',common)","assert '$' not in expanded"]: assert t in sv,t
assert 'textwrap.dedent' not in sv
assert 'setInitial\\(\\s*SCOPE_GLOBAL' in rv
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower() and not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
 assert t in s,t
print('PASS 26731 infrastructure: exact successful 26729 R2 mechanics + successful 26730 inherited implementation hash-pinned; compiler/build commands and stage order unchanged; 26729 R1/R2 failure regressions retained; mechanics delta ZERO; no backup/commit/push')
