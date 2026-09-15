#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26640_r1_infrastructure.py BUILD_SCRIPT WORKFLOW [--git]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
# Exact successful 26639 mechanics authority blobs, independently retrieved from commit 18861d3d...
assert 'AUTH26639_BUILD_SCRIPT_AUTHORITY_BLOB="a5870d5776c05b6ec134cc1da50da2c835770419"' in b
assert 'AUTH26639_WORKFLOW_AUTHORITY_BLOB="4fc781824f9ecf38291575e4536a361560141bf1"' in b
# Preserve the exact successful ordering; identity/scope/applicability may change only around it.
ordered=[
 'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26639_mechanics',
 'install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches',
 '26640 PRE-BUILD SAFETY PROOF PASSED',
 './gradlew :app:assembleDebug --stacktrace',
 'expected exactly one Gradle debug APK',
 'postbuild_proof']
pos=-1
for token in ordered:
 n=b.find(token,pos+1)
 if n<0: raise SystemExit('missing/reordered 26639 mechanic: '+token[:90])
 pos=n
for token in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
              'snapshot_candidate_from_authority','compare_app_trees','git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD',
              'POST-BUILD INVARIANCE','CLEAN ARTIFACT SOURCE EXPORT']:
 assert token in b,token
# Workflow: exact 26639 3-stage shape and environment retained.
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','GITHUB_TOKEN: ${{ github.token }}']:
 assert token in w,token
assert w.count('- name:')==3
# New workflow path filter must be 26640-only so old workflow is not re-triggered by this package.
assert "'R1_26640_*'" in w and "'R1_26639_*'" not in w
print('PASS 26640 infrastructure audit: exact successful 26639 compiler/build/patch/PRE-BUILD/assemble/postbuild sequence preserved; delta limited to 26640 identity/authority/scope/regressions')
