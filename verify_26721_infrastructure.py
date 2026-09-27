#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26721_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
prior={'build_26720_banding_highzoom_rgb.sh':'90ae95e886ee34eabb923fd2d8b4fe47057e5817b84ee22d149d20d56ae4e7f7','.github/workflows/build-26720-banding-highzoom-rgb.yml':'612f4792cbc1473a34664b4dad8952fe4fc59ce1578460e814908172fea094fb'}
if Path('.git').exists():
 for path,h in prior.items():
  data=subprocess.check_output(['git','show','77bd85387073e254855695366db721ff6e880c9e:'+path]); assert hashlib.sha256(data).hexdigest()==h,('26720 R2 infrastructure authority drift',path)
for t in [
'RUNTIME_AUTHORITY_COMMIT="77bd85387073e254855695366db721ff6e880c9e"',
'BASE_RUN_ID="36350512389"','BASE_ARTIFACT_ID="10942018031"',
'BASE_ARTIFACT_SHA="8e90b5d41e8338afff20978816a3685753c0e46830625fcddadd2c0ad17b4f6b"',
'BASE_TAR_SHA="92c1841ce5fd01c572672551e5c60723a00f9094d1fca6fcdc3174031bbdd8d3"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26721_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'90ae95e886ee34eabb923fd2d8b4fe47057e5817b84ee22d149d20d56ae4e7f7',
'612f4792cbc1473a34664b4dad8952fe4fc59ce1578460e814908172fea094fb']:
 assert t in s,t
m='# IRIS_26721_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(m)==1; main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26720_r2_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26721 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26721 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26721_high_zoom_rgb32f_transport.sh']:
 assert t in w,t
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
print('PASS 26721 infrastructure: exact successful 26720 R2 mechanics authority hash-pinned; compiler/build stage order and commands unchanged; authority/version/scope/applicable gates advanced only; 4-file runtime scope; no backup')
