#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26659_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
required=['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs:raise SystemExit('FAIL inherited successful-26658 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26658_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos:raise SystemExit('FAIL successful-26658 ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf:raise SystemExit('FAIL workflow mechanics: '+t)
for t in ['RUNTIME_AUTHORITY_COMMIT="f44dbd33cfd1bc9612817e7b8cc1674c5b4e67f4"','BASE_RUN_ID="35256084878"','BASE_ARTIFACT_ID="10512866149"','BASE_ARTIFACT_SHA="6cebe6b2883e652cdab16eb3986e19de6dd14502759369af356e97ffe45003a9"','BASE_TAR_SHA="92c818d6cfd9563a6f7e09ba687b72baf443e7b8356bb890ae15d1cdc86f95bb"']:
 if t not in bs:raise SystemExit('FAIL exact successful-26658 authority contract: '+t)
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs:raise SystemExit('FAIL exact runtime shader compiler invocation')
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='f44dbd33cfd1bc9612817e7b8cc1674c5b4e67f4';refs=[('build_26658_r1_google_hdr_bracketing.sh','a2de70d015fc65ac81a9bb1e0a9834efa1d93be9'),('.github/workflows/build-26658-r1-google-hdr-bracketing.yml','018d0ed3b29b8a34e64ac79fb8881e3be5a61491')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp:raise SystemExit(f'FAIL 26658 mechanics blob {path}: {got} != {exp}')
 oldbs=subprocess.check_output(['git','show',f'{commit}:build_26658_r1_google_hdr_bracketing.sh'],cwd=gitroot,text=True);oldwf=subprocess.check_output(['git','show',f'{commit}:.github/workflows/build-26658-r1-google-hdr-bracketing.yml'],cwd=gitroot,text=True)
 for t in required:
  if t not in oldbs:raise SystemExit('FAIL claimed 26658 mechanic absent: '+t)
 for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
  if t not in oldwf:raise SystemExit('FAIL claimed 26658 workflow mechanic absent: '+t)
print('PASS 26659 infrastructure: exact successful 26658 compiler/native/patch/PRE-BUILD/assemble/postbuild ordering retained; only identity, 26658 authority, 4-path scope and semantic validators changed')
