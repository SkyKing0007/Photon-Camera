#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26675_infrastructure.py BUILD_SCRIPT WORKFLOW')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
for t in [
'AUTH_26674_BUILD_SCRIPT_BLOB="18bfa3508552b641faf873727b264f891307bd78"',
'AUTH_26674_WORKFLOW_BLOB="40907c1831bbde676c38325f25587cf1911d33a8"',
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'snapshot_candidate_from_authority','compare_app_trees','verify_candidate_patches','postbuild_proof']:
 if t not in b: raise SystemExit('FAIL build mechanics token '+t)
# Exact successful-26674 functional order retained.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26674_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild_proof']
pos=-1
for t in seq:
 n=b.find(t,pos+1)
 if n<0: raise SystemExit('FAIL missing/order build mechanics '+t)
 pos=n
for t in ["':app:buildCMakeDebug[arm64-v8a]'", "':app:buildCMakeDebug[armeabi-v7a]'",'--local-prebuild','NOT RUN locally (Actions required)','all locally applicable packaged gates passed']:
 assert t in b,t
for t in ['rm -rf "$dest_root/app/src"','cp -a "$live_root/app/src" "$dest_root/app/"','cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"','cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"']:
 assert t in b,t
for t in [
'UPLOAD_PARENT_COMMIT="c73b5e95be2b1d762f044d79318603afa1d8b0d3"','RUNTIME_AUTHORITY_COMMIT="c73b5e95be2b1d762f044d79318603afa1d8b0d3"',
'BASE_RUN_ID="35492860182"','BASE_ARTIFACT_ID="10600250297"','BASE_ARTIFACT_NAME="photon-26674-r1-protected-normal-manual-geometry"',
'BASE_ARTIFACT_SHA="c370ebc345468e9238546b8df765a9d00a20f823e2cba3b6a3dd75bae07fd41f"','BASE_TAR_SHA="106354ca57e85acba47851be060f7cabf48a402d604876ffb2fbf49df6639a61"']:
 assert t in b,t
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','sha256sum -c R1_26675_HANDOFF_HASHES.sha256','bash -n build_26675_r1_preview_decoupled_short_manual_icons.sh','bash build_26675_r1_preview_decoupled_short_manual_icons.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
 if t not in y: raise SystemExit('FAIL workflow token '+t)
assert y.count('bash build_26675_r1_preview_decoupled_short_manual_icons.sh')==1
assert y.count('actions/upload-artifact@v4')==1
for old in ['26674_R1_','handoff_payload_26674/**','build_26674_r1_protected_normal_manual_geometry.sh','verify_26674_*.py']:
 assert old not in y,old
print('PASS 26675 infrastructure: functional build/workflow mechanics delta from successful 26674 is ZERO; identity/exact-26674 authority/8-path semantic targets only; exact compiler/native/patch/PRE-BUILD/assemble/postbuild order retained')
