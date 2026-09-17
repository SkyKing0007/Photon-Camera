#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26657_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); bs=build.read_text(); wf=workflow.read_text()
# Exact successful 26656 compiler/build ordering. 26657 changes identity/authority/scope/regression only.
required=[
'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches',
'set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace',
'find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof',
"tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C \"$POST\" app | gzip -n"]
for t in required:
 if t not in bs: raise SystemExit('FAIL inherited successful-26656 mechanic: '+t)
order=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n','verify_successful_26656_mechanics\n','install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos: raise SystemExit('FAIL successful-26656 ordering: '+t)
 pos=p
workflow_required=['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']
for t in workflow_required:
 if t not in wf: raise SystemExit('FAIL workflow mechanics: '+t)
# Exact successful 26656 runtime authority contract.
for t in [
'RUNTIME_AUTHORITY_COMMIT="fedd17af01cfc113b66e9b56c4c8083bf336d841"','BASE_RUN_ID="35236339680"','BASE_ARTIFACT_ID="10503720660"',
'BASE_ARTIFACT_SHA="01d3d26b6dd4bfb9852d1032cd6970584a9cdc41558e96d3c2c05485b0050065"','BASE_TAR_SHA="5f2bd5e9e192b0a0dda3435e4809d43ae89188bb4e77a5236aa035ec78ac3be6"']:
 if t not in bs: raise SystemExit('FAIL exact successful-26656 authority contract: '+t)
if 'AUTH_26656_BUILD_SCRIPT_BLOB="c6d488247e97c9b89cfc87051ee0e876c3ed451d"' not in bs: raise SystemExit('FAIL successful-26656 build blob pin')
if 'AUTH_26656_WORKFLOW_BLOB="10d297ef59ba004db17ba10e706a394c35c8f806"' not in bs: raise SystemExit('FAIL successful-26656 workflow blob pin')
if 'python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$compiler"' not in bs: raise SystemExit('FAIL exact runtime shader compiler invocation')
if re.search(r'glslang[^\n]*(app/src/main/assets|\.glsl)',bs,re.I): raise SystemExit('FAIL raw-asset glslang shortcut returned')
# APK contract exact between build script and workflow.
m=re.search(r'^FINAL="\$ROOT/(IrisCamera-[^"]+\.apk)"$',bs,re.M); vm=re.search(r'^VERSION_NAME="([^"]+)"; VERSION_BUILD="([^"]+)"$',bs,re.M)
if not m or not vm: raise SystemExit('FAIL APK/version parse')
final=m.group(1).replace('${VERSION_NAME}',vm.group(1)).replace('${VERSION_BUILD}',vm.group(2)); apks=re.findall(r'^\s+(IrisCamera-[^\s]+\.apk)\s*$',wf,re.M)
if apks!=[final] or f'test -f {final}' not in wf: raise SystemExit(f'FAIL APK packaging contract build={final} workflow={apks}')
for t in ['build_26657_r1_photon_new_rgb_carrier_correction.sh','build_26657_r1_photon_new_rgb_carrier_correction_outputs','photon-26657-r1-photon-new-rgb-carrier-correction']:
 if t not in bs+wf: raise SystemExit('FAIL 26657 wrapper identity '+t)
# Authenticate exact successful 26656 mechanics blobs and replay the shared mechanical contract in upload checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
 commit='fedd17af01cfc113b66e9b56c4c8083bf336d841'
 refs=[('build_26656_r1_photon_new_post_reconstruction_tone.sh','c6d488247e97c9b89cfc87051ee0e876c3ed451d'),('.github/workflows/build-26656-r1-photon-new-post-reconstruction-tone.yml','10d297ef59ba004db17ba10e706a394c35c8f806')]
 for path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp: raise SystemExit(f'FAIL 26656 mechanics blob {path}: {got} != {exp}')
 oldbs=subprocess.check_output(['git','show',f'{commit}:build_26656_r1_photon_new_post_reconstruction_tone.sh'],cwd=gitroot,text=True)
 oldwf=subprocess.check_output(['git','show',f'{commit}:.github/workflows/build-26656-r1-photon-new-post-reconstruction-tone.yml'],cwd=gitroot,text=True)
 for t in required:
  if t not in oldbs: raise SystemExit('FAIL claimed 26656 mechanic absent in authenticated script: '+t)
 for t in workflow_required:
  if t not in oldwf: raise SystemExit('FAIL claimed 26656 workflow mechanic absent: '+t)
 # Mechanical command sequence itself must be identical after removing wrapper identity/output labels.
 def command_sig(s):
  needles=['sha256sum -c "$HANDOFF"','bash -n "$BUILD_SCRIPT"','python3 -S "$TRANSFORM"','python3 -S "$VALIDATE"','python3 -S "$GATEVERIFY"','python3 -S "$AUTHORITY"','python3 -S "$SHADERVERIFY"','python3 -S "$INFRA"','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','find "$ROOT/app/build/outputs/apk/debug"','postbuild_proof','tar --sort=name']
  return [(n,s.find(n)) for n in needles]
 new_sig=command_sig(bs); old_sig=command_sig(oldbs)
 if [n for n,p in new_sig if p<0] or [n for n,p in old_sig if p<0]: raise SystemExit('FAIL mechanical signature missing')
 if [n for n,p in sorted(new_sig,key=lambda x:x[1])] != [n for n,p in sorted(old_sig,key=lambda x:x[1])]: raise SystemExit('FAIL 26656 mechanical command ordering delta')
print('PASS 26657 infrastructure: exact successful 26656 compiler/native/patch/PRE-BUILD/assemble/postbuild command order retained; Java17/Python3.12/glslang16.5.0 retained; authority advanced only to exact successful 26656 artifact; infrastructure delta limited to 26657 identity/2-path scope/RGB-carrier regression')
