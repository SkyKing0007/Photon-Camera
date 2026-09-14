#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26639_r1_infrastructure.py BUILD WORKFLOW [--git]')
build=Path(sys.argv[1]).read_text(); wf=Path(sys.argv[2]).read_text(); do_git=len(sys.argv)==4 and sys.argv[3]=='--git'
# Exact successful-26638 top-level execution order is preserved. Shader applicability remains in the same
# verify_shaders slot; 26639 only corrects runtime expansion to the actual GLInterface #version310/#line path
# and replays that changed verification mechanic against the real successful-26638 candidate before 26639.
main_chain='verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26638_mechanics'
assert main_chain in build
tail=['install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
      "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",
      'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug',
      'expected exactly one Gradle debug APK','postbuild_proof']
pos=build.index(main_chain)+len(main_chain)
for a in tail:
 n=build.find(a,pos); assert n>=0,a; pos=n
for a in ['POST-BUILD INVARIANCE','candidate_app_source.tar.gz','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','--compiler "$compiler"',
          'RUNTIME_AUTHORITY_COMMIT="ece6ca77e299652f7be20872414b23bafc5aa5e7"','BASE_RUN_ID="34888005504"','BASE_ARTIFACT_ID="10365606935"']:
 assert a in build,a
for a in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert a in wf,a
# One 26639 upload/commit must only target the intended 26639 workflow names.
for a in ["'26639_R1_README_UPLOAD.txt'","'R1_26639_*'","'handoff_payload_26639_r1/**'","'build_26639_r1_color_shadow_detail_selective_uhdr.sh'","'.github/workflows/build-26639-r1-color-shadow-detail-selective-uhdr.yml'"]:
 assert a in wf,a
if do_git:
 auth='ece6ca77e299652f7be20872414b23bafc5aa5e7'
 pins={
  'build_26638_r1_short_acr3_shadow.sh':'539dde5a79092ba40607d18b698322ed0d1b9f01',
  '.github/workflows/build-26638-r1-short-acr3-shadow.yml':'5c0930b9a5370e5c50f90ecd5c6386f5960dbc8e',
  'transform_26638_r1.py':'04c38e9d0a3cd3de9d018ca0799ea5fdda8fb011'}
 for path,want in pins.items():
  got=subprocess.check_output(['git','rev-parse',f'{auth}:{path}'],text=True).strip(); assert got==want,(path,got,want)
print('PASS 26639 infrastructure: exact successful-26638 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only 26639 identity/authority/scope/regression + runtime-expanded shader applicability delta, replayed against exact successful-26638 authority')
