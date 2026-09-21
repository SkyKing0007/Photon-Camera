#!/usr/bin/env python3
from pathlib import Path
import sys
b=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for x in ['RUNTIME_AUTHORITY_COMMIT="36c494046250838e04a45aa777c5028e957da77b"','BASE_RUN_ID="35535056891"','BASE_ARTIFACT_ID="10613355008"','BASE_ARTIFACT_SHA="23f5ebf48af9d57549256548986aa5512c7f37fc6f7871254d710a3b2d051b0c"','BASE_TAR_SHA="dbf087c8a9bae035cf0d6fa3246f1be6e69700925ab30a2745cefb638d879b1b"','VERSION_NAME="0.9726678"; VERSION_BUILD="26678"','MECHANICS_AUTHORITY_COMMIT="101fb9ac90549d6053e15b2b9e97ba5835a14849"','AUTH_26676_BUILD_SCRIPT_BLOB="c33df84f61d3c29e0e7b316ed0f9a827f903ab7d"','AUTH_26676_WORKFLOW_BLOB="a889494ac4c1e06ebaf2bb950f2eca5c5a927ff8"']:assert x in b,x
# Exact successful-26676 verification/build ordering, names aside.
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26676_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof'];pos=-1
for x in seq:
 n=b.find(x,pos+1);assert n>=0,x;pos=n
for x in ['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4','ubuntu-24.04',"java-version: '17'",'build_26678_r1_flicker_adaptive_watermark.sh']:assert x in w,x
print('PASS 26678 infrastructure: exact successful-26676 compiler/native/patch/PRE-BUILD/assemble/postbuild order retained; identity/authority/scope only')
