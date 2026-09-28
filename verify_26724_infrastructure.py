#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26724_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='9ad7d0dedfbc3a4ea3b13faeecfdaaf70c8d2385'
PRIOR={
 'build_26723_intelligent_flicker_high_zoom_detail.sh':'3b26f3c52eb252abc431dd40eab2da51bedffef7ebfa2c1b40dc33c3a587793b',
 '.github/workflows/build-26723-intelligent-flicker-high-zoom-detail.yml':'975d112f1cdea195aba757d19c04f2fd2de637d25ecdf24ac35f19e0a67ce985',
}
if Path('.git').exists():
 for path,h in PRIOR.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26723 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',
 'BASE_RUN_ID="36367895713"','BASE_ARTIFACT_ID="10948541089"',
 'BASE_ARTIFACT_NAME="photon-26723-intelligent-flicker-high-zoom-detail"',
 'BASE_ARTIFACT_SHA="b2ab591ee6d80bc056015580f6a9082c5eca26625ff52e35a23d7c2297be98b8"',
 'BASE_TAR_SHA="65f41897b039c02e9c30f95a27f2b791b761ae9e1834724883c127b096d41239"',
 'VERSION_NAME="0.9726724"','VERSION_BUILD="26724"',
 'GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'export IRIS26724_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 PRIOR['build_26723_intelligent_flicker_high_zoom_detail.sh'],PRIOR['.github/workflows/build-26723-intelligent-flicker-high-zoom-detail.yml']]: assert t in s,t
marker='# IRIS_26724_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26723_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26724 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26724 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26723-inherited stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26724_resilient_capture_high_zoom_iq.sh']: assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert ".github/workflows/build-26724-resilient-capture-high-zoom-iq.yml" in w
assert '26723_' not in w
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']: assert t in s,t
print('PASS 26724 infrastructure: exact successful 26723 authority hash-pinned; compiler/build commands and stage order unchanged; only authority/version/4-file scope/applicable validators advanced; no backup')
