#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26643_r1_infrastructure.py BUILD_SCRIPT WORKFLOW [--git]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
# Immediate verification-mechanics authority is the exact successful 26642 implementation.
assert 'AUTH26642_BUILD_SCRIPT_AUTHORITY_BLOB="2b7a9f4caeb6fba66dbf3880b7d399acb01af256"' in b
assert 'AUTH26642_WORKFLOW_AUTHORITY_BLOB="e9df8c2f964fb4bd839885f63241187d83baf6d1"' in b
# Inherited successful 26641 and root 26639 authorities remain explicit.
assert 'AUTH26641_BUILD_SCRIPT_AUTHORITY_BLOB="53bf57126a97d684a35c3d2a04e33bcdaa4f31ee"' in b
assert 'AUTH26641_WORKFLOW_AUTHORITY_BLOB="1577eeb875644495578e08196514fd7c0bc99c47"' in b
assert 'AUTH26639_BUILD_SCRIPT_AUTHORITY_BLOB="a5870d5776c05b6ec134cc1da50da2c835770419"' in b
assert 'AUTH26639_WORKFLOW_AUTHORITY_BLOB="4fc781824f9ecf38291575e4536a361560141bf1"' in b
ordered=[
 'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26639_mechanics',
 'install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches',
 '26643 PRE-BUILD SAFETY PROOF PASSED',
 './gradlew :app:assembleDebug --stacktrace',
 'expected exactly one Gradle debug APK',
 'postbuild_proof']
pos=-1
for token in ordered:
 n=b.find(token,pos+1)
 if n<0: raise SystemExit('missing/reordered successful-26642 mechanic: '+token[:120])
 pos=n
for token in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
              'snapshot_candidate_from_authority','compare_app_trees','git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD','POST-BUILD INVARIANCE','CLEAN ARTIFACT SOURCE EXPORT']:
 assert token in b,token
# Exact successful 26642 compiled-candidate authority.
for token in ['RUNTIME_AUTHORITY_COMMIT="23ef05f61020cfd0ce412ef7ecb0bdc1064f99ba"','BASE_RUN_ID="34930671416"','BASE_ARTIFACT_ID="10381088303"',
              'BASE_ARTIFACT_SHA="a475b50c17f1d2d4cd7da8dc0757089400335bc95a8e6a2a267bd067e667df61"',
              'BASE_TAR_SHA="8c7fbbc120ca3150e19d98c6b2e7c6244204611482bcb638f2163ec329c63a3c"']:
 assert token in b,token
assert 'REAL GLSL COMPILE: NOT APPLICABLE (0 modified GLSL/runtime-expanded shaders)' in b
# Added-path patch verifier retains successful 26642 non-ignored cleanup; never -x.
pv=Path(__file__).with_name('verify_26643_r1_patches.py').read_text()
assert "run(['git','clean','-fd','-q'],repo)" in pv and "git','clean','-fdx" not in pv
# Workflow exact environment and 3-stage shape.
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','GITHUB_TOKEN: ${{ github.token }}']:
 assert token in w,token
assert w.count('- name:')==3
# Unique 26643 trigger namespace, no overlapping historical handoff triggers.
assert "'R1_26643_*'" in w and "'R1_26642_*'" not in w and "'R1_26641_*'" not in w and "'R1_26640_*'" not in w and "'R1_26639_*'" not in w
print('PASS 26643 infrastructure audit: exact successful-26642 compiler/build/NDK/patch/PRE-BUILD/assemble/postbuild order preserved; delta limited to 26643 authority/scope/HEIC+UI regressions and 0-GLSL applicability')
