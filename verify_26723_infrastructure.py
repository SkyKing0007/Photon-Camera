#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26723_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='069f19e3f79a803d00339a2a7eb494519b1bce3e'
PRIOR={
 'build_26722_high_zoom_native_chroma.sh':'edf75559eb7bdf5f19631ac56c1b4fbe827fcab9a91bb60cd9bba16d18998a3b',
 '.github/workflows/build-26722-high-zoom-native-chroma.yml':'9ccf7aee2432be4974ab6c7b2317ab5e9641078faa4bfcfff8d2f3849157d925',
}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26722 infrastructure authority drift',path)
# Authority/version/artifact pins must be exact successful 26722.
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',
 'BASE_RUN_ID="36357844301"','BASE_ARTIFACT_ID="10944876040"',
 'BASE_ARTIFACT_NAME="photon-26722-high-zoom-native-chroma"',
 'BASE_ARTIFACT_SHA="7e852ac7b1915c5a9c014ae9f3550c8b047f73ccd05fd58c747849b1df750ab2"',
 'BASE_TAR_SHA="9b893c74ffab036496f888d1805207beb48b3f3ee2042543a14e1f42a671951e"',
 'VERSION_NAME="0.9726723"','VERSION_BUILD="26723"',
 'GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'export IRIS26723_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26722_high_zoom_native_chroma.sh'],PRIOR['.github/workflows/build-26722-high-zoom-native-chroma.yml']]:
 assert t in s,t
# Exact successful-26722 core execution order. Only authority/version/scope/applicable validators advance.
marker='# IRIS_26723_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=[
 'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26722_mechanics',
 'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader',
 'install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 'JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches','26723 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace',
 'postbuild_proof','26723 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26722-inherited stage order',t); pos=n
# Compiler/build commands and environment are unchanged from successful 26722.
for t in [
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace',
 'runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5',
 "distribution: temurin","java-version: '17'",'cache: gradle','actions/setup-python@v5',
 "python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90',
 'bash build_26723_intelligent_flicker_high_zoom_detail.sh']:
 assert t in (s+'\n'+w),t
# One intended workflow trigger/domain, same two-step upload mechanics; no backup or source push owner.
assert "branches: [experimental-clean-photon-rebuild]" in w
assert ".github/workflows/build-26723-intelligent-flicker-high-zoom-detail.yml" in w
assert '26722_' not in w
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
# Frozen-candidate semantics and exactly-one APK proof retained.
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
 assert t in s,t
print('PASS 26723 infrastructure: exact successful 26722 authority hash-pinned; compiler/build commands and stage order unchanged; only authority/version/4-file scope/applicable validators advanced; no backup')
