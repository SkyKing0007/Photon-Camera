#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26655_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
# Exact successful 26654 compiler/build ordering; 26655 changes only identity/authority/scope and required spatial/semantic/shader coverage.
required=[
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches',
'set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace',
'find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',
"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs: raise SystemExit('FAIL inherited successful-26654 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26654_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos: raise SystemExit('FAIL successful-26654 ordering: '+t)
 pos=p
workflow_required=['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']
for t in workflow_required:
 if t not in wf: raise SystemExit('FAIL workflow mechanics: '+t)
# Exact successful 26654 runtime authority contract.
for t in [
'RUNTIME_AUTHORITY_COMMIT="1b14a779a760981aa72ab910590041ba65ebfafa"','BASE_RUN_ID="35174255132"','BASE_ARTIFACT_ID="10478072255"',
'BASE_ARTIFACT_SHA="9ead04ac4c6c39daa8ef0e747e952f76c371a529a01afc1fad3b355245a2cae6"','BASE_TAR_SHA="059f0f90635264c5e42fa63a8eeff7ee19c20f3bf036677acb06a075c9f4ae44"']:
 if t not in bs: raise SystemExit('FAIL exact successful-26654 authority contract: '+t)
if 'AUTH_26654_BUILD_SCRIPT_BLOB="2283bd981ddbf80650aee9642ef92d4d39030069"' not in bs: raise SystemExit('FAIL successful-26654 build blob pin')
if 'AUTH_26654_WORKFLOW_BLOB="a42702539a70de8598538d4550bd1a367dbc0d8b"' not in bs: raise SystemExit('FAIL successful-26654 workflow blob pin')
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs: raise SystemExit('FAIL exact runtime shader compiler invocation')
if re.search(r'glslang[^\n]*(app/src/main/assets|\.glsl)',bs,re.I): raise SystemExit('FAIL raw-asset glslang shortcut returned')
# APK contract exact between build script and workflow.
m=re.search(r'^FINAL="\$ROOT/(IrisCamera-[^"]+\.apk)"$',bs,re.M);vm=re.search(r'^VERSION_NAME="([^"]+)"; VERSION_BUILD="([^"]+)"$',bs,re.M)
if not m or not vm: raise SystemExit('FAIL APK/version parse')
final=m.group(1).replace('${VERSION_NAME}',vm.group(1)).replace('${VERSION_BUILD}',vm.group(2));apks=re.findall(r'^\s+(IrisCamera-[^\s]+\.apk)\s*$',wf,re.M)
if apks!=[final] or f'test -f {final}' not in wf: raise SystemExit(f'FAIL APK packaging contract build={final} workflow={apks}')
# Wrapper identity must be the 26655 source-domain build, not a stale 26654 label.
for t in ['build_26655_r1_source_domain_spatial_highlight.sh','build_26655_r1_source_domain_spatial_highlight_outputs','photon-26655-r1-source-domain-spatial-highlight']:
 if t not in bs+wf: raise SystemExit('FAIL 26655 wrapper identity '+t)
# Authenticate exact successful 26654 mechanics blobs when running in upload checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='1b14a779a760981aa72ab910590041ba65ebfafa'
 refs=[('build_26654_r1_final_highlight_authority_cleanup.sh','2283bd981ddbf80650aee9642ef92d4d39030069'),('.github/workflows/build-26654-r1-final-highlight-authority-cleanup.yml','a42702539a70de8598538d4550bd1a367dbc0d8b')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp: raise SystemExit(f'FAIL 26654 mechanics blob {path}: {got} != {exp}')
 oldbs=subprocess.check_output(['git','show',f'{commit}:build_26654_r1_final_highlight_authority_cleanup.sh'],cwd=gitroot,text=True)
 oldwf=subprocess.check_output(['git','show',f'{commit}:.github/workflows/build-26654-r1-final-highlight-authority-cleanup.yml'],cwd=gitroot,text=True)
 for t in required:
  if t not in oldbs: raise SystemExit('FAIL claimed 26654 mechanic absent in authenticated script: '+t)
 for t in workflow_required:
  if t not in oldwf: raise SystemExit('FAIL claimed 26654 workflow mechanic absent: '+t)
print('PASS 26655 infrastructure: successful 26654 compiler/native/patch/PRE-BUILD/assemble/postbuild order retained exactly; pinned environment retained; runtime authority advanced only to exact successful 26654 compiled artifact; no raw-shader shortcut')
