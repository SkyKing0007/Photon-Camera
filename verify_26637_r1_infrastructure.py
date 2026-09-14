#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26637_r1_infrastructure.py BUILD WORKFLOW [--git]')
build=Path(sys.argv[1]).read_text(); wf=Path(sys.argv[2]).read_text(); do_git=len(sys.argv)==4 and sys.argv[3]=='--git'
# Exact successful 26636 mechanics anchors retained. Helper-function definition position is not
# execution order, so validate the main call chain and compiler/build tail separately.
main_chain='verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26636_mechanics'
assert main_chain in build
tail=['install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
      "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",
      'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug',
      'expected exactly one Gradle debug APK','postbuild_proof']
pos=build.index(main_chain)+len(main_chain)
for a in tail:
 n=build.find(a,pos); assert n>=0, a; pos=n
for a in ['POST-BUILD INVARIANCE','candidate_app_source.tar.gz']:
 assert a in build,a
for a in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 assert a in wf,a
if do_git:
 auth='52be30fe45f9492a765efe6437a6b2c1de6b7ff3'
 pins={'build_26636_r1_heic_ultrahdr.sh':'920c78ebb12cc83cecc56de90697811c1fee8ee5','.github/workflows/build-26636-r1-heic-ultrahdr.yml':'8d9461669a01e6a065c730b321615b34fddb3752','transform_26636_r1.py':'bb6c2de7bcc8eaa8ad6cc487879ff8aebe146952'}
 for path,want in pins.items():
  got=subprocess.check_output(['git','rev-parse',f'{auth}:{path}'],text=True).strip(); assert got==want,(path,got)
print('PASS 26637 infrastructure: successful-26636 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; authority/scope/container validators only')
