#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3:
    raise SystemExit('usage: verify_26648_r1_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2])
bs=build.read_text(); wf=workflow.read_text()
required_build=[
    'GLSLANG_VERSION="16.5.0"',
    'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
    'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26646_mechanics',
    'install_frozen_candidate_live',
    './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
    "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
    'verify_candidate_patches',
    'set_report "PRE-BUILD SAFETY PROOF" "PASS"',
    './gradlew :app:assembleDebug --stacktrace',
    'find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort',
    'postbuild_proof',
    'tar --sort=name --mtime=\'UTC 1970-01-01\' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n',
]
for token in required_build:
    if token not in bs: raise SystemExit('FAIL infrastructure: missing successful-26646 mechanic: '+token)
order=[
    'install_frozen_candidate_live\n',
    './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
    "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
    'verify_candidate_patches\n',
    'set_report "PRE-BUILD SAFETY PROOF" "PASS"',
    './gradlew :app:assembleDebug --stacktrace',
    'postbuild_proof\n',
]
pos=-1
for token in order:
    p=bs.find(token,pos+1)
    if p<0: raise SystemExit('FAIL infrastructure order token: '+token)
    if p<=pos: raise SystemExit('FAIL infrastructure ordering: '+token)
    pos=p
required_wf=[
    'runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0',
    'uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",
    'uses: actions/setup-python@v5',"python-version: '3.12'",
    'uses: actions/upload-artifact@v4','retention-days: 90',
]
for token in required_wf:
    if token not in wf: raise SystemExit('FAIL workflow mechanics: '+token)
for stale in ['build-26646-r1-universal-hdr-superres-heic.yml','build-26647-r1-direct-short-heic-p3.yml',"R1_26646_","R1_26647_"]:
    if stale in wf: raise SystemExit('FAIL workflow overlapping prior trigger identity: '+stale)
# Scope change is deliberately limited to proving current handoff-only 26647 parent while keeping 26646 runtime authority.
for token in [
 'RUNTIME_AUTHORITY_COMMIT="19003161060180e61354e23051308b1798f917b9"',
 'local intervening="3d9851e030cededc038e3a1a3287460c916c9e9d"',
 'git diff --name-only "$RUNTIME_AUTHORITY_COMMIT".."$intervening"',
 'git diff --name-only "$intervening"..HEAD',
]:
    if token not in bs: raise SystemExit('FAIL 26648 authority/scope lineage proof: '+token)
# Independently authenticate exact successful 26646 implementation blobs on Actions checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
    authority='19003161060180e61354e23051308b1798f917b9'
    refs={
      'build_26646_r1_universal_hdr_superres_heic.sh':'10e22181cb4964af845d637ab62878f988628571',
      '.github/workflows/build-26646-r1-universal-hdr-superres-heic.yml':'a1326ea24920fbd60daef953bf3d129a1546fe9f',
    }
    for path,expected in refs.items():
        got=subprocess.check_output(['git','rev-parse',f'{authority}:{path}'],cwd=gitroot,text=True).strip()
        if got!=expected: raise SystemExit(f'FAIL successful-26646 mechanics blob {path}: {got} != {expected}')
print('PASS 26648 infrastructure: successful 26646 compiler/native/patch/PRE-BUILD/assemble/postbuild order and ubuntu24.04/Temurin17/Python3.12 toolchain retained; delta limited to 26648 identity/scope/semantic assertions plus handoff-only intervening-commit proof')
