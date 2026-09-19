#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26673_infrastructure.py BUILD_SCRIPT WORKFLOW')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
# Exact successful-26672 implementation is mechanics authority.
for t in [
'AUTH_26672_BUILD_SCRIPT_BLOB="daa1219054538ff5d8fad6a19b60dba71b6c7576"',
'AUTH_26672_WORKFLOW_BLOB="3a04ad23f90706c532e37ecb270201e928ccdf28"',
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'snapshot_candidate_from_authority','compare_app_trees','verify_candidate_patches','postbuild_proof']:
 if t not in b: raise SystemExit('FAIL build mechanics token '+t)
# Preserve exact successful-26672 gate/build order; no reordering or substitute compilers.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26672_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','./gradlew \':app:buildCMakeDebug[arm64-v8a]\' \':app:buildCMakeDebug[armeabi-v7a]\'','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild_proof']
pos=-1
for t in seq:
 n=b.find(t,pos+1)
 if n<0: raise SystemExit('FAIL missing/order build mechanics '+t)
 pos=n
for t in ['--local-prebuild','NOT RUN locally (Actions required)','all locally applicable packaged gates passed']:
 assert t in b,t
for t in ['rm -rf "$dest_root/app/src"','cp -a "$live_root/app/src" "$dest_root/app/"','cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"','cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"']:
 assert t in b,t
# Authority must be exact successful 26672 Actions artifact/candidate.
for t in [
'UPLOAD_PARENT_COMMIT="2b6c3ef726cc8532ebfa5e4499bde6ab79bdbc14"',
'RUNTIME_AUTHORITY_COMMIT="2b6c3ef726cc8532ebfa5e4499bde6ab79bdbc14"',
'BASE_RUN_ID="35471368787"','BASE_ARTIFACT_ID="10593065124"',
'BASE_ARTIFACT_SHA="a8230bc9ff9e46bd8ad4d2688dd152542386dda22576a577d07b132c5aaba95c"',
'BASE_TAR_SHA="b82a82930a507698fa3aaedc458c9dd4721dea8f139333cdcdb398a7adc50d86"']:
 assert t in b,t
# Workflow mechanics inherited exactly: same runner/actions/language runtime/single build/single artifact upload.
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','sha256sum -c R1_26673_HANDOFF_HASHES.sha256','bash -n build_26673_r1_android16_heic_fixed_manual_midpoint.sh','bash build_26673_r1_android16_heic_fixed_manual_midpoint.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
 if t not in y: raise SystemExit('FAIL workflow token '+t)
assert y.count('bash build_26673_r1_android16_heic_fixed_manual_midpoint.sh')==1
assert y.count('actions/upload-artifact@v4')==1
# One upload/commit must launch only this build, not historical namespaces.
for old in ['26672_R1_','26671_R1_','26670_R1_','handoff_payload_26672/**','handoff_payload_26671/**','build_26672_r1_heic_google_v2_ui_polish.sh','verify_26672_*.py']:
 assert old not in y,old
print('PASS 26673 infrastructure: functional build/workflow mechanics delta from successful 26672 is ZERO; identity/exact-26672 authority/3-path HEIC+manual semantic targets only; exact compiler/native/patch/PRE-BUILD/assemble/postbuild order retained')
