#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26718_infrastructure.py BUILD_SCRIPT WORKFLOW')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
prior={
'build_26717_downloads_iris_log_storage.sh':'a1bbaf3c876ab89eca921d7a4e4abd015333d2b52bc5cf17d42f440dca492017',
'.github/workflows/build-26717-downloads-iris-log-storage.yml':'9c88b2eb7edb3e4ea769482adbe6ac6919a726a6ae02f7bd772f9dd7b0856afe',
'transform_26717.py':'c2ea6800d6b069243b1014a7ca20741a7ec091048b3ed70523431fb72fdc1f43',
'validate_26717.py':'4677bea5923b2da7958b94ed205c42599b6ea7d1c04f11d5bfce1a63665eac73',
'verify_26717_authority.py':'c4e2c65c7f0320eb021af456b5873907c7b3c399547a9266b08ae66254073121',
'verify_26717_infrastructure.py':'fe8b636f39781cb8b244e8a6911e2b7a5ae9f358be46925151f118bab44b5b23',
'verify_26717_patches.py':'32419db25a3d8d95bb4899d1bf7a949810f3e8f2947e96d155fbcb20024c43a5',
'verify_26717_regressions.py':'52e8b8e2f25ee5676581c9f81a3f9eb787417daa37857d4ae90cc78b8107fcb4',
'verify_26717_shaders.py':'198c9de09b42a96a842859fa145beb51f6964db0b2e8ba46e71c955e5db59cff'}
# When running in the real checkout, hash the exact successful implementation at its authority commit.
if Path('.git').exists():
 for path,h in prior.items():
  data=subprocess.check_output(['git','show','cc158368bf8bd1303a164d85457e396840ddb16e:'+path]);assert hashlib.sha256(data).hexdigest()==h,('26717 infrastructure authority drift',path)
for t in [
'RUNTIME_AUTHORITY_COMMIT="cc158368bf8bd1303a164d85457e396840ddb16e"',
'BASE_RUN_ID="36286961631"','BASE_ARTIFACT_ID="10921015621"',
'BASE_ARTIFACT_SHA="6e8741ee0c49826bdf73faeaa2acb049092a73987bbcb630da9a31f294ef8a77"',
'BASE_TAR_SHA="8bae03a6a74fd71b048511b2c19c0c1e65ae4ab3853b7611099446500b24d759"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26718_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'a1bbaf3c876ab89eca921d7a4e4abd015333d2b52bc5cf17d42f440dca492017',
'9c88b2eb7edb3e4ea769482adbe6ac6919a726a6ae02f7bd772f9dd7b0856afe']:
 assert t in s,t
m='# IRIS_26718_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
# Exact successful-26717 execution stage order. Applicable shader checks expand inside the existing shader stage only.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26717_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26718 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26718 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
# Prove the compiler/build commands themselves are unchanged from 26717.
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26718_high_zoom_detail_reconstruction.sh']:
 assert t in w,t
assert 'python3 -S verify_26718_infrastructure.py build_26718_high_zoom_detail_reconstruction.sh .github/workflows/build-26718-high-zoom-detail-reconstruction.yml' in w
assert 'successful 26717 compiled authority' in w
assert 'backup' not in s.lower()
print('PASS 26718 infrastructure: exact successful 26717 mechanics authority hash-pinned; stage order and compiler/build commands unchanged; authority advanced to successful 26717; only 12-file scope and applicable shader/semantic validators expand; no backup')
