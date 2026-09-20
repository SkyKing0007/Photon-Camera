#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26676_infrastructure.py BUILD_SCRIPT WORKFLOW')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
for t in ['AUTH_26675_BUILD_SCRIPT_BLOB="5c06b41d5535f581e12f8d05418f9e2bdfe5f9d1"','AUTH_26675_WORKFLOW_BLOB="184932506e9dcab058c9f2471d3cc99b885f59ef"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','snapshot_candidate_from_authority','compare_app_trees','verify_candidate_patches','postbuild_proof']:
 if t not in b: raise SystemExit('FAIL build mechanics token '+t)
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26675_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild_proof']
pos=-1
for t in seq:
 n=b.find(t,pos+1)
 if n<0: raise SystemExit('FAIL missing/order build mechanics '+t)
 pos=n
for t in ["':app:buildCMakeDebug[arm64-v8a]'", "':app:buildCMakeDebug[armeabi-v7a]'",'--local-prebuild','NOT RUN locally (Actions required)','all locally applicable packaged gates passed']:
 assert t in b,t
for t in ['rm -rf "$dest_root/app/src"','cp -a "$live_root/app/src" "$dest_root/app/"','cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"','cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"']:
 assert t in b,t
for t in ['UPLOAD_PARENT_COMMIT="2992abb5ec9ec577e7bd088811319bf402c783bb"','RUNTIME_AUTHORITY_COMMIT="2992abb5ec9ec577e7bd088811319bf402c783bb"','BASE_RUN_ID="35517341418"','BASE_ARTIFACT_ID="10607511056"','BASE_ARTIFACT_NAME="photon-26675-r1-preview-decoupled-short-manual-icons"','BASE_ARTIFACT_SHA="198913d1452ee1e16daa8bc95e2bc99eb18bfeada8a9b09499f0cce1561043e5"','BASE_TAR_SHA="0498ba74ce53811e7b48ff4437552e3724507c20c419a3cea4bb2f57a7bb9ff7"']:
 assert t in b,t
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','sha256sum -c R1_26676_HANDOFF_HASHES.sha256','bash -n build_26676_r1_fast_hdr_wysiwyg_iris_watermark.sh','bash build_26676_r1_fast_hdr_wysiwyg_iris_watermark.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
 if t not in y: raise SystemExit('FAIL workflow token '+t)
assert y.count('bash build_26676_r1_fast_hdr_wysiwyg_iris_watermark.sh')==1 and y.count('actions/upload-artifact@v4')==1
for old in ['handoff_payload_26675/**','build_26675_r1_preview_decoupled_short_manual_icons.sh','verify_26675_*.py']:
 assert old not in y,old
print('PASS 26676 infrastructure: functional build/workflow mechanics delta from successful 26675 is ZERO; exact compiler/native/patch/PRE-BUILD/assemble/postbuild order retained')
