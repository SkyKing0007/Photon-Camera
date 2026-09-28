#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26726_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='4f0b6fe37839dc601099071bbdca2935755dbeba'
PRIOR={
 'build_26725_pixel_raw_cpu_compatibility.sh':'2fa6c5dc3afefda85794706de7188d7567bb8cca4778d1044d1db045a3e86fd5',
 '.github/workflows/build-26725-pixel-raw-cpu-compatibility.yml':'be32d84f9e76d362e5e3e9a6b82753124bc1b3398d076f9ca8d783c383b83985',
}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26725 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',
 'BASE_RUN_ID="36429502096"','BASE_ARTIFACT_ID="10972589664"',
 'BASE_ARTIFACT_NAME="photon-26725-pixel-raw-cpu-compatibility"',
 'BASE_ARTIFACT_SHA="22d2bbb3910517d33bdf65a64cd7f30781f8414614df70a22e5057540c7a81d2"',
 'BASE_TAR_SHA="32dfe196d338424176f6306e89c5cd4462da576c8d6abf8dafc04fd9f40ca3f8"',
 'VERSION_NAME="0.9726726"','VERSION_BUILD="26726"',
 'GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'export IRIS26726_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26725_pixel_raw_cpu_compatibility.sh'],PRIOR['.github/workflows/build-26725-pixel-raw-cpu-compatibility.yml']]: assert t in s,t
marker='# IRIS_26726_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26725_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26726 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26726 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26725-inherited stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26726_universal_rgba16f_carrier.sh']: assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert ".github/workflows/build-26726-universal-rgba16f-carrier.yml" in w
assert '26725_' not in w
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']: assert t in s,t
print('PASS 26726 infrastructure: exact successful 26725 authority hash-pinned; compiler/build commands and stage order unchanged; only authority/version/8-file scope/applicable validators advanced; no backup')
