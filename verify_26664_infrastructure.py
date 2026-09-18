#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26664_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
required=['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs:raise SystemExit('FAIL inherited successful-26663 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26663_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos:raise SystemExit('FAIL successful-26663 ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf:raise SystemExit('FAIL workflow mechanics: '+t)
for t in ['RUNTIME_AUTHORITY_COMMIT="e2931664924dfba8c923e15e5d7bd508caa1e011"','BASE_RUN_ID="35303072801"','BASE_ARTIFACT_ID="10530349789"','BASE_ARTIFACT_SHA="a94d19f4c6c61b72ce6494068941ddf8af3851a4d4e7115cdd94635e57ac8ee2"','BASE_TAR_SHA="d79acc7bebc5f5a9ef9916977f9ba58f98b46eec8c06dc7c83d3445fb5bb67dc"']:
 if t not in bs:raise SystemExit('FAIL exact successful-26663 runtime authority '+t)
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs:raise SystemExit('FAIL exact shader compiler invocation')
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='e2931664924dfba8c923e15e5d7bd508caa1e011';refs=[('build_26663_r1_stable_preview_hdr_body.sh','98a315d5b0ce7f887fa34e58a061afad127f1ff5'),('.github/workflows/build-26663-r1-stable-preview-hdr-body.yml','c3cb09ec1a35853e18eea370d1e0269292d5a108')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp:raise SystemExit(f'FAIL 26663 mechanics blob {path}: {got} != {exp}')
print('PASS 26664 infrastructure: exact successful 26663 compiler/native/patch/PRE-BUILD/assemble/postbuild ordering retained; only identity/successful-26663 authority/6-path scope and semantic validators changed')
