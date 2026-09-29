#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26730_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); sv=Path('verify_26730_shaders.py').read_text(); rv=Path('verify_26730_regressions.py').read_text()
AUTH='ac11ce0875343815513ab637a8c23ff7fa85921b'
PRIOR={
 '.github/workflows/build-26729-vgn-chroma-containment.yml':'ec717d6847127da9fdfcfbc979697b641bcbc65b0a929d87913bcf61ef1e433f',
 'build_26729_vgn_chroma_containment.sh':'8f7c40421fd55e8b437b47d9675aac1d870e331a2bb28ad2736f24b97f70d874',
 'transform_26729.py':'36df7b17c8fe9cd631aad96acb49e1867decbb0a298359c35e1925e6b24de669',
 'validate_26729.py':'974d2af5ebc17c99d0427aa2a9c33960fe7000de90aebb6d601e2933ed3c5f5d',
 'verify_26729_authority.py':'a5d4133524e8e36c8fcf427ddc2f74915c1225bfcd7f17355bd6b9cffd310691',
 'verify_26729_infrastructure.py':'89c33d15ca6b079f1a5d8092993de861d9326e13d92675577394558694f1339b',
 'verify_26729_patches.py':'794a81f0d74331598f832715cba37bfbbb7922a33736ffb201e5fb5dfad43590',
 'verify_26729_regressions.py':'0559f62dcafed4c7f977b889d25e0fef8641e5c22a177c272d07c4f1bd5657ab',
 'verify_26729_shaders.py':'c26fb0bb61a0e87259c54128a621fb2cfd935cc46ec0bcee928463e41f392b88'}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26729 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"','BASE_RUN_ID="36506106479"','BASE_ARTIFACT_ID="11007950351"',
 'BASE_ARTIFACT_NAME="photon-26729-vgn-chroma-containment"',
 'BASE_ARTIFACT_SHA="5676791aa0c2f29c797f72ebec0c49735bc0fed4ca4a191bb1dcd1e74ae7fe2e"',
 'BASE_TAR_SHA="5d7920a592cf2db517316eaf63e40fba553b429a9d9ab92c83df180acebd88ca"',
 'VERSION_NAME="0.9726730"','VERSION_BUILD="26730"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26730_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26729_vgn_chroma_containment.sh'],PRIOR['.github/workflows/build-26729-vgn-chroma-containment.yml'],PRIOR['verify_26729_shaders.py']]:
 assert t in s,t
marker='# IRIS_26730_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26729_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26730 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26730 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26729-inherited stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26730_validity_owned_chroma_containment.sh']:
 assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert '.github/workflows/build-26730-validity-owned-chroma-containment.yml' in w
# 26729 R1 permanent regression: exact Kotlin runtime interpolation before all shader proof/compile.
for t in ['IRIS_26730_INHERIT_R1_EXACT_KOTLIN_RUNTIME_SHADER_EXPANSION',"raw=raw.replace('$common',common)","assert '$' not in expanded",'bs=runtime_shader(base,relp,name); cs=runtime_shader(cand,relp,name)']:
 assert t in sv,t
assert 'textwrap.dedent' not in sv
# 26729 R2 permanent regression: raw String keys cannot use boolean setInitial overload.
for t in ['pref_iris_residual_chroma_custom", "0"','setInitial\\(\\s*SCOPE_GLOBAL']:
 assert t in rv,t
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
 assert t in s,t
print('PASS 26730 infrastructure: exact successful 26729 R2 infrastructure hash-pinned; compiler/build commands and stage order unchanged; 26729 R1/R2 build-failure regressions enforced; mechanics delta ZERO; no backup/commit/push')
