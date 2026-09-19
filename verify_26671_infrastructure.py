#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26671_infrastructure.py BUILD_SCRIPT WORKFLOW')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
# Exact successful-26670 verification-mechanics authority blobs must be named.
for t in ['AUTH_26670_BUILD_SCRIPT_BLOB="de02a1b566583aa3909580db4b349d125dd40e5b"','AUTH_26670_WORKFLOW_BLOB="bdc6d64d8591197c835596c54b623873a891dca3"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','snapshot_candidate_from_authority','compare_app_trees','verify_candidate_patches','postbuild_proof']:
 if t not in b: raise SystemExit('FAIL build mechanics token '+t)
# Preserve exact successful-26670 gate/build order.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26670_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','./gradlew \':app:buildCMakeDebug[arm64-v8a]\' \':app:buildCMakeDebug[armeabi-v7a]\'','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild_proof']
pos=-1
for t in seq:
 n=b.find(t,pos+1)
 if n<0: raise SystemExit('FAIL missing/order build mechanics '+t)
 pos=n
for t in ['--local-prebuild','NOT RUN locally (Actions required)','all locally applicable packaged gates passed']:
 assert t in b,t
for t in ['rm -rf "$dest_root/app/src"','cp -a "$live_root/app/src" "$dest_root/app/"','cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"','cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"']:
 assert t in b,t
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','sha256sum -c R1_26671_HANDOFF_HASHES.sha256','bash -n build_26671_r1_highlight_separation_histogram.sh','bash build_26671_r1_highlight_separation_histogram.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
 if t not in y: raise SystemExit('FAIL workflow token '+t)
for forbidden in ['26670_R1_','handoff_payload_26670/**','build_26670_r1_restore_26660_live_hdr_manual.sh','verify_26670_*.py']:
 assert forbidden not in y,forbidden
assert y.count('bash build_26671_r1_highlight_separation_histogram.sh')==1
assert y.count('actions/upload-artifact@v4')==1
print('PASS 26671 infrastructure: functional build/workflow mechanics delta from successful 26670 is ZERO; identity/authority/5-path scope/semantic+shader targets only; exact compiler/native/patch/PRE-BUILD/assemble/postbuild order retained')
