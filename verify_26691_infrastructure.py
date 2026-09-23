#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26691_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2])
MECH='a0aab18288222675dddb0fa0c53be46101cf539f'
AUTH_BUILD='f7b1c768d1a92205f9379a3b6b45a629a217bbec'
AUTH_WORKFLOW='5fe2551f3467ba2cf279efdb1bba17559ef58acc'
local_build=os.environ.get('IRIS26691_AUTH_BUILD_FILE')
local_workflow=os.environ.get('IRIS26691_AUTH_WORKFLOW_FILE')
if local_build or local_workflow:
 assert local_build and local_workflow, 'both local mechanics authority files are required'
 assert subprocess.check_output(['git','hash-object',local_build],text=True).strip()==AUTH_BUILD
 assert subprocess.check_output(['git','hash-object',local_workflow],text=True).strip()==AUTH_WORKFLOW
else:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26690_r1_unspektrawesome_jni_startup_containment.sh'],text=True).strip()==AUTH_BUILD
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26690-r1-unspektrawesome-jni-startup-containment.yml'],text=True).strip()==AUTH_WORKFLOW
s=build.read_text(); w=workflow.read_text()
# Stable native compiler bridge inherited unchanged from successful 26690.
stable='IRIS26681_SPEKTRA_GLSLANG'
assert s.count(f'export {stable}="$compiler"')==1
assert s.count(f'local compiler="${stable}" outspv=')==1
for bad in ('IRIS26691_SPEKTRA_GLSLANG','IRIS26690_SPEKTRA_GLSLANG','IRIS26689_SPEKTRA_GLSLANG'):
 assert bad not in s, f'stable glslang contract renamed: {bad}'
for token in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','glslang-16.5.0-linux-x86_64-release.tar.gz']:
 assert token in s, f'pinned glslang authority drift: {token}'
# Exact successful-26690 compiler/build order retained. No new compiler/build stage is inserted.
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26690_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof']
pos=-1
for a in anchors:
 n=s.find(a,pos+1); assert n>=0,f'successful-26690 order anchor missing/reordered: {a}'; pos=n
for token in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','./gradlew \':app:buildCMakeDebug[arm64-v8a]\' \':app:buildCMakeDebug[armeabi-v7a]\'','./gradlew :app:assembleDebug']:
 assert token in s,token
# Successful 26690 workflow skeleton is retained with only 26691 identities/paths.
for token in ['actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4','experimental-clean-photon-rebuild']:
 assert token in w,token
assert w.count('uses: actions/checkout@v5')==1 and w.count('uses: actions/setup-java@v5')==1 and w.count('uses: actions/setup-python@v5')==1 and w.count('uses: actions/upload-artifact@v4')==1
print('PASS 26691 infrastructure audit: successful-26690 blobs pinned; exact compiler/build ordering retained; identities/scope/regressions only')
