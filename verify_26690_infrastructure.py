#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26690_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2])
MECH='356871e584bb2712ab40c2182a0bb49f6de6f021'
AUTH_BUILD='cbdbd6e9b19316168909f5dd619cb09415859cca'
AUTH_WORKFLOW='e13da2dd63706054812b0c95637c4b53dbdb4ffc'
local_build=os.environ.get('IRIS26690_AUTH_BUILD_FILE')
local_workflow=os.environ.get('IRIS26690_AUTH_WORKFLOW_FILE')
if local_build or local_workflow:
 assert local_build and local_workflow, 'both local mechanics authority files are required'
 assert subprocess.check_output(['git','hash-object',local_build],text=True).strip()==AUTH_BUILD
 assert subprocess.check_output(['git','hash-object',local_workflow],text=True).strip()==AUTH_WORKFLOW
else:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26689_r1_unspektrawesome_hosted_mode.sh'],text=True).strip()==AUTH_BUILD
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26689-r1-unspektrawesome-hosted-mode.yml'],text=True).strip()==AUTH_WORKFLOW
s=build.read_text(); w=workflow.read_text()
# Stable inherited native build contract. This name is owned by CMake from 26681 onward and must
# never be mechanically renamed with the current build identity again.
stable='IRIS26681_SPEKTRA_GLSLANG'
assert s.count(f'export {stable}="$compiler"')==1
assert s.count(f'local compiler="${stable}" outspv=')==1
assert 'IRIS26690_SPEKTRA_GLSLANG' not in s and 'IRIS26689_SPEKTRA_GLSLANG' not in s
for token in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','glslang-16.5.0-linux-x86_64-release.tar.gz']:
 assert token in s, f'pinned glslang authority drift: {token}'
# Exact successful-26689 R1.2 compiler/build order is retained. The only new gate is a post-assemble
# APK JNI contract proof placed after exactly-one-APK selection and before the inherited postbuild proof.
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26689_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof']
pos=-1
for a in anchors:
 n=s.find(a,pos+1); assert n>=0,f'successful-26689 order anchor missing/reordered: {a}'; pos=n
# No compiler/build stage may be skipped or substituted.
for token in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','./gradlew \':app:buildCMakeDebug[arm64-v8a]\' \':app:buildCMakeDebug[armeabi-v7a]\'','./gradlew :app:assembleDebug']:
 assert token in s,token
# Workflow skeleton stays the successful 26689 shape with only 26690 identities.
for token in ['actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4','experimental-clean-photon-rebuild']:
 assert token in w,token
assert w.count('uses: actions/checkout@v5')==1 and w.count('uses: actions/setup-java@v5')==1 and w.count('uses: actions/setup-python@v5')==1 and w.count('uses: actions/upload-artifact@v4')==1
print('PASS 26690 infrastructure audit: successful-26689 R1.2 blobs pinned; compiler/build ordering retained; only post-compiler/APK JNI regressions added')
