#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26662_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
required=['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs:raise SystemExit('FAIL inherited successful-26661 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26661_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos:raise SystemExit('FAIL successful-26661 ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf:raise SystemExit('FAIL workflow mechanics: '+t)
for t in ['RUNTIME_AUTHORITY_COMMIT="4b527b078f30d3e443ba563ff677beb1e60c03a1"','BASE_RUN_ID="35296521033"','BASE_ARTIFACT_ID="10527679647"','BASE_ARTIFACT_SHA="58ea61c9a8e278d45635964af4ba89f02b51862b41ae0bd676b9ce09b652b9e5"','BASE_TAR_SHA="7aece829af111413627441a5c48ea07359be709ef4974b9181c286440163feab"']:
 if t not in bs:raise SystemExit('FAIL exact successful-26661 runtime authority '+t)
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs:raise SystemExit('FAIL exact shader compiler invocation')
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='4b527b078f30d3e443ba563ff677beb1e60c03a1';refs=[('build_26661_r1_google_reference_ae.sh','62d16853af50e0f09df08fc996fd3aa804ad24df'),('.github/workflows/build-26661-r1-google-reference-ae.yml','46d75aa533fe861e8144541b64d52428f3b1b9e0')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp:raise SystemExit(f'FAIL 26661 mechanics blob {path}: {got} != {exp}')
print('PASS 26662 infrastructure: exact successful 26661 compiler/native/patch/PRE-BUILD/assemble/postbuild ordering retained; only identity/successful-26661 authority/6-path scope and semantic validators changed')
