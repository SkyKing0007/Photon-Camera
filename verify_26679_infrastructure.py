#!/usr/bin/env python3
from pathlib import Path
import sys
b=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for x in [
'RUNTIME_AUTHORITY_COMMIT="03debb380a9fd2c23e212b7b902469c3c59ad70c"',
'BASE_RUN_ID="35547471196"','BASE_ARTIFACT_ID="10617261167"',
'BASE_ARTIFACT_SHA="24a8f8390617d462a0cf17225fdf5fab2ea23303fcf3e65b4ae13574dc6d4f42"',
'BASE_TAR_SHA="e0e299072d419e564dfd35d66f2cdbcf144199adf07fed14ae9ba8e2d495e551"',
'VERSION_NAME="0.9726679"; VERSION_BUILD="26679"',
'MECHANICS_AUTHORITY_COMMIT="03debb380a9fd2c23e212b7b902469c3c59ad70c"',
'AUTH_26678_BUILD_SCRIPT_BLOB="56bcdc35f055f9074cbc2db8b1183d3c361c0101"',
'AUTH_26678_WORKFLOW_BLOB="83d69dc2059e9c4f9af4f03d9368432dfe87915e"']:
 assert x in b,x
# Exact successful-26678 verification/build order. Identity/authority/scope/semantic names may change only.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26678_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof'];pos=-1
for x in seq:
 n=b.find(x,pos+1);assert n>=0,x;pos=n
# Preserve successful 26678 compiler pins, runner/toolchain and one-APK upload architecture.
for x in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','expected exactly one Gradle debug APK']:
 assert x in b,x
for x in ['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4','ubuntu-24.04',"java-version: '17'",'build_26679_r1_shutter_session_recovery.sh']:
 assert x in w,x
# No historical workflow path trigger overlap: only 26679 paths.
assert "'R1_26679_*'" in w and "'handoff_payload_26679/**'" in w
for old in ['26676_R1','26677_R1','26678_R1']:
 assert old not in w,old
print('PASS 26679 infrastructure: exact successful-26678 compiler/native/patch/PRE-BUILD/assemble/postbuild order retained; only 26679 identity, 26678 authority, five-path scope and regression targets differ')
