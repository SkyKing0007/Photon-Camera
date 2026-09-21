#!/usr/bin/env python3
from pathlib import Path
import sys
build=Path(sys.argv[1]).read_text();wf=Path(sys.argv[2]).read_text()
# Exact 26679 compiler/build order retained.
seq2=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26679_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"','verify_candidate_patches','26680 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for x in seq2:
 n=build.find(x,pos+1);assert n>pos,x;pos=n
assert "':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'" in build
for x in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'bash build_26680_r1_stable_preview.sh','actions/upload-artifact@v4'] : assert x in wf,x
for x in ['RUNTIME_AUTHORITY_COMMIT="81dddc56b0d445d917a6bf6393b41afc6fb09a18"','BASE_RUN_ID="35557298961"','BASE_ARTIFACT_ID="10620958112"','BASE_ARTIFACT_SHA="e20bb8ed184a26423da0e87a51fd997484e9683e79cb43f02120bc718ff3237c"','BASE_TAR_SHA="0f769602c0a17f80074c9fc26b949ffba6e96ebb1f92bd0cc2ed83c2e6c2a079"','AUTH_26679_BUILD_SCRIPT_BLOB="a4c5c29507366238062b3c96a4a82a875133b69b"','AUTH_26679_WORKFLOW_BLOB="8776b8c7aea356b1b1088f192bec642b43c4032a"'] : assert x in build,x
print('PASS 26680 infrastructure: successful 26679 R2 compiler/build order retained; only identity/authority/two-file-scope/regression assertions changed')
