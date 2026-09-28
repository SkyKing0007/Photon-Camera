#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26725_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='1e31f39b27b0572fef6658e4535709d95bb955c0'
PRIOR={
 'build_26724_resilient_capture_high_zoom_iq.sh':'16fa502afd1e540d25d7b6c2e39fe34255b4be4edb570aaab43e1160467e5556',
 '.github/workflows/build-26724-resilient-capture-high-zoom-iq.yml':'8e1d78d63230555bba756c46166c7b485880d71fed3728411512ba500b930855',
}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26724 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',
 'BASE_RUN_ID="36379815046"','BASE_ARTIFACT_ID="10952775232"',
 'BASE_ARTIFACT_NAME="photon-26724-resilient-capture-high-zoom-iq"',
 'BASE_ARTIFACT_SHA="bbb69e8680e75acc5303b1b67c5b657330f3068bb9c1f0adc8359b7b47dc412c"',
 'BASE_TAR_SHA="6bc2e2cae12483e1714f0ad041e4e120933508b447cc20d397b34d81acfab2ae"',
 'VERSION_NAME="0.9726725"','VERSION_BUILD="26725"',
 'GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'export IRIS26725_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26724_resilient_capture_high_zoom_iq.sh'],PRIOR['.github/workflows/build-26724-resilient-capture-high-zoom-iq.yml']]: assert t in s,t
marker='# IRIS_26725_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26724_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26725 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26725 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26724-inherited stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26725_pixel_raw_cpu_compatibility.sh']: assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert ".github/workflows/build-26725-pixel-raw-cpu-compatibility.yml" in w
assert '26724_' not in w
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']: assert t in s,t
print('PASS 26725 infrastructure: exact successful 26724 authority hash-pinned; compiler/build commands and stage order unchanged; only authority/version/2-file scope/applicable validators advanced; no backup')
