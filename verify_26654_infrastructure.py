#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26654_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); bs=build.read_text(); wf=workflow.read_text()
# Exact successful 26653 compiler/build ordering; 26654 changes only identity/authority/scope and required semantic/shader coverage.
required=[
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches',
'set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace',
'find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',
"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs: raise SystemExit('FAIL inherited successful-26653 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26653_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos: raise SystemExit('FAIL successful-26653 ordering: '+t)
 pos=p
workflow_required=['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']
for t in workflow_required:
 if t not in wf: raise SystemExit('FAIL workflow mechanics: '+t)
for t in [
'RUNTIME_AUTHORITY_COMMIT="5031e403553928e6e9411789a2ff7deab01390ed"','BASE_RUN_ID="35170004987"','BASE_ARTIFACT_ID="10476700363"',
'BASE_ARTIFACT_SHA="2cd27a12ca2339fa4e1df02b661b6f7836487deb2d9576a353d18fec8f1e2bce"','BASE_TAR_SHA="aa2febedc278945e13055cadc7fde11c8637de3bfb8ea04e47908edbd70bf369"']:
 if t not in bs: raise SystemExit('FAIL exact successful-26653 authority contract: '+t)
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs: raise SystemExit('FAIL exact runtime shader compiler invocation')
if re.search(r'glslang[^\n]*(app/src/main/assets|\.glsl)',bs,re.I): raise SystemExit('FAIL raw-asset glslang shortcut returned')
# APK contract exact between build script and workflow.
m=re.search(r'^FINAL="\$ROOT/(IrisCamera-[^"]+\.apk)"$',bs,re.M); vm=re.search(r'^VERSION_NAME="([^"]+)"; VERSION_BUILD="([^"]+)"$',bs,re.M)
if not m or not vm: raise SystemExit('FAIL APK/version parse')
final=m.group(1).replace('${VERSION_NAME}',vm.group(1)).replace('${VERSION_BUILD}',vm.group(2)); apks=re.findall(r'^\s+(IrisCamera-[^\s]+\.apk)\s*$',wf,re.M)
if apks!=[final] or f'test -f {final}' not in wf: raise SystemExit(f'FAIL APK packaging contract build={final} workflow={apks}')
# Authenticate exact successful 26653 mechanics blobs if this is the upload checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='5031e403553928e6e9411789a2ff7deab01390ed'
 refs=[('build_26653_r1_final_highlight_tone_fine_structure.sh','7ae9e53a2cb57347cb03a546624125ac50b75917'),('.github/workflows/build-26653-r1-final-highlight-tone-fine-structure.yml','ba5daffd6ed95622366538cf8f7d3231d1f0576d')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp: raise SystemExit(f'FAIL 26653 mechanics blob {path}: {got} != {exp}')
 oldbs=subprocess.check_output(['git','show',f'{commit}:build_26653_r1_final_highlight_tone_fine_structure.sh'],cwd=gitroot,text=True)
 oldwf=subprocess.check_output(['git','show',f'{commit}:.github/workflows/build-26653-r1-final-highlight-tone-fine-structure.yml'],cwd=gitroot,text=True)
 for t in required:
  if t not in oldbs: raise SystemExit('FAIL claimed 26653 mechanic absent in authenticated script: '+t)
 for t in workflow_required:
  if t not in oldwf: raise SystemExit('FAIL claimed 26653 workflow mechanic absent: '+t)
print('PASS 26654 infrastructure: successful 26653 compiler/native/patch/PRE-BUILD/assemble/postbuild order retained exactly; pinned environment retained; runtime authority advanced only to exact successful 26653 compiled artifact; no raw-shader shortcut')
