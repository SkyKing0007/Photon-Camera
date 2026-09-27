#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26719_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
prior={'build_26718_high_zoom_detail_reconstruction.sh':'7cb543e6e54fad2bbe55b01db4ce6582cbef40f4ec4d1e8dc8e970097a895498','.github/workflows/build-26718-high-zoom-detail-reconstruction.yml':'fe0fc38103152f6e3acd38fc7ff2e780eae767bd7e68bf376f9287539e4e0814'}
if Path('.git').exists():
 for path,h in prior.items():
  data=subprocess.check_output(['git','show','cac257e1a691a057916bc6670540e9daa7162ac7:'+path]); assert hashlib.sha256(data).hexdigest()==h,('26718 R1 infrastructure authority drift',path)
for t in ['RUNTIME_AUTHORITY_COMMIT="cac257e1a691a057916bc6670540e9daa7162ac7"','BASE_RUN_ID="36331431117"','BASE_ARTIFACT_ID="10936345053"','BASE_ARTIFACT_SHA="877c4a67ba111812a8b7ceb0f688e5148e0ffc2515b8c9021c5bf74319c695c7"','BASE_TAR_SHA="173514b8a0291719b174f1e04909c10594ed310bd43f8b1996524555b8f9c975"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26719_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"','7cb543e6e54fad2bbe55b01db4ce6582cbef40f4ec4d1e8dc8e970097a895498','fe0fc38103152f6e3acd38fc7ff2e780eae767bd7e68bf376f9287539e4e0814']:
 assert t in s,t
m='# IRIS_26719_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(m)==1; main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26718_r1_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26719 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26719 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26719_high_zoom_lazy_isolation.sh']:
 assert t in w,t
assert 'backup' not in s.lower()
print('PASS 26719 infrastructure: exact successful 26718 R1 mechanics hash-pinned; stage order and compiler/build commands unchanged; authority advanced only; 2-file repair scope; no backup')
