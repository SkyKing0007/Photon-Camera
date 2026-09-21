#!/usr/bin/env python3
from pathlib import Path
import re,sys
build=Path(sys.argv[1]).read_text(); wf=Path(sys.argv[2]).read_text()
# Exact successful 26680 compiler/build stage order retained. Spektra-specific work is confined
# inside make_candidate/verify_shaders/native source; no real compiler/build stage may move.
seq=[
'verify_package',
'verify_scope',
'obtain_authority',
'make_candidate',
'verify_shaders',
'verify_successful_26680_mechanics',
'install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",
'verify_candidate_patches',
'26681 PRE-BUILD SAFETY PROOF PASSED',
'./gradlew :app:assembleDebug',
'postbuild_proof']
pos=-1
for x in seq:
 n=build.find(x,pos+1); assert n>pos,x; pos=n
# No alternate/reordered Gradle compiler/build path may be introduced.
gradle=[x.strip() for x in build.splitlines() if x.strip().startswith('./gradlew ')]
assert gradle==[
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26681_gradle_language_compilers.log"',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee \"$OUT/26681_gradle_native_compiler.log\"",
'./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26681_gradle_assemble.log"']
# Successful 26680 Actions/toolchain layout preserved.
for x in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'bash build_26681_r1_spektra.sh','actions/upload-artifact@v4','runs-on: ubuntu-24.04']:
 assert x in wf,x
# Split-upload provenance repair: exact successful 26680 remains ancestry authority while
# cumulative upload scope from that authority to HEAD must remain exact. This changes no build stage.
assert 'git merge-base --is-ancestor "$UPLOAD_PARENT_COMMIT" HEAD' in build
assert 'git diff --name-only "$UPLOAD_PARENT_COMMIT"..HEAD' in build
assert 'git rev-parse HEAD^' not in build
# Runtime authority and mechanics authority are exact successful 26680 R1.
for x in [
'RUNTIME_AUTHORITY_COMMIT="e4a4cc41d56d3773872aae33ba69e87aea86d0ae"',
'BASE_RUN_ID="35561207312"',
'BASE_ARTIFACT_ID="10622625438"',
'BASE_ARTIFACT_SHA="409646871929e77f5eb1bf8315725bbec9b64ba1726555ce06435aecad12c00b"',
'BASE_TAR_SHA="417db348013f2aeb5c3130cbf8b4899c09f587ff46a2fec65b5545b15f3f102c"',
'AUTH_26680_BUILD_SCRIPT_BLOB="84681526e61396e0e40481661f6a3b95f4c0b8e3"',
'AUTH_26680_WORKFLOW_BLOB="2e2fbb92e73b4759553dfef52e69d3119e4854ef"',
'GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert x in build,x
# Spektra shader extension stays inside the pre-language GLSL stage and feeds the same compiler to CMake.
assert build.find('materialize_upstream_spektra_shaders') < build.find('install_frozen_candidate_live')
assert 'export IRIS26681_SPEKTRA_GLSLANG="$compiler"' in build
assert build.find('export IRIS26681_SPEKTRA_GLSLANG="$compiler"') < build.find("./gradlew ':app:buildCMakeDebug[arm64-v8a]'")
# Patch mechanics are still full-index + exact 7/12/40 + apply --check; only staged-index form differs
# because 26681 has legitimate additions that 26680 did not.
pv=Path(Path(sys.argv[1]).parent/'verify_26681_patches.py').read_text()
for x in ["('7','12','40')", "'--binary','--full-index','--no-ext-diff'", "'git','apply','--check'", "'git','add','-A','app'"]:
 assert x in pv,x
print('PASS 26681 infrastructure: successful 26680 R1 compiler/build order retained; exact-26680 ancestry + exact cumulative upload scope; extensions limited to Spektra shader/source verification and additions-aware canonical patch representation')
