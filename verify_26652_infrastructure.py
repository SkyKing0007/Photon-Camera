#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26652_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
# Exact successful 26651 compiler/build ordering; 26652 changes only identity/authority/scope/semantic validators.
required=[
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches',
'set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace',
'find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',
"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs: raise SystemExit('FAIL inherited successful-26651 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26651_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos: raise SystemExit('FAIL successful-26651 ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf: raise SystemExit('FAIL workflow mechanics: '+t)
for t in [
'RUNTIME_AUTHORITY_COMMIT="fb0ce7883f976a39e84335a2922aec814eeb5483"','BASE_RUN_ID="35128052552"','BASE_ARTIFACT_ID="10459669305"',
'BASE_ARTIFACT_SHA="765c1f2f7291de4e64411dcdbb12a60a2a9855ade41557e1dda8efaca25d7022"','BASE_TAR_SHA="56ff26323803abd7ace40cf3e11178d891de2623782b8b7f04229ec9133d3fb9"']:
 if t not in bs: raise SystemExit('FAIL exact successful-26651 authority contract: '+t)
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs: raise SystemExit('FAIL exact runtime shader compiler invocation')
if re.search(r'glslang[^\n]*(app/src/main/assets|\.glsl)',bs,re.I): raise SystemExit('FAIL raw-asset glslang shortcut returned')
# APK contract exact between build script and workflow.
m=re.search(r'^FINAL="\$ROOT/(IrisCamera-[^"]+\.apk)"$',bs,re.M); vm=re.search(r'^VERSION_NAME="([^"]+)"; VERSION_BUILD="([^"]+)"$',bs,re.M)
if not m or not vm: raise SystemExit('FAIL APK/version parse')
final=m.group(1).replace('${VERSION_NAME}',vm.group(1)).replace('${VERSION_BUILD}',vm.group(2)); apks=re.findall(r'^\s+(IrisCamera-[^\s]+\.apk)\s*$',wf,re.M)
if apks!=[final] or f'test -f {final}' not in wf: raise SystemExit(f'FAIL APK packaging contract build={final} workflow={apks}')
# Authenticate exact successful 26651 mechanics blobs if this is the upload checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='fb0ce7883f976a39e84335a2922aec814eeb5483'
 refs=[('build_26651_r1_normal_master_short_fusion.sh','d8ddddc45f7abd0aaaffafed158a43c53e8a535c'),('.github/workflows/build-26651-r1-normal-master-short-fusion.yml','310f80ae077f1b0792740642858a0fcfe17961e0')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp: raise SystemExit(f'FAIL 26651 mechanics blob {path}: {got} != {exp}')
 oldbs=subprocess.check_output(['git','show',f'{commit}:build_26651_r1_normal_master_short_fusion.sh'],cwd=gitroot,text=True)
 oldwf=subprocess.check_output(['git','show',f'{commit}:.github/workflows/build-26651-r1-normal-master-short-fusion.yml'],cwd=gitroot,text=True)
 for t in required:
  if t not in oldbs: raise SystemExit('FAIL claimed 26651 mechanic absent in authenticated script: '+t)
 for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
  if t not in oldwf: raise SystemExit('FAIL claimed 26651 workflow mechanic absent: '+t)
print('PASS 26652 infrastructure: successful 26651 compiler/native/patch/PRE-BUILD/assemble/postbuild order retained exactly; pinned environment retained; runtime authority advanced only to exact successful 26651 compiled artifact; no raw-shader shortcut')
