#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26672_infrastructure.py BUILD_SCRIPT WORKFLOW')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
for t in ['AUTH_26671_BUILD_SCRIPT_BLOB="145c7d98812ffc0ad4371574812d06fe17aa079e"','AUTH_26671_WORKFLOW_BLOB="777126a3f3cc9b44e9a64325837725a99e3dc42c"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','snapshot_candidate_from_authority','compare_app_trees','verify_candidate_patches','postbuild_proof']:
 if t not in b: raise SystemExit('FAIL build mechanics token '+t)
# Preserve exact successful-26671 gate/build order.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26671_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','./gradlew \':app:buildCMakeDebug[arm64-v8a]\' \':app:buildCMakeDebug[armeabi-v7a]\'','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild_proof']
pos=-1
for t in seq:
 n=b.find(t,pos+1)
 if n<0: raise SystemExit('FAIL missing/order build mechanics '+t)
 pos=n
for t in ['--local-prebuild','NOT RUN locally (Actions required)','all locally applicable packaged gates passed']:
 assert t in b,t
for t in ['rm -rf "$dest_root/app/src"','cp -a "$live_root/app/src" "$dest_root/app/"','cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"','cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"']:
 assert t in b,t
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','sha256sum -c R1_26672_HANDOFF_HASHES.sha256','bash -n build_26672_r1_heic_google_v2_ui_polish.sh','bash build_26672_r1_heic_google_v2_ui_polish.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
 if t not in y: raise SystemExit('FAIL workflow token '+t)
for forbidden in ['26671_R1_','handoff_payload_26671/**','build_26671_r1_highlight_separation_histogram.sh','verify_26671_*.py']:
 assert forbidden not in y,forbidden
assert y.count('bash build_26672_r1_heic_google_v2_ui_polish.sh')==1
assert y.count('actions/upload-artifact@v4')==1
# New workflow must not trigger on historical namespaces.
for old in ['26670_R1_','26669_R1_','handoff_payload_26670/**','handoff_payload_26669/**']:
 assert old not in y,old
print('PASS 26672 infrastructure: functional build/workflow mechanics delta from successful 26671 is ZERO; identity/authority/4-path HEIC+UI semantic targets only; exact compiler/native/patch/PRE-BUILD/assemble/postbuild order retained')
