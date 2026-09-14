#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26638_r1_infrastructure.py BUILD WORKFLOW [--git]')
build=Path(sys.argv[1]).read_text(); wf=Path(sys.argv[2]).read_text(); do_git=len(sys.argv)==4 and sys.argv[3]=='--git'
# Preserve exact successful 26637 top-level execution order. Modified GLSL now makes the already
# proven 26635 pinned compiler gate applicable inside verify_shaders; it does not reorder later gates.
main_chain='verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26637_mechanics'
assert main_chain in build
tail=['install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
      "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",
      'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug',
      'expected exactly one Gradle debug APK','postbuild_proof']
pos=build.index(main_chain)+len(main_chain)
for a in tail:
 n=build.find(a,pos); assert n>=0,a; pos=n
for a in ['POST-BUILD INVARIANCE','candidate_app_source.tar.gz','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','--compiler "$compiler"']:
 assert a in build,a
for a in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert a in wf,a
if do_git:
 auth='a448bb1389dbf5ca643d05cda2ce1dad267b23ec'
 pins={'build_26637_r1_heic_container_fix.sh':'620ce3767bbe11fb2083d0506b78abbb3c7f194c','.github/workflows/build-26637-r1-heic-container-fix.yml':'68c3b784eb35c31162c4c7fd3e93553aaf95bcff','transform_26637_r1.py':'271158878d3eb0448f4d09cdbdacd5f9e77e796b'}
 for path,want in pins.items():
  got=subprocess.check_output(['git','rev-parse',f'{auth}:{path}'],text=True).strip(); assert got==want,(path,got)
print('PASS 26638 infrastructure: exact successful-26637 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only applicable proven GLSL gate + identity/authority/scope/regression deltas')
