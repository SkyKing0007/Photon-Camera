#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26641_r1_infrastructure.py BUILD_SCRIPT WORKFLOW [--git]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
# Exact successful 26639 mechanics authority blobs, inherited unchanged through successful 26640.
assert 'AUTH26639_BUILD_SCRIPT_AUTHORITY_BLOB="a5870d5776c05b6ec134cc1da50da2c835770419"' in b
assert 'AUTH26639_WORKFLOW_AUTHORITY_BLOB="4fc781824f9ecf38291575e4536a361560141bf1"' in b
# Exact successful ordering. Identity/authority/scope/regression applicability may change around it only.
ordered=[
 'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26639_mechanics',
 'install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches',
 '26641 PRE-BUILD SAFETY PROOF PASSED',
 './gradlew :app:assembleDebug --stacktrace',
 'expected exactly one Gradle debug APK',
 'postbuild_proof']
pos=-1
for token in ordered:
 n=b.find(token,pos+1)
 if n<0: raise SystemExit('missing/reordered successful-26639 mechanic: '+token[:100])
 pos=n
for token in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
              'snapshot_candidate_from_authority','compare_app_trees','git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD',
              'POST-BUILD INVARIANCE','CLEAN ARTIFACT SOURCE EXPORT']:
 assert token in b,token
# Authority is successful 26640 compiled candidate; mechanics remain successful 26639.
for token in ['RUNTIME_AUTHORITY_COMMIT="29b5a38277fc2584aa980df8410d5936e2d6bb55"',
              'BASE_RUN_ID="34917470763"','BASE_ARTIFACT_ID="10376279662"',
              'BASE_ARTIFACT_SHA="6b9e8bcaca965af1aba99593508e53870241ae16f306ac1c36be55fbdb1cda4e"',
              'BASE_TAR_SHA="9518f2c3da0dd9136e55dd031e3138fbedd3a5469f077411425ec3d8f3fb8a39"']:
 assert token in b,token
# Workflow retains exact environment and 3-stage shape.
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','GITHUB_TOKEN: ${{ github.token }}']:
 assert token in w,token
assert w.count('- name:')==3
# Only new 26641 trigger namespace; historical workflows are not retriggered by this upload.
assert "'R1_26641_*'" in w and "'R1_26640_*'" not in w and "'R1_26639_*'" not in w
print('PASS 26641 infrastructure audit: successful-26639 compiler/build/patch/PRE-BUILD/assemble/postbuild ordering preserved exactly; successful-26640 compiled candidate is runtime authority')
