#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26670_infrastructure.py BUILD_SCRIPT WORKFLOW')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
# Exact successful-26669 verification-mechanics authority blobs must be named.
for t in ['AUTH_26669_BUILD_SCRIPT_BLOB="dd89e377831df6611fe0833343fd58b2fff2e914"','AUTH_26669_WORKFLOW_BLOB="ecc6f934370d1a354b063a03adbec7f0c2ab7d1e"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','snapshot_candidate_from_authority','compare_app_trees','verify_candidate_patches','postbuild_proof']:
 if t not in b: raise SystemExit('FAIL build mechanics token '+t)
# Preserve exact successful-26669 gate/build order.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26669_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','./gradlew \':app:buildCMakeDebug[arm64-v8a]\' \':app:buildCMakeDebug[armeabi-v7a]\'','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild_proof']
pos=-1
for t in seq:
 n=b.find(t,pos+1)
 if n<0: raise SystemExit('FAIL missing/order build mechanics '+t)
 pos=n
# Local prebuild must stop before real language/native/assemble, exactly as 26669.
for t in ['--local-prebuild','NOT RUN locally (Actions required)','all locally applicable packaged gates passed']:
 assert t in b,t
# Authority-seeded canonical overlay excludes generated/repository-only app universe.
for t in ['rm -rf "$dest_root/app/src"','cp -a "$live_root/app/src" "$dest_root/app/"','cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"','cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"']:
 assert t in b,t
# Workflow shell/action mechanics unchanged from 26669.
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','sha256sum -c R1_26670_HANDOFF_HASHES.sha256','bash -n build_26670_r1_restore_26660_live_hdr_manual.sh','bash build_26670_r1_restore_26660_live_hdr_manual.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
 if t not in y: raise SystemExit('FAIL workflow token '+t)
# One intended new trigger namespace only; no overlapping 26669 trigger paths.
for forbidden in ['26669_R1_','handoff_payload_26669/**','build_26669_r1_capture_ui_preview_correction.sh','verify_26669_*.py']:
 assert forbidden not in y,forbidden
assert y.count('bash build_26670_r1_restore_26660_live_hdr_manual.sh')==1
assert y.count('actions/upload-artifact@v4')==1
print('PASS 26670 infrastructure: functional build/workflow mechanics delta from successful 26669 is ZERO; identity/authority/16-path scope/semantic+shader targets only; exact compiler/native/patch/PRE-BUILD/assemble/postbuild order retained')
