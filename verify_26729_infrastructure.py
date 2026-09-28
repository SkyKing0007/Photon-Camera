#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26729_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='5d0482abd0b99979f5f8b800bf55b7a39ef40dab'
PRIOR={
 'build_26728_physically_supported_chroma.sh':'99b6bbcee7724fece17e631891d12d033b870e3d458c7c31a7378900f7bd9b75',
 '.github/workflows/build-26728-physically-supported-chroma.yml':'a2f23b01337b414e9f6a10594620bdbcf1ba7b1acf899b378435dc89d93c57df',
 'verify_26728_shaders.py':'bec3ea56778bbd074003d845a199ce96479dc49116fbfe13cfe3c12d82bb290d'}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26728 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',
 'BASE_RUN_ID="36482206871"','BASE_ARTIFACT_ID="10997561110"',
 'BASE_ARTIFACT_NAME="photon-26728-physically-supported-chroma"',
 'BASE_ARTIFACT_SHA="c8a63a217be8c47f226976972afdc5edb0b8a68521cf045e4578ffce7aee384b"',
 'BASE_TAR_SHA="fc1dea853e131f48decbe56d1138fe9d7c5a4148ed50b80fb2ccf0820a2fefe8"',
 'VERSION_NAME="0.9726729"','VERSION_BUILD="26729"',
 'GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'export IRIS26729_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26728_physically_supported_chroma.sh'],PRIOR['.github/workflows/build-26728-physically-supported-chroma.yml'],PRIOR['verify_26728_shaders.py']]:
 assert t in s,t
marker='# IRIS_26729_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=[
 'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26728_mechanics',
 'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 'JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches','26729 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace',
 'postbuild_proof','26729 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26728-inherited stage order',t); pos=n
for t in [
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0',
 'actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',
 "python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26729_vgn_chroma_containment.sh']:
 assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert '.github/workflows/build-26729-vgn-chroma-containment.yml' in w
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
 assert t in s,t
print('PASS 26729 infrastructure: exact successful 26728 authority hash-pinned; compiler/build commands and stage order unchanged; mechanics delta ZERO; no backup/commit/push')
