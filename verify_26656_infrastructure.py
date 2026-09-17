#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26656_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]);workflow=Path(sys.argv[2]);bs=build.read_text();wf=workflow.read_text()
# Exact successful 26655 compiler/build ordering. 26656 changes identity/authority/scope and validators only.
required=[
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches',
'set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace',
'find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',
"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs: raise SystemExit('FAIL inherited successful-26655 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26655_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos: raise SystemExit('FAIL successful-26655 ordering: '+t)
 pos=p
workflow_required=['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']
for t in workflow_required:
 if t not in wf: raise SystemExit('FAIL workflow mechanics: '+t)
# Exact successful 26655 runtime authority contract.
for t in [
'RUNTIME_AUTHORITY_COMMIT="a6a5dd5733a0f5db0f0b869cc638c54671c13012"','BASE_RUN_ID="35179194102"','BASE_ARTIFACT_ID="10479604160"',
'BASE_ARTIFACT_SHA="7f4775429058ac168caf9bc1ff7fedeac64a69bf59078e0593f6f475f1b66b22"','BASE_TAR_SHA="e3be49a3d1be59e3ed4721d18b5084e142874e9eefb8623709cf93a6c84cb3dc"']:
 if t not in bs: raise SystemExit('FAIL exact successful-26655 authority contract: '+t)
if 'AUTH_26655_BUILD_SCRIPT_BLOB="05bde2489f9d81238821546b5f917f1b1fb93b90"' not in bs: raise SystemExit('FAIL successful-26655 build blob pin')
if 'AUTH_26655_WORKFLOW_BLOB="d255c6c546b7742e7bb169a8f457fe0f8dd93046"' not in bs: raise SystemExit('FAIL successful-26655 workflow blob pin')
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs: raise SystemExit('FAIL exact runtime shader compiler invocation')
if re.search(r'glslang[^\n]*(app/src/main/assets|\.glsl)',bs,re.I): raise SystemExit('FAIL raw-asset glslang shortcut returned')
# APK contract exact between build script and workflow.
m=re.search(r'^FINAL="\$ROOT/(IrisCamera-[^"]+\.apk)"$',bs,re.M);vm=re.search(r'^VERSION_NAME="([^"]+)"; VERSION_BUILD="([^"]+)"$',bs,re.M)
if not m or not vm: raise SystemExit('FAIL APK/version parse')
final=m.group(1).replace('${VERSION_NAME}',vm.group(1)).replace('${VERSION_BUILD}',vm.group(2));apks=re.findall(r'^\s+(IrisCamera-[^\s]+\.apk)\s*$',wf,re.M)
if apks!=[final] or f'test -f {final}' not in wf: raise SystemExit(f'FAIL APK packaging contract build={final} workflow={apks}')
for t in ['build_26656_r1_photon_new_post_reconstruction_tone.sh','build_26656_r1_photon_new_post_reconstruction_tone_outputs','photon-26656-r1-photon-new-post-reconstruction-tone']:
 if t not in bs+wf: raise SystemExit('FAIL 26656 wrapper identity '+t)
# Authenticate exact successful 26655 mechanics blobs and replay the shared mechanical contract when in Git checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='a6a5dd5733a0f5db0f0b869cc638c54671c13012'
 refs=[('build_26655_r1_source_domain_spatial_highlight.sh','05bde2489f9d81238821546b5f917f1b1fb93b90'),('.github/workflows/build-26655-r1-source-domain-spatial-highlight.yml','d255c6c546b7742e7bb169a8f457fe0f8dd93046')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp: raise SystemExit(f'FAIL 26655 mechanics blob {path}: {got} != {exp}')
 oldbs=subprocess.check_output(['git','show',f'{commit}:build_26655_r1_source_domain_spatial_highlight.sh'],cwd=gitroot,text=True)
 oldwf=subprocess.check_output(['git','show',f'{commit}:.github/workflows/build-26655-r1-source-domain-spatial-highlight.yml'],cwd=gitroot,text=True)
 for t in required:
  if t not in oldbs: raise SystemExit('FAIL claimed 26655 mechanic absent in authenticated script: '+t)
 for t in workflow_required:
  if t not in oldwf: raise SystemExit('FAIL claimed 26655 workflow mechanic absent: '+t)
print('PASS 26656 infrastructure: exact successful 26655 compiler/native/patch/PRE-BUILD/assemble/postbuild order retained; Java17/Python3.12/glslang16.5.0 retained; runtime authority advanced only to exact successful 26655 compiled artifact; functional infrastructure delta limited to 26656 identity/scope/semantic/shader validators')
