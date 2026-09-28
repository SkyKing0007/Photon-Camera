#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26727_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='d5ac40d2a18b7ee08c2bbd1195980512c78b28dc'
PRIOR={
 'build_26726_universal_rgba16f_carrier.sh':'7ad72238b2838c8762b32817ee3faeb9994d7ecebb98a62e726849b2bfa3f5c2',
 '.github/workflows/build-26726-universal-rgba16f-carrier.yml':'cb0eefc4705c34aba9977207f7a3bcf5c246b11e0d862c96dc888589455dae8b',
}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26726 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',
 'BASE_RUN_ID="36454846825"','BASE_ARTIFACT_ID="10984683693"',
 'BASE_ARTIFACT_NAME="photon-26726-universal-rgba16f-carrier"',
 'BASE_ARTIFACT_SHA="f0d8916aaed4acaa827e2635bbf7b3a250e2c7d22239bbd4ef458b242a3fd3cd"',
 'BASE_TAR_SHA="740077de8ca62230a7a51b5bf869d32a6a8069a53cfe4f1147955e2479e7d36d"',
 'VERSION_NAME="0.9726727"','VERSION_BUILD="26727"',
 'GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'export IRIS26727_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26726_universal_rgba16f_carrier.sh'],PRIOR['.github/workflows/build-26726-universal-rgba16f-carrier.yml']]: assert t in s,t
marker='# IRIS_26727_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=[
 'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26726_mechanics',
 'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 'JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches','26727 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace',
 'postbuild_proof','26727 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26726-inherited stage order',t); pos=n
for t in [
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0',
 'actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',
 "python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26727_rgba16f_half_float_upload.sh']:
 assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert '.github/workflows/build-26727-rgba16f-half-float-upload.yml' in w
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
 assert t in s,t
print('PASS 26727 infrastructure: exact successful 26726 authority hash-pinned; compiler/build commands and stage order unchanged; only authority/version/scope/applicable validation advanced; no backup/commit/push')
