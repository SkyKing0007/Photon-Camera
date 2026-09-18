#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26665_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
required=['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs:raise SystemExit('FAIL inherited successful-26664 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26664_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos:raise SystemExit('FAIL successful-26664 ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf:raise SystemExit('FAIL workflow mechanics: '+t)
for t in ['RUNTIME_AUTHORITY_COMMIT="62088643221694e42217eccd9c44c039617a08e4"','BASE_RUN_ID="35305844785"','BASE_ARTIFACT_ID="10531509303"','BASE_ARTIFACT_SHA="5c8b2aba750e85918f110ef5a4b81c9e09b96c19810b91e76f9c5b4ba5f6375b"','BASE_TAR_SHA="10c133fe7e2a3daa8df7fe544bc023a400e9feed9dc1cf197e64d5dbe7b87048"']:
 if t not in bs:raise SystemExit('FAIL exact successful-26664 runtime authority '+t)
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs:raise SystemExit('FAIL exact shader compiler invocation')
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='62088643221694e42217eccd9c44c039617a08e4';refs=[('build_26664_r1_global_log_body_tone.sh','b96452c6686fc3cd40288558efc4d2e6db036081'),('.github/workflows/build-26664-r1-global-log-body-tone.yml','7b0fc395213e9354e96d49c5758b81e0a0c7cf40')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp:raise SystemExit(f'FAIL 26664 mechanics blob {path}: {got} != {exp}')
print('PASS 26665 infrastructure: exact successful 26664 compiler/native/patch/PRE-BUILD/assemble/postbuild ordering retained; only identity/successful-26664 authority/6-path scope and semantic validators changed')
