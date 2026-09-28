#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26728_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='78843548ca83f8431430c441a6fd19108fd76d75'
PRIOR={
 'build_26727_rgba16f_half_float_upload.sh':'4db26c8be456b90ca2540f8ceb8e07365d431cc1ce2f0d12f78af7e2349546b7',
 '.github/workflows/build-26727-rgba16f-half-float-upload.yml':'f661eb41f969e79105ddb2f38ba04220dc9a537d7dc9512d31b64e650093b88f',
 'verify_26727_shaders.py':'180fa8f0daed736bb5453dd1dbfda93f28aa34e0b6309f818a04be48e0f3b645'}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}']); assert hashlib.sha256(data).hexdigest()==h,('successful 26727 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"','BASE_RUN_ID="36459168943"','BASE_ARTIFACT_ID="10987660159"',
 'BASE_ARTIFACT_NAME="photon-26727-rgba16f-half-float-upload"','BASE_ARTIFACT_SHA="c7d38ac4fadd7ac7c9e930cfc8c06d26c76c6ef3b35f088842dc494bece7d3d1"',
 'BASE_TAR_SHA="470d0b6b74c4e101c34e365cd44765f122868faa0270301d28aeab22dd32bd7f"',
 'VERSION_NAME="0.9726728"','VERSION_BUILD="26728"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26728_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26727_rgba16f_half_float_upload.sh'],PRIOR['.github/workflows/build-26727-rgba16f-half-float-upload.yml'],PRIOR['verify_26727_shaders.py']]: assert t in s,t
marker='# IRIS_26728_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26727_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26728 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26728 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26727-inherited stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26728_physically_supported_chroma.sh']:
 assert t in (s+'\n'+w),t
assert 'branches: [experimental-clean-photon-rebuild]' in w
assert '.github/workflows/build-26728-physically-supported-chroma.yml' in w
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
 assert t in s,t
print('PASS 26728 infrastructure: exact successful 26727 mechanics authority hash-pinned; compiler/build commands and stage order unchanged; only authority/version/scope/applicable validation advanced; no backup/commit/push')
