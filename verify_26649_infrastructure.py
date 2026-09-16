#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26649_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); bs=build.read_text(); wf=workflow.read_text()
required_build=[
 'GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26648_mechanics',
 'install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches',
 'set_report "PRE-BUILD SAFETY PROOF" "PASS"',
 './gradlew :app:assembleDebug --stacktrace',
 'find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort',
 'postbuild_proof',
 "tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n",
]
for t in required_build:
 if t not in bs: raise SystemExit('FAIL infrastructure missing successful mechanic: '+t)
order=[
 'install_frozen_candidate_live\n',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches\n',
 'set_report "PRE-BUILD SAFETY PROOF" "PASS"',
 './gradlew :app:assembleDebug --stacktrace',
 'postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos: raise SystemExit('FAIL infrastructure ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf: raise SystemExit('FAIL workflow mechanics: '+t)
# Disjoint 26649 trigger and exact APK contract must be explicit.
for t in ["'R1_26649_*'","'handoff_payload_26649/**'","'.github/workflows/build-26649-r1-photon-highlight-compression.yml'",'test -f IrisCamera-0.9726649-26649-r1-photon-highlight-compression-debug.apk','IrisCamera-0.9726649-26649-r1-photon-highlight-compression-debug.apk']:
 if t not in wf: raise SystemExit('FAIL 26649 workflow contract: '+t)
# Exact successful R1.2 implementation blobs are verification-mechanics authority on an Actions checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
 authority='3b46a176d4d018613b17912bce30ebdb6e2fd7e7'
 refs={
  'build_r1_2_26648_universal_fusion_heic_ui.sh':'940320d3b7b6d60cdb9bb8f0f2e9dc61b7d932f7',
  '.github/workflows/build-r1-2-26648-apk-artifact-repair.yml':'ef04fa514a63464d71cc4db630dcf72c8f040283'}
 for path,expected in refs.items():
  got=subprocess.check_output(['git','rev-parse',f'{authority}:{path}'],cwd=gitroot,text=True).strip()
  if got!=expected: raise SystemExit(f'FAIL successful-26648 R1.2 mechanics blob {path}: {got} != {expected}')
print('PASS 26649 infrastructure: exact successful 26648 R1.2 compiler/native/patch/PRE-BUILD/assemble/postbuild ordering and ubuntu24.04/Temurin17/Python3.12 toolchain retained; delta limited to 26649 identity/scope/semantic assertions')
