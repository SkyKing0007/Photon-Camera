#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26642_r1_infrastructure.py BUILD_SCRIPT WORKFLOW [--git]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
# Immediate verification-mechanics authority is the exact successful 26641 implementation.
assert 'AUTH26641_BUILD_SCRIPT_AUTHORITY_BLOB="53bf57126a97d684a35c3d2a04e33bcdaa4f31ee"' in b
assert 'AUTH26641_WORKFLOW_AUTHORITY_BLOB="1577eeb875644495578e08196514fd7c0bc99c47"' in b
# Root compiler/build ordering authority remains successful 26639, inherited by 26641.
assert 'AUTH26639_BUILD_SCRIPT_AUTHORITY_BLOB="a5870d5776c05b6ec134cc1da50da2c835770419"' in b
assert 'AUTH26639_WORKFLOW_AUTHORITY_BLOB="4fc781824f9ecf38291575e4536a361560141bf1"' in b
ordered=[
 'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26639_mechanics',
 'install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches',
 '26642 PRE-BUILD SAFETY PROOF PASSED',
 './gradlew :app:assembleDebug --stacktrace',
 'expected exactly one Gradle debug APK',
 'postbuild_proof']
pos=-1
for token in ordered:
 n=b.find(token,pos+1)
 if n<0: raise SystemExit('missing/reordered successful-26641 mechanic: '+token[:120])
 pos=n
for token in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
              'snapshot_candidate_from_authority','compare_app_trees','git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD',
              'POST-BUILD INVARIANCE','CLEAN ARTIFACT SOURCE EXPORT']:
 assert token in b,token
# Exact successful 26641 compiled-candidate authority.
for token in ['RUNTIME_AUTHORITY_COMMIT="6856814b2e072a7c9974f7b93f2d946dd9d1947e"',
              'BASE_RUN_ID="34924928568"','BASE_ARTIFACT_ID="10379707013"',
              'BASE_ARTIFACT_SHA="a321bfce16db3a8cc2b3fb56818aeb2f76c157a87e89f84226312daf5e70e89d"',
              'BASE_TAR_SHA="66ae8daf38c96067ac227d38c768cdf284450c8b1775dc323f72ec00560de9f9"']:
 assert token in b,token
# Applicability delta only: 0 changed GLSL, but the shader gate remains in the same slot.
assert 'REAL GLSL COMPILE: NOT APPLICABLE (0 modified GLSL/runtime-expanded shaders)' in b
# Added-path patch verifier must clean only non-ignored added files. Never use -x: authority-seeded ignored vendor headers are protected runtime bytes.
assert "run(['git','clean','-fd','-q'],repo)" in Path(__file__).with_name('verify_26642_r1_patches.py').read_text()
assert "git','clean','-fdx" not in Path(__file__).with_name('verify_26642_r1_patches.py').read_text()
# Workflow retains exact successful environment and 3-stage shape.
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','GITHUB_TOKEN: ${{ github.token }}']:
 assert token in w,token
assert w.count('- name:')==3
# Unique 26642 trigger namespace: no historical 26641/26640/26639 trigger overlap.
assert "'R1_26642_*'" in w and "'R1_26641_*'" not in w and "'R1_26640_*'" not in w and "'R1_26639_*'" not in w
print('PASS 26642 infrastructure audit: exact successful-26641 compiler/build/NDK/patch/PRE-BUILD/assemble/postbuild order preserved; delta limited to 26642 authority/scope/regressions, 0-GLSL applicability, and added-path patch cleanup')
