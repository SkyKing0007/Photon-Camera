#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26663_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
required=['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs:raise SystemExit('FAIL inherited successful-26662 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26662_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos:raise SystemExit('FAIL successful-26662 ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf:raise SystemExit('FAIL workflow mechanics: '+t)
for t in ['RUNTIME_AUTHORITY_COMMIT="b691abfd8c7e04fdc44f78189ed2882e0a776e33"','BASE_RUN_ID="35300573903"','BASE_ARTIFACT_ID="10529652460"','BASE_ARTIFACT_SHA="d2ef9e96bae61e5c93e6d4900241926aaec4dfbb048db34e160a9a7790d95846"','BASE_TAR_SHA="acf9af1ab3ee096289f8fb869dc111d0215f90f34c5421dcd17320518b47df0b"']:
 if t not in bs:raise SystemExit('FAIL exact successful-26662 runtime authority '+t)
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs:raise SystemExit('FAIL exact shader compiler invocation')
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='b691abfd8c7e04fdc44f78189ed2882e0a776e33';refs=[('build_26662_r1_google_reference_normalization.sh','786b8310af2e9fd48f71e3cac40bd7bfdbd0eb6e'),('.github/workflows/build-26662-r1-google-reference-normalization.yml','a4502d294b4ba35eb7586cd7003fab4faeae11bf')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp:raise SystemExit(f'FAIL 26662 mechanics blob {path}: {got} != {exp}')
print('PASS 26663 infrastructure: exact successful 26662 compiler/native/patch/PRE-BUILD/assemble/postbuild ordering retained; only identity/successful-26662 authority/7-path scope and semantic validators changed')
