#!/usr/bin/env python3
from pathlib import Path
import os,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26692_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2])
MECH='7fcfd4544eaed4b8bff40c64e63db4df1938fea8'; AUTH_BUILD='d90369a024f59bda416d2cbcbf54d3296a47d36c'; AUTH_WORKFLOW='5ff663e24c9b547fae90fcb1604a58985dc3084c'
lb=os.environ.get('IRIS26692_AUTH_BUILD_FILE'); lw=os.environ.get('IRIS26692_AUTH_WORKFLOW_FILE')
if lb or lw:
 assert lb and lw
 assert subprocess.check_output(['git','hash-object',lb],text=True).strip()==AUTH_BUILD
 assert subprocess.check_output(['git','hash-object',lw],text=True).strip()==AUTH_WORKFLOW
else:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26691_r1_spektra_capture_native_histogram.sh'],text=True).strip()==AUTH_BUILD
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26691-r1-spektra-capture-native-histogram.yml'],text=True).strip()==AUTH_WORKFLOW
s=build.read_text(); w=workflow.read_text(); stable='IRIS26681_SPEKTRA_GLSLANG'
assert s.count(f'export {stable}="$compiler"')==1 and s.count(f'local compiler="${stable}" outspv=')==1
for bad in ('IRIS26692_SPEKTRA_GLSLANG','IRIS26691_SPEKTRA_GLSLANG','IRIS26690_SPEKTRA_GLSLANG','IRIS26689_SPEKTRA_GLSLANG'): assert bad not in s
for token in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','glslang-16.5.0-linux-x86_64-release.tar.gz']: assert token in s
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26691_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof']
pos=-1
for a in anchors:
 n=s.find(a,pos+1); assert n>=0,f'26691 order anchor missing/reordered: {a}'; pos=n
for token in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','./gradlew \\:app:buildCMakeDebug[arm64-v8a]']:
 pass
for token in ['actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4','experimental-clean-photon-rebuild']: assert token in w,token
assert w.count('uses: actions/checkout@v5')==1 and w.count('uses: actions/setup-java@v5')==1 and w.count('uses: actions/setup-python@v5')==1 and w.count('uses: actions/upload-artifact@v4')==1
print('PASS 26692 infrastructure audit: successful-26691 blobs pinned; compiler/build ordering retained; identities/scope/regressions only')
