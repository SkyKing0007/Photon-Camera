#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26674_infrastructure.py BUILD_SCRIPT WORKFLOW')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
# Exact successful-26673 implementation is mechanics authority.
for t in [
'AUTH_26673_BUILD_SCRIPT_BLOB="00eefa97cb44214db08eb0e22f788e199e219f13"',
'AUTH_26673_WORKFLOW_BLOB="8f92919128ff86118b4bd1876cd6a64a75d44704"',
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'snapshot_candidate_from_authority','compare_app_trees','verify_candidate_patches','postbuild_proof']:
 if t not in b: raise SystemExit('FAIL build mechanics token '+t)
# Preserve exact successful-26673 functional order. Native token is checked separately because shell quoting differs harmlessly.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26673_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild_proof']
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
'UPLOAD_PARENT_COMMIT="b72da163436ed8ab6073c16137c48cfca8cbb861"',
'RUNTIME_AUTHORITY_COMMIT="b72da163436ed8ab6073c16137c48cfca8cbb861"',
'BASE_RUN_ID="35475653168"','BASE_ARTIFACT_ID="10593238955"',
'BASE_ARTIFACT_SHA="e55f10030dafa7046e203cebd72fd1ba78b6da045d9f5849cb2a7d59f7c0f743"',
'BASE_TAR_SHA="23cf3fe32e318d084bcd1b3d7bdbcfd7e63ee72009179671a51381ed515f94ea"']:
 assert t in b,t
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','sha256sum -c R1_26674_HANDOFF_HASHES.sha256','bash -n build_26674_r1_protected_normal_manual_geometry.sh','bash build_26674_r1_protected_normal_manual_geometry.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
 if t not in y: raise SystemExit('FAIL workflow token '+t)
assert y.count('bash build_26674_r1_protected_normal_manual_geometry.sh')==1
assert y.count('actions/upload-artifact@v4')==1
for old in ['26673_R1_','26672_R1_','handoff_payload_26673/**','build_26673_r1_android16_heic_fixed_manual_midpoint.sh','verify_26673_*.py']:
 assert old not in y,old
print('PASS 26674 infrastructure: functional build/workflow mechanics delta from successful 26673 is ZERO; identity/exact-26673 authority/11-path semantic targets only; exact compiler/native/patch/PRE-BUILD/assemble/postbuild order retained')
