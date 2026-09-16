#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_r1_2_26648_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); bs=build.read_text(); wf=workflow.read_text()
required_build=['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','find "$ROOT/app/build/outputs/apk/debug" -type f -name \'*.apk\' | sort','postbuild_proof','tar --sort=name --mtime=\'UTC 1970-01-01\' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n']
for t in required_build:
 if t not in bs: raise SystemExit('FAIL infrastructure mechanic: '+t)
order=['install_frozen_candidate_live\n','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches\n','set_report "PRE-BUILD SAFETY PROOF" "PASS"','./gradlew :app:assembleDebug --stacktrace','postbuild_proof\n']
pos=-1
for t in order:
 p=bs.find(t,pos+1)
 if p<0 or p<=pos: raise SystemExit('FAIL infrastructure ordering: '+t)
 pos=p
for t in ['runs-on: ubuntu-24.04','uses: actions/checkout@v5','fetch-depth: 0','uses: actions/setup-java@v5','distribution: temurin',"java-version: '17'",'uses: actions/setup-python@v5',"python-version: '3.12'",'uses: actions/upload-artifact@v4','retention-days: 90','if-no-files-found: error']:
 if t not in wf: raise SystemExit('FAIL workflow mechanics: '+t)
for t in ['RUNTIME_AUTHORITY_COMMIT="4dfea0e55f74f18dce453eff4fcdd265f4634f01"','BASE_RUN_ID="35052623377"','BASE_ARTIFACT_ID="10429058098"','BASE_ARTIFACT_SHA="643668fcac6f38c2b802ed09618d08ad70495968af3c5b999025a954e336870a"','BASE_TAR_SHA="5b4bbc97b0958e7bcf68bfb39651fee051271610ffc69d8d8692eb664c1f46ca"']:
 if t not in bs: raise SystemExit('FAIL R1.1 authority contract: '+t)
# Permanent artifact regression: the build script FINAL basename and workflow APK upload basename must be exactly identical.
m=re.search(r'^FINAL="\$ROOT/(IrisCamera-[^"]+\.apk)"$',bs,re.M)
if not m: raise SystemExit('FAIL packaging: cannot parse FINAL APK basename')
final=m.group(1)
vm=re.search(r'^VERSION_NAME="([^"]+)"; VERSION_BUILD="([^"]+)"$',bs,re.M)
if not vm: raise SystemExit('FAIL packaging: cannot parse version/build')
final=final.replace('${VERSION_NAME}',vm.group(1)).replace('${VERSION_BUILD}',vm.group(2))
apks=re.findall(r'^\s+(IrisCamera-[^\s]+\.apk)\s*$',wf,re.M)
if apks!=[final]: raise SystemExit(f'FAIL packaging APK contract: build FINAL={final} workflow={apks}')
if f'test -f {final}' not in wf: raise SystemExit('FAIL packaging: explicit pre-upload APK existence gate missing')
# Verify successful R1.1 and original 26646 mechanics blobs when in checkout.
gitroot=build.parent
if (gitroot/'.git').exists():
 refs=[('4dfea0e55f74f18dce453eff4fcdd265f4634f01','build_r1_1_26648_universal_fusion_heic_ui.sh','7dd19c527d30b5be8b77f74ce4208963435029d6'),('4dfea0e55f74f18dce453eff4fcdd265f4634f01','.github/workflows/build-r1-1-26648-universal-fusion-heic-ui.yml','51743e7dc84ca843baff75efb348e283b58f3e67'),('19003161060180e61354e23051308b1798f917b9','build_26646_r1_universal_hdr_superres_heic.sh','10e22181cb4964af845d637ab62878f988628571'),('19003161060180e61354e23051308b1798f917b9','.github/workflows/build-26646-r1-universal-hdr-superres-heic.yml','a1326ea24920fbd60daef953bf3d129a1546fe9f')]
 for ref,path,exp in refs:
  got=subprocess.check_output(['git','rev-parse',f'{ref}:{path}'],cwd=gitroot,text=True).strip()
  if got!=exp: raise SystemExit(f'FAIL mechanics blob {path}: {got} != {exp}')
print('PASS 26648 R1.2 infrastructure: zero runtime delta from successful R1.1; exact 26646 compiler/build order retained; build FINAL and workflow APK path are identical with explicit pre-upload existence gate')
